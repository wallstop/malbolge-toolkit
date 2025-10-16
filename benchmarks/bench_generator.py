# SPDX-License-Identifier: MIT
"""
Micro-benchmarks for the Malbolge program generator.

Run with:
    python -m benchmarks.bench_generator
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List, Tuple

from malbolge import GenerationConfig, ProgramGenerator


@dataclass
class BenchmarkCase:
    name: str
    target: str
    runs: int = 3
    config: GenerationConfig = field(
        default_factory=lambda: GenerationConfig(random_seed=1234)
    )


CASES: List[BenchmarkCase] = [
    BenchmarkCase("short", "Hi"),
    BenchmarkCase("longer", "Hello"),
]


def time_generation(case: BenchmarkCase) -> Tuple[float, float, Dict[str, int]]:
    generator = ProgramGenerator()
    measurements: List[float] = []
    stats: Dict[str, int] = {}

    for _ in range(case.runs):
        start = time.perf_counter()
        result = generator.generate_for_string(case.target, config=case.config)
        end = time.perf_counter()
        measurements.append(end - start)
        stats = result.stats

    return min(measurements), mean(measurements), stats


def main() -> None:
    print("Generator Benchmarks")
    print("====================")
    for case in CASES:
        fastest, average, stats = time_generation(case)
        stats_summary = ", ".join(f"{key}={value}" for key, value in stats.items())
        print(
            f"{case.name:20s}  fastest: {fastest:.6f} s  average: {average:.6f} s  [{stats_summary}]"
        )


if __name__ == "__main__":
    main()
