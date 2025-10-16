# SPDX-License-Identifier: MIT
"""
Micro-benchmarks for the Malbolge interpreter.

Run with:
    python -m benchmarks.bench_interpreter
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from statistics import mean

from malbolge import GenerationConfig, MalbolgeInterpreter, ProgramGenerator


@dataclass
class BenchmarkCase:
    name: str
    opcodes: str
    runs: int = 5


def build_cases() -> list[BenchmarkCase]:
    generator = ProgramGenerator()
    sample_program = generator.generate_for_string(
        "Hi", config=GenerationConfig(random_seed=1234)
    ).opcodes
    return [
        BenchmarkCase("noop", "v"),
        BenchmarkCase("generated_hi", sample_program),
    ]


def time_interpreter(case: BenchmarkCase) -> tuple[float, float]:
    interpreter = MalbolgeInterpreter()
    measurements: list[float] = []

    for _ in range(case.runs):
        start = time.perf_counter()
        interpreter.execute(case.opcodes)
        end = time.perf_counter()
        measurements.append(end - start)

    return min(measurements), mean(measurements)


def main() -> None:
    print("Interpreter Benchmarks")
    print("======================")
    for case in build_cases():
        fastest, average = time_interpreter(case)
        print(
            f"{case.name:20s}  fastest: {fastest * 1e6:9.2f} µs  "
            f"average: {average * 1e6:9.2f} µs"
        )


if __name__ == "__main__":
    main()
