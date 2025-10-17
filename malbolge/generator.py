# SPDX-License-Identifier: MIT
"""
Program generation strategies for Malbolge.

The current implementation mirrors the legacy breadth-first search algorithm
but routes execution through the new interpreter and exposes configuration
hooks for determinism and performance tuning.
"""

from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)


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
    stats: dict[str, int | float]
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
        return len(machine.tape), machine.a % 256, machine.c, machine.d, tail

    @staticmethod
    def _fallback_signature(
        machine: MalbolgeMachine,
    ) -> tuple[int, int, int, int, tuple[int, ...]]:
        tail_width = (
            SIGNATURE_TAPE_WIDTH if SIGNATURE_TAPE_WIDTH > 0 else len(machine.tape)
        )
        tail = tuple(machine.tape[-tail_width:]) if tail_width else ()
        return len(machine.tape), machine.a, machine.c, machine.d, tail

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
        seen_states: dict[tuple[int, int, int, int, tuple[int, ...]], int] = {}
        canonical_signatures: dict[StateSignature, int] = {}
        signature_collisions = 0
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
        fallback_prefix = self._fallback_signature(prefix_state.machine)
        seen_states[fallback_prefix] = len(prefix_state.output)
        canonical_signatures[self._state_signature(prefix_state.machine)] = len(
            prefix_state.output
        )

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
            logger.debug(
                "generation_trace_event",
                extra={
                    "status": reason,
                    "candidate": candidate,
                    "pruned": pruned,
                    "cache_hit": cache_hit,
                    "trace_depth": depth_level,
                },
            )
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
                    fallback_key = self._fallback_signature(combined_state.machine)
                    output_value = combined_state.output
                    output_length = len(output_value)
                    known_output_length = seen_states.get(fallback_key)
                    is_new_state = (
                        known_output_length is None
                        or output_length > known_output_length
                    )
                    previous_signature_output = canonical_signatures.get(signature)
                    is_new_by_signature = (
                        previous_signature_output is None
                        or output_length > previous_signature_output
                    )
                    valid_prefix = target.startswith(output_value) and (
                        output_length <= len(target)
                    )

                    pruned = False
                    reason = "candidate_retained"

                    if valid_prefix and output_value == target_prefix:
                        seen_states[fallback_key] = max(
                            known_output_length or 0, output_length
                        )
                        canonical_signatures[signature] = max(
                            previous_signature_output or 0, output_length
                        )
                        prefix_state = combined_state
                        found = True
                        reason = "accepted"
                    elif not valid_prefix:
                        stats.pruned += 1
                        dead_programs.add(program_key)
                        pruned = True
                        reason = "prefix_mismatch"
                    elif not is_new_state:
                        stats.pruned += 1
                        stats.repeated_state_pruned += 1
                        dead_programs.add(program_key)
                        state_cache.pop(program_key, None)
                        pruned = True
                        reason = "repeated_state"
                    else:
                        if not is_new_by_signature:
                            signature_collisions += 1
                            reason = "signature_collision"
                        if (
                            known_output_length is None
                            or output_length > known_output_length
                        ):
                            seen_states[fallback_key] = output_length
                        if (
                            previous_signature_output is None
                            or output_length > previous_signature_output
                        ):
                            canonical_signatures[signature] = output_length

                    _record_trace(
                        suffix,
                        output_value,
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

                if not combinations:
                    raise MalbolgeRuntimeError(
                        "Exhausted opcode search before reaching target prefix "
                        f"'{target_prefix}'."
                    )

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
                    random_fallback = self._fallback_signature(random_state.machine)
                    random_output_length = len(random_state.output)
                    random_known_length = seen_states.get(random_fallback)
                    random_is_new = (
                        random_known_length is None
                        or random_output_length > random_known_length
                    )
                    random_previous_signature = canonical_signatures.get(
                        random_signature
                    )
                    random_is_new_by_signature = (
                        random_previous_signature is None
                        or random_output_length > random_previous_signature
                    )
                    if not random_is_new:
                        stats.pruned += 1
                        stats.repeated_state_pruned += 1
                        state_cache.pop(random_key, None)
                        random_pruned = True
                        random_reason = "repeated_state"
                    else:
                        if not random_is_new_by_signature:
                            signature_collisions += 1
                            random_reason = "collision_extension"
                        if (
                            random_known_length is None
                            or random_output_length > random_known_length
                        ):
                            seen_states[random_fallback] = random_output_length
                        if (
                            random_previous_signature is None
                            or random_output_length > random_previous_signature
                        ):
                            canonical_signatures[random_signature] = (
                                random_output_length
                            )
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
        final_key = self._fallback_signature(final_state.machine)
        final_signature = self._state_signature(final_state.machine)
        final_output_length = len(final_state.output)
        seen_states[final_key] = final_output_length
        canonical_signatures[final_signature] = max(
            canonical_signatures.get(final_signature, 0),
            final_output_length,
        )
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
        total_repeated = stats.repeated_state_pruned + signature_collisions
        total_pruned = stats.pruned

        return GenerationResult(
            target=target,
            opcodes=final_program,
            machine_output=final_output,
            stats={
                "evaluations": stats.evaluations,
                "cache_hits": stats.cache_hits,
                "pruned": total_pruned,
                "repeated_state_pruned": total_repeated,
                "duration_ns": finished_ns - started_ns,
                "trace_length": len(trace_events or []),
                "pruned_ratio": (
                    total_pruned / stats.evaluations if stats.evaluations else 0.0
                ),
                "repeated_state_ratio": (
                    total_repeated / total_pruned if total_pruned else 0.0
                ),
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
