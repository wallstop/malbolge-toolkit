# SPDX-License-Identifier: MIT
"""
Render cycle repeat-length statistics from interpreter benchmarks.

Usage:
    python benchmarks/cycle_repeat_report.py --baseline benchmarks/baseline.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report cycle repeat-length statistics for interpreter baselines."
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("benchmarks") / "baseline.json",
        help="Path to the baseline JSON file (default: benchmarks/baseline.json).",
    )
    return parser.parse_args()


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Baseline JSON must be an object.")
    return cast(dict[str, Any], data)


def _extract_lengths(entries: list[dict[str, Any]]) -> list[int]:
    lengths: list[int] = []
    for entry in entries:
        metadata = entry.get("metadata", {})
        length = metadata.get("cycle_repeat_length")
        if isinstance(length, int):
            lengths.append(length)
    return lengths


def render_histogram(counts: Counter[int]) -> str:
    if not counts:
        return "No cycle repeat lengths recorded.\n"
    lines = ["Cycle Repeat-Length Histogram", "-----------------------------"]
    max_count = max(counts.values())
    for length in sorted(counts):
        count = counts[length]
        bar = "#" * max(1, int(round((count / max_count) * 40)))
        lines.append(f"{length:>6} : {count:>3} {bar}")
    lines.append("")
    return "\n".join(lines)


def render_cycle_table(entries: list[dict[str, Any]]) -> str:
    lines = ["Per-case Cycle Data", "---------------------"]
    for entry in entries:
        metadata = entry.get("metadata", {})
        lines.append(
            f"{entry['case']:20s} repeat_length={metadata.get('cycle_repeat_length')} "
            f"cycle_detected={metadata.get('cycle_detected')} "
            f"cycle_tracking_limited={metadata.get('cycle_tracking_limited')}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    baseline = _load(args.baseline)
    interpreter_entries = baseline.get("interpreter", [])
    lengths = _extract_lengths(interpreter_entries)
    counts = Counter(lengths)
    print(render_histogram(counts), end="")
    print(render_cycle_table(interpreter_entries), end="")


if __name__ == "__main__":
    main()
