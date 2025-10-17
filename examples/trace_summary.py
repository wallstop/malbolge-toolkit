# SPDX-License-Identifier: MIT
"""
Summarise generator trace events.

Usage:
    python examples/trace_summary.py --text "Hi" --seed 42 --limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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
        description="Generate a trace summary for a target string."
    )
    parser.add_argument("--text", default="Hello", help="Target string to generate.")
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for deterministic search."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of trace events to display (0 for all).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    generator = ProgramGenerator()
    config = GenerationConfig(random_seed=args.seed, capture_trace=True)
    result = generator.generate_for_string(args.text, config=config)

    print("Stats:")
    print(json.dumps(result.stats, indent=2))

    reasons = Counter(event.get("reason", "unknown") for event in result.trace)
    print("\nReason summary:")
    print(json.dumps(reasons, indent=2))

    limit = args.limit if args.limit > 0 else len(result.trace)
    print(f"\nFirst {limit} trace events:")
    for event in result.trace[:limit]:
        print(json.dumps(event, ensure_ascii=False))


if __name__ == "__main__":
    main()
