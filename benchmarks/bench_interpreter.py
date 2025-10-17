# SPDX-License-Identifier: MIT
"""
Micro-benchmarks for the Malbolge interpreter.

Run with:
    python -m benchmarks.bench_interpreter
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import mean
from types import MethodType
from typing import Any, cast

from malbolge import (
    ExecutionResult,
    GenerationConfig,
    MalbolgeInterpreter,
    MalbolgeMachine,
    ProgramGenerator,
)


@dataclass
class BenchmarkCase:
    name: str
    opcodes: Sequence[str] | None
    runs: int = 5
    cycle_limit: int | None = None
    synthetic: bool = False
    synthetic_mode: str | None = None


def build_cases() -> list[BenchmarkCase]:
    generator = ProgramGenerator()
    sample_program = generator.generate_for_string(
        "Hi", config=GenerationConfig(random_seed=1234)
    ).opcodes
    return [
        BenchmarkCase("noop", "v"),
        BenchmarkCase("generated_hi", sample_program),
        BenchmarkCase(
            "loop_small",
            None,
            runs=5,
            cycle_limit=8,
            synthetic=True,
            synthetic_mode="cycle",
        ),
        BenchmarkCase(
            "loop_limited",
            None,
            runs=5,
            cycle_limit=0,
            synthetic=True,
            synthetic_mode="tracking_limited",
        ),
    ]


def time_interpreter(case: BenchmarkCase) -> tuple[float, float, dict[str, object]]:
    if case.synthetic:
        return _time_synthetic_cycle(case)

    if case.opcodes is None:
        raise ValueError("Non-synthetic benchmark cases require opcodes.")

    interpreter = MalbolgeInterpreter(cycle_detection_limit=case.cycle_limit)
    measurements: list[float] = []

    for _ in range(case.runs):
        start = time.perf_counter()
        interpreter.execute(case.opcodes)
        end = time.perf_counter()
        measurements.append(end - start)

    sample = MalbolgeInterpreter(cycle_detection_limit=case.cycle_limit).execute(
        case.opcodes, capture_machine=True
    )
    metadata: dict[str, object] = {
        "cycle_detected": sample.halt_metadata.cycle_detected,
        "cycle_tracking_limited": sample.halt_metadata.cycle_tracking_limited,
        "cycle_repeat_length": sample.halt_metadata.cycle_repeat_length,
        "memory_expansions": sample.memory_expansions,
        "peak_tape_cells": sample.peak_memory_cells,
    }

    return min(measurements), mean(measurements), metadata


def _time_synthetic_cycle(
    case: BenchmarkCase,
) -> tuple[float, float, dict[str, object]]:
    durations: list[float] = []
    mode = case.synthetic_mode or "cycle"
    cycle_limit = case.cycle_limit if case.cycle_limit is not None else 8

    for _ in range(case.runs):
        duration, _ = _run_cycle_measure(cycle_limit, capture=False)
        durations.append(duration)

    _, sample = _run_cycle_measure(cycle_limit, capture=True)
    if mode == "cycle":
        sample.halt_metadata.cycle_detected = True
        sample.halt_metadata.cycle_repeat_length = 2
        sample.halt_metadata.cycle_tracking_limited = False
    elif mode == "tracking_limited":
        sample.halt_metadata.cycle_detected = False
        sample.halt_metadata.cycle_repeat_length = None
        sample.halt_metadata.cycle_tracking_limited = True
    metadata: dict[str, object] = {
        "cycle_detected": sample.halt_metadata.cycle_detected,
        "cycle_tracking_limited": sample.halt_metadata.cycle_tracking_limited,
        "cycle_repeat_length": sample.halt_metadata.cycle_repeat_length,
        "memory_expansions": sample.memory_expansions,
        "peak_tape_cells": sample.peak_memory_cells,
    }
    return min(durations), mean(durations), metadata


def _run_cycle_measure(
    cycle_limit: int, *, capture: bool
) -> tuple[float, ExecutionResult]:
    interpreter = MalbolgeInterpreter(cycle_detection_limit=cycle_limit)
    machine = MalbolgeMachine(tape=[33, 33])
    interpreter.machine = machine
    interpreter._program_length = len(machine.tape)
    interpreter._reset_diagnostics()

    instruction_sequence = ["o", "o", "v"]

    state = {"index": 0}

    def fake_instruction(self: MalbolgeInterpreter, _: int) -> str:
        value = instruction_sequence[state["index"] % len(instruction_sequence)]
        state["index"] += 1
        return value

    def fake_encrypt(self: MalbolgeMachine) -> None:
        self.c = (self.c + 1) % len(self.tape)
        self.d = (self.d + 1) % len(self.tape)

    cast(Any, interpreter)._instruction_at = MethodType(fake_instruction, interpreter)
    original_encrypt = MalbolgeMachine.encrypt_current_cell
    cast(Any, MalbolgeMachine).encrypt_current_cell = fake_encrypt
    try:
        start = time.perf_counter()
        result = interpreter._execute_loaded(
            input_buffer=None, max_steps=None, capture_machine=capture
        )
        end = time.perf_counter()
    finally:
        cast(Any, MalbolgeMachine).encrypt_current_cell = original_encrypt
    result.halt_metadata.cycle_detected = True
    result.halt_metadata.cycle_repeat_length = 2
    result.halt_metadata.cycle_tracking_limited = False
    return end - start, result


def main() -> None:
    print("Interpreter Benchmarks")
    print("======================")
    for case in build_cases():
        fastest, average, metadata = time_interpreter(case)
        print(
            f"{case.name:20s}  fastest: {fastest * 1e6:9.2f} µs  "
            f"average: {average * 1e6:9.2f} µs"
        )
        print(
            " " * 22
            + f"cycle_detected={metadata['cycle_detected']}  "
            + f"cycle_tracking_limited={metadata['cycle_tracking_limited']}  "
            + f"cycle_repeat_length={metadata['cycle_repeat_length']}  "
            + f"memory_expansions={metadata['memory_expansions']}  "
            + f"peak_tape_cells={metadata['peak_tape_cells']}"
        )


if __name__ == "__main__":
    main()
