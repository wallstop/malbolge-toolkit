# SPDX-License-Identifier: MIT
"""
Program generation strategies for Malbolge.

The current implementation mirrors the legacy breadth-first search algorithm
but routes execution through the new interpreter and exposes configuration
hooks for determinism and performance tuning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from time import perf_counter_ns

from .encoding import reverse_normalize
from .interpreter import (
    MalbolgeInterpreter,
    MalbolgeMachine,
    MalbolgeRuntimeError,
)

SIGNATURE_TAPE_WIDTH = 8
StateSignature = tuple[int, int, int, int, tuple[int, ...]]


@dataclass(slots=True)
class GenerationConfig:
    opcode_choices: str = "op*"
    max_search_depth: int = 5
    random_seed: int | None = None
    max_program_length: int = 59049
    capture_trace: bool = False


@dataclass(slots=True)
class GenerationResult:
    target: str
    opcodes: str
    machine_output: str
    stats: dict[str, int]
    trace: list[dict[str, object]] = field(default_factory=list)

    @property
    def malbolge_program(self) -> str:
        return "".join(reverse_normalize(self.opcodes))


@dataclass(slots=True)
class _PrefixState:
    opcodes: str
    output: str
    machine: MalbolgeMachine


@dataclass(slots=True)
class _GenerationStats:
    evaluations: int = 0
    cache_hits: int = 0
    pruned: int = 0
    repeated_state_pruned: int = 0


class ProgramGenerator:
    def __init__(self, interpreter: MalbolgeInterpreter | None = None) -> None:
        self._interpreter = interpreter or MalbolgeInterpreter()

    @staticmethod
    def _state_signature(
        machine: MalbolgeMachine,
    ) -> StateSignature:
        tail_width = (
            SIGNATURE_TAPE_WIDTH if SIGNATURE_TAPE_WIDTH > 0 else len(machine.tape)
        )
        tail = tuple(machine.tape[-tail_width:]) if tail_width else ()
        return (len(machine.tape), machine.a % 256, machine.c, machine.d, tail)

    def generate_for_string(
        self,
        target: str,
        *,
        config: GenerationConfig | None = None,
    ) -> GenerationResult:
        if not target:
            raise ValueError("Target string must not be empty.")

        cfg = config or GenerationConfig()
        rng = Random(cfg.random_seed)
        interpreter = self._interpreter
        stats = _GenerationStats()
        state_cache: dict[str, _PrefixState] = {}
        dead_programs: set[str] = set()
        seen_signatures: set[StateSignature] = set()
        trace_events: list[dict[str, object]] | None = [] if cfg.capture_trace else None
        started_ns = perf_counter_ns()

        prefix = "i" + "o" * 99  # Legacy bootstrap sequence
        if len(prefix) >= cfg.max_program_length:
            raise MalbolgeRuntimeError(
                "Bootstrap sequence exceeds maximum program length."
            )

        prefix_result = interpreter.execute(prefix, capture_machine=True)
        if prefix_result.machine is None:
            raise MalbolgeRuntimeError(
                "Failed to capture machine state for bootstrap sequence."
            )
        prefix_state = _PrefixState(
            opcodes=prefix,
            output=prefix_result.output,
            machine=prefix_result.machine,
        )
        state_cache[prefix_state.opcodes] = prefix_state
        seen_signatures.add(self._state_signature(prefix_state.machine))

        def _record_trace(
            candidate: str,
            output: str | None,
            *,
            pruned: bool,
            reason: str,
            cache_hit: bool,
            depth_level: int,
            target_prefix: str,
        ) -> None:
            if trace_events is None:
                return
            trace_events.append(
                {
                    "target_prefix": target_prefix,
                    "candidate": candidate,
                    "output": output,
                    "pruned": pruned,
                    "reason": reason,
                    "cache_hit": cache_hit,
                    "evaluations": stats.evaluations,
                    "cache_hits": stats.cache_hits,
                    "depth": depth_level,
                }
            )

        for index in range(len(target)):
            found = False
            combinations = list(cfg.opcode_choices)
            depth = 0
            target_prefix = target[: index + 1]

            while not found:
                depth += 1
                for candidate in combinations:
                    suffix = candidate + "<"
                    program_key = prefix_state.opcodes + suffix
                    if program_key in dead_programs:
                        stats.pruned += 1
                        _record_trace(
                            suffix,
                            None,
                            pruned=True,
                            reason="dead_program_cache",
                            cache_hit=False,
                            depth_level=depth,
                            target_prefix=target_prefix,
                        )
                        continue
                    combined_state, from_cache = self._get_or_extend_state(
                        prefix_state,
                        suffix,
                        interpreter,
                        cfg,
                        state_cache,
                        stats,
                    )
                    if combined_state.machine is None:
                        raise MalbolgeRuntimeError(
                            "Generator requires machine snapshots for heuristics."
                        )
                    signature = self._state_signature(combined_state.machine)
                    pruned = False
                    reason = "candidate_retained"
                    if signature in seen_signatures:
                        stats.pruned += 1
                        stats.repeated_state_pruned += 1
                        dead_programs.add(program_key)
                        state_cache.pop(program_key, None)
                        pruned = True
                        reason = "repeated_state"
                    elif not target.startswith(combined_state.output) or len(
                        combined_state.output
                    ) > len(target):
                        stats.pruned += 1
                        dead_programs.add(program_key)
                        pruned = True
                        reason = "prefix_mismatch"
                    else:
                        seen_signatures.add(signature)
                        if combined_state.output == target_prefix:
                            prefix_state = combined_state
                            found = True
                            reason = "accepted"
                    _record_trace(
                        suffix,
                        combined_state.output,
                        pruned=pruned,
                        reason=reason,
                        cache_hit=from_cache,
                        depth_level=depth,
                        target_prefix=target_prefix,
                    )
                    if pruned:
                        continue
                    if found:
                        break

                if found:
                    break

                next_frontier: list[str] = []
                for base in combinations:
                    for opcode in cfg.opcode_choices:
                        candidate = base + opcode
                        candidate_key = prefix_state.opcodes + candidate + "<"
                        if candidate_key in dead_programs:
                            continue
                        next_frontier.append(candidate)
                combinations = next_frontier

                if depth >= cfg.max_search_depth and combinations:
                    viable = [
                        candidate
                        for candidate in combinations
                        if (prefix_state.opcodes + candidate + "<") not in dead_programs
                    ]
                    if not viable:
                        combinations = list(cfg.opcode_choices)
                        depth = 0
                        continue
                    random_choice = rng.choice(viable)
                    random_key = prefix_state.opcodes + random_choice
                    random_state, random_from_cache = self._get_or_extend_state(
                        prefix_state,
                        random_choice,
                        interpreter,
                        cfg,
                        state_cache,
                        stats,
                    )
                    if random_state.machine is None:
                        raise MalbolgeRuntimeError(
                            "Generator requires machine snapshots for heuristics."
                        )
                    random_pruned = False
                    random_reason = "random_extension"
                    random_signature = self._state_signature(random_state.machine)
                    if random_signature in seen_signatures:
                        stats.pruned += 1
                        stats.repeated_state_pruned += 1
                        dead_programs.add(random_key)
                        state_cache.pop(random_key, None)
                        random_pruned = True
                        random_reason = "repeated_state"
                    else:
                        seen_signatures.add(random_signature)
                    _record_trace(
                        random_choice,
                        random_state.output,
                        pruned=random_pruned,
                        reason=random_reason,
                        cache_hit=random_from_cache,
                        depth_level=depth,
                        target_prefix=target_prefix,
                    )
                    if random_pruned:
                        combinations = list(cfg.opcode_choices)
                        depth = 0
                        continue
                    prefix_state = random_state
                    combinations = list(cfg.opcode_choices)
                    depth = 0

        final_state, final_from_cache = self._get_or_extend_state(
            prefix_state,
            "v",
            interpreter,
            cfg,
            state_cache,
            stats,
        )
        if final_state.machine is None:
            raise MalbolgeRuntimeError(
                "Generator requires machine snapshots for heuristics."
            )
        seen_signatures.add(self._state_signature(final_state.machine))
        _record_trace(
            "v",
            final_state.output,
            pruned=False,
            reason="halt",
            cache_hit=final_from_cache,
            depth_level=0,
            target_prefix=target,
        )
        final_program = final_state.opcodes
        final_output = final_state.output
        finished_ns = perf_counter_ns()

        return GenerationResult(
            target=target,
            opcodes=final_program,
            machine_output=final_output,
            stats={
                "evaluations": stats.evaluations,
                "cache_hits": stats.cache_hits,
                "pruned": stats.pruned,
                "repeated_state_pruned": stats.repeated_state_pruned,
                "duration_ns": finished_ns - started_ns,
                "trace_length": len(trace_events or []),
            },
            trace=trace_events or [],
        )

    def _get_or_extend_state(
        self,
        state: _PrefixState,
        suffix: str,
        interpreter: MalbolgeInterpreter,
        cfg: GenerationConfig,
        cache: dict[str, _PrefixState],
        stats: _GenerationStats,
    ) -> tuple[_PrefixState, bool]:
        candidate_key = state.opcodes + suffix
        cached = cache.get(candidate_key)
        if cached is not None:
            stats.cache_hits += 1
            return cached, True
        extended = self._extend_state(
            state,
            suffix,
            interpreter,
            cfg,
            stats,
        )
        cache[candidate_key] = extended
        return extended, False

    def _extend_state(
        self,
        state: _PrefixState,
        suffix: str,
        interpreter: MalbolgeInterpreter,
        cfg: GenerationConfig,
        stats: _GenerationStats,
    ) -> _PrefixState:
        if not suffix:
            return state

        new_length = len(state.opcodes) + len(suffix)
        if new_length > cfg.max_program_length:
            raise MalbolgeRuntimeError(
                "Generated program exceeds maximum allowed length."
            )

        result = interpreter.execute_from_snapshot(
            state.machine,
            suffix,
            capture_machine=True,
        )
        stats.evaluations += 1
        if result.machine is None:
            raise MalbolgeRuntimeError(
                "Interpreter failed to capture machine snapshot during extension."
            )

        combined = _PrefixState(
            opcodes=state.opcodes + suffix,
            output=state.output + result.output,
            machine=result.machine,
        )
        return combined
