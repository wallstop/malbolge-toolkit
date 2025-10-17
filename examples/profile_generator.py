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

try:
    from malbolge import GenerationConfig, ProgramGenerator
except ImportError:  # pragma: no cover - fallback for direct script invocation
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

    durations: list[float] = []
    evaluations: list[int] = []
    cache_hits: list[int] = []
    pruned: list[int] = []
    repeated_pruned: list[int] = []

    for run in range(args.runs):
        start = time.perf_counter()
        result = generator.generate_for_string(args.text, config=config)
        duration = time.perf_counter() - start

        durations.append(duration)
        evaluations.append(int(result.stats.get("evaluations", 0) or 0))
        cache_hits.append(int(result.stats.get("cache_hits", 0) or 0))
        pruned.append(int(result.stats.get("pruned", 0) or 0))
        repeated_pruned.append(int(result.stats.get("repeated_state_pruned", 0) or 0))

        print(
            f"[run {run+1}] duration={duration:.6f}s "
            f"evaluations={evaluations[-1]} cache_hits={cache_hits[-1]} "
            f"pruned={pruned[-1]} repeated_pruned={repeated_pruned[-1]}"
        )

    print("\n=== Summary ===")
    print(f"Target: {args.text!r}")
    print(f"Runs: {args.runs}")
    fastest = min(durations)
    average_duration = statistics.mean(durations)
    print(f"Duration fastest: {fastest:.6f}s  average: {average_duration:.6f}s")
    print(f"Evaluations avg: {statistics.mean(evaluations):.2f}")
    print(f"Cache hits avg: {statistics.mean(cache_hits):.2f}")
    print(f"Pruned avg: {statistics.mean(pruned):.2f}")
    print(f"Repeated pruned avg: {statistics.mean(repeated_pruned):.2f}")


if __name__ == "__main__":
    main()
