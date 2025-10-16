# SPDX-License-Identifier: MIT
"""
Capture interpreter and generator benchmark baselines to JSON.

Usage:
    python benchmarks/capture_baseline.py --output benchmarks/baseline.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.bench_generator import CASES as GENERATOR_CASES
from benchmarks.bench_generator import time_generation
from benchmarks.bench_interpreter import build_cases, time_interpreter


def capture_interpreter_baseline() -> list[dict[str, Any]]:
    baseline: list[dict[str, Any]] = []
    for case in build_cases():
        fastest, average, metadata = time_interpreter(case)
        baseline.append(
            {
                "case": case.name,
                "opcodes_length": len(case.opcodes) if case.opcodes is not None else 0,
                "runs": case.runs,
                "fastest_us": fastest * 1e6,
                "average_us": average * 1e6,
                "metadata": metadata,
                "synthetic": case.synthetic,
            }
        )
    return baseline


def capture_generator_baseline() -> list[dict[str, Any]]:
    baseline: list[dict[str, Any]] = []
    for case in GENERATOR_CASES:
        fastest, average, stats = time_generation(case)
        baseline.append(
            {
                "case": case.name,
                "target": case.target,
                "runs": case.runs,
                "config": {
                    "random_seed": case.config.random_seed,
                    "max_search_depth": case.config.max_search_depth,
                    "opcode_choices": case.config.opcode_choices,
                },
                "fastest_s": fastest,
                "average_s": average,
                "stats": stats,
            }
        )
    return baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture interpreter and generator benchmark baselines."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks") / "baseline.json",
        help="Path to write JSON baseline (default: benchmarks/baseline.json).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = args.output
    baseline = {
        "interpreter": capture_interpreter_baseline(),
        "generator": capture_generator_baseline(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    print(f"Wrote benchmark baseline to {output_path}")


if __name__ == "__main__":
    main()
