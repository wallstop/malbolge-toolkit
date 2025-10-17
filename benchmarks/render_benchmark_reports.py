# SPDX-License-Identifier: MIT
"""
Render combined benchmark summaries in Markdown for dashboards or CI artifacts.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .cycle_repeat_report import _extract_lengths, render_cycle_table, render_histogram
from .summarize_baseline import _load, _summarise_generator, _summarise_interpreter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render Markdown reports combining benchmark summaries and cycle "
            "histograms."
        )
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("benchmarks") / "baseline.json",
        help="Input baseline JSON file (default: benchmarks/baseline.json).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination Markdown file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline = _load(args.baseline)
    interpreter_entries = baseline.get("interpreter", [])
    generator_entries = baseline.get("generator", [])
    histogram = render_histogram(_extract_lengths_counter(interpreter_entries)).strip()
    per_case = render_cycle_table(interpreter_entries).strip()

    lines = [
        "# Benchmark Summary",
        "",
        "## Interpreter",
        "",
        "```",
        _summarise_interpreter(interpreter_entries).strip(),
        "```",
        "",
        "## Generator",
        "",
        "```",
        _summarise_generator(generator_entries).strip(),
        "```",
        "",
        "## Cycle Repeat-Length Histogram",
        "",
        "```",
        histogram,
        "```",
        "",
        "## Cycle Details",
        "",
        "```",
        per_case,
        "```",
    ]
    args.output.write_text("\n".join(lines), encoding="utf-8")


def _extract_lengths_counter(entries: Iterable[dict[str, Any]]) -> Counter[int]:
    if isinstance(entries, list):
        materialized = entries
    else:
        materialized = list(entries)
    return Counter(_extract_lengths(materialized))


if __name__ == "__main__":
    main()
