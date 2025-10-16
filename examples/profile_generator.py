# SPDX-License-Identifier: MIT
"""
Example: profile generator heuristics across multiple runs.

Run with:
    python examples/profile_generator.py --text "Hello" --runs 5
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from malbolge import GenerationConfig, ProgramGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile Malbolge generator heuristics."
    )
    parser.add_argument("--text", default="Hello", help="Target string to generate.")
    parser.add_argument("--runs", type=int, default=5, help="Number of timed runs.")
    parser.add_argument(
        "--seed", type=int, default=1234, help="Random seed for deterministic search."
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum search depth before randomization.",
    )
    parser.add_argument(
        "--opcodes", default="op*", help="Opcode choices considered during search."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generator = ProgramGenerator()
    config = GenerationConfig(
        opcode_choices=args.opcodes,
        max_search_depth=args.max_depth,
        random_seed=args.seed,
    )

    durations: List[float] = []
    evaluations: List[int] = []
    cache_hits: List[int] = []
    pruned: List[int] = []

    for run in range(args.runs):
        start = time.perf_counter()
        result = generator.generate_for_string(args.text, config=config)
        duration = time.perf_counter() - start

        durations.append(duration)
        evaluations.append(result.stats.get("evaluations", 0))
        cache_hits.append(result.stats.get("cache_hits", 0))
        pruned.append(result.stats.get("pruned", 0))

        print(
            f"[run {run+1}] duration={duration:.6f}s evaluations={evaluations[-1]} cache_hits={cache_hits[-1]} pruned={pruned[-1]}"
        )

    print("\n=== Summary ===")
    print(f"Target: {args.text!r}")
    print(f"Runs: {args.runs}")
    print(
        f"Duration fastest: {min(durations):.6f}s  average: {statistics.mean(durations):.6f}s"
    )
    print(f"Evaluations avg: {statistics.mean(evaluations):.2f}")
    print(f"Cache hits avg: {statistics.mean(cache_hits):.2f}")
    print(f"Pruned avg: {statistics.mean(pruned):.2f}")


if __name__ == "__main__":
    main()
