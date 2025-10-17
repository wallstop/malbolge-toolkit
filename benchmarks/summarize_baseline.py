# SPDX-License-Identifier: MIT
"""Summarise benchmark baselines for dashboards or quick inspection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarise interpreter/generator metrics from a baseline JSON."
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


def _summarise_interpreter(entries: list[dict[str, Any]]) -> str:
    lines = ["Interpreter Summary", "-------------------"]
    for entry in entries:
        meta = entry.get("metadata", {})
        label = " (synthetic)" if entry.get("synthetic") else ""
        lines.append(
            f"{entry['case']:20s} len={entry['opcodes_length']:4d} "
            f"runs={entry['runs']:2d}{label}"
        )
        lines.append(
            "  "
            + (
                f"fastest={entry['fastest_us']:.3f}us "
                f"average={entry['average_us']:.3f}us "
            )
            + f"cycle_repeat_length={meta.get('cycle_repeat_length')}"
        )
    lines.append("")
    return "\n".join(lines)


def _summarise_generator(entries: list[dict[str, Any]]) -> str:
    lines = ["Generator Summary", "------------------"]
    for entry in entries:
        stats = entry.get("stats", {})
        lines.append(
            f"{entry['case']:20s} target='{entry['target']}' runs={entry['runs']:2d}"
        )
        lines.append(
            "  "
            + (
                f"fastest={entry['fastest_s']:.3f}s "
                f"average={entry['average_s']:.3f}s "
            )
            + f"pruned={stats.get('pruned')} "
            + f"repeated_state_pruned={stats.get('repeated_state_pruned')}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    baseline = _load(args.baseline)
    print(_summarise_interpreter(baseline.get("interpreter", [])), end="")
    print(_summarise_generator(baseline.get("generator", [])), end="")


if __name__ == "__main__":
    main()
