# SPDX-License-Identifier: MIT
"""
Program generation strategies for Malbolge.

The current implementation mirrors the legacy breadth-first search algorithm
but routes execution through the new interpreter and exposes configuration
hooks for determinism and performance tuning.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Dict, List, Set
from time import perf_counter_ns

from .encoding import reverse_normalize
from .interpreter import (
    MalbolgeInterpreter,
    MalbolgeMachine,
    MalbolgeRuntimeError,
)


@dataclass(slots=True)
class GenerationConfig:
    opcode_choices: str = "op*"
    max_search_depth: int = 5
    random_seed: int | None = None
    max_program_length: int = 59049


@dataclass(slots=True)
class GenerationResult:
    target: str
    opcodes: str
    machine_output: str
    stats: Dict[str, int]

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


class ProgramGenerator:
    def __init__(self, interpreter: MalbolgeInterpreter | None = None) -> None:
        self._interpreter = interpreter or MalbolgeInterpreter()

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
        state_cache: Dict[str, _PrefixState] = {}
        dead_programs: Set[str] = set()
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
                        continue
                    combined_state = self._get_or_extend_state(
                        prefix_state,
                        suffix,
                        interpreter,
                        cfg,
                        state_cache,
                        stats,
                    )
                    if not target.startswith(combined_state.output) or len(
                        combined_state.output
                    ) > len(target):
                        dead_programs.add(program_key)
                        stats.pruned += 1
                        continue
                    if combined_state.output == target_prefix:
                        prefix_state = combined_state
                        found = True
                        break

                if found:
                    break

                next_frontier: List[str] = []
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
                    prefix_state = self._extend_state(
                        prefix_state,
                        random_choice,
                        interpreter,
                        cfg,
                        state_cache,
                        stats,
                    )
                    combinations = list(cfg.opcode_choices)
                    depth = 0

        final_state = self._extend_state(
            prefix_state,
            "v",
            interpreter,
            cfg,
            state_cache,
            stats,
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
                "duration_ns": finished_ns - started_ns,
            },
        )

    def _get_or_extend_state(
        self,
        state: _PrefixState,
        suffix: str,
        interpreter: MalbolgeInterpreter,
        cfg: GenerationConfig,
        cache: Dict[str, _PrefixState],
        stats: _GenerationStats,
    ) -> _PrefixState:
        candidate_key = state.opcodes + suffix
        cached = cache.get(candidate_key)
        if cached is not None:
            stats.cache_hits += 1
            return cached
        extended = self._extend_state(
            state,
            suffix,
            interpreter,
            cfg,
            cache,
            stats,
        )
        cache[candidate_key] = extended
        return extended

    def _extend_state(
        self,
        state: _PrefixState,
        suffix: str,
        interpreter: MalbolgeInterpreter,
        cfg: GenerationConfig,
        cache: Dict[str, _PrefixState],
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
        cache[combined.opcodes] = combined
        return combined
