# SPDX-License-Identifier: MIT
"""
Visualise generator trace events by depth and reason.

Usage examples:
    # Parse trace emitted by `python -m malbolge.cli generate --trace`
    python examples/trace_viz.py --path traces/hello-trace.json

    # Read from standard input (e.g., piped CLI output)
    python -m malbolge.cli generate --text "Hello" --seed 42 --trace \\
        | python examples/trace_viz.py --stdin
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def _load_trace_from_text(raw: str) -> list[dict[str, Any]]:
    """
    Attempt to decode trace data from a string.

    Handles plain JSON arrays, objects with a `trace` key, or CLI output that
    embeds `trace=` prefixes.
    """

    def _attempt_decode(candidate: str) -> list[dict[str, Any]] | None:
        candidate = candidate.strip()
        if not candidate:
            return None
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict) and "trace" in parsed:
            parsed_trace = parsed["trace"]
        else:
            parsed_trace = parsed
        if isinstance(parsed_trace, list):
            return [event for event in parsed_trace if isinstance(event, dict)]
        return None

    initial = _attempt_decode(raw)
    if initial is not None:
        return initial

    if "trace_summary" in raw and "trace=" in raw:
        before_summary = raw.split("trace_summary", 1)[0]
        extracted = before_summary.split("trace=", 1)[-1]
        decoded = _attempt_decode(extracted)
        if decoded is not None:
            return decoded

    if "trace=" in raw:
        extracted = raw.split("trace=", 1)[-1]
        decoded = _attempt_decode(extracted)
        if decoded is not None:
            return decoded

    decoded = _attempt_decode(raw[raw.find("[") :])
    if decoded is not None:
        return decoded

    raise ValueError(
        "Unable to parse trace content. Provide raw JSON or CLI output containing "
        "`trace=`."
    )


def _read_source(path: Path | None, use_stdin: bool) -> str:
    if use_stdin:
        data = sys.stdin.read()
        if not data:
            raise ValueError("No data received on stdin.")
        return data
    if path is None:
        raise ValueError("Either --path or --stdin must be supplied.")
    return path.read_text(encoding="utf-8")


def _render_bar(value: int, total: int, width: int = 40) -> str:
    if total <= 0 or value <= 0:
        return ""
    fraction = min(max(value / total, 0.0), 1.0)
    length = max(1, int(round(fraction * width)))
    return "#" * length


def _format_table(rows: Iterable[tuple[str, list[str]]]) -> str:
    col_widths: list[int] = []
    matrix: list[list[str]] = []
    for heading, columns in rows:
        row = [heading, *columns]
        matrix.append(row)
        for idx, cell in enumerate(row):
            if len(col_widths) <= idx:
                col_widths.append(len(cell))
            else:
                col_widths[idx] = max(col_widths[idx], len(cell))

    buffer = io.StringIO()
    for row in matrix:
        padded = "  ".join(cell.ljust(col_widths[idx]) for idx, cell in enumerate(row))
        buffer.write(padded)
        buffer.write("\n")
    return buffer.getvalue()


def summarise_trace(events: list[dict[str, Any]]) -> str:
    if not events:
        return "Trace is empty.\n"

    total_events = len(events)
    pruned = sum(1 for event in events if event.get("pruned"))
    accepted = sum(1 for event in events if not event.get("pruned"))

    depth_buckets: dict[int, Counter[str]] = defaultdict(Counter)
    reason_counts: Counter[str] = Counter()

    for event in events:
        depth = int(event.get("depth", 0) or 0)
        reason = str(event.get("reason", "unknown"))
        pruned_flag = "pruned" if event.get("pruned") else "retained"
        depth_buckets[depth][pruned_flag] += 1
        depth_buckets[depth][reason] += 1
        reason_counts[reason] += 1

    buffer = io.StringIO()
    buffer.write("Trace overview\n")
    buffer.write("================\n")
    buffer.write(f"Total events    : {total_events}\n")
    buffer.write(f"Pruned candidates: {pruned}\n")
    buffer.write(f"Retained paths  : {accepted}\n")
    buffer.write("\nDepth histogram\n----------------\n")

    rows: list[tuple[str, list[str]]] = []
    grand_totals: dict[str, int] = Counter()
    for depth in sorted(depth_buckets):
        counts = depth_buckets[depth]
        total_at_depth = sum(counts[flag] for flag in ("pruned", "retained"))
        pruned_count = counts.get("pruned", 0)
        retained_count = counts.get("retained", 0)
        grand_totals["pruned"] += pruned_count
        grand_totals["retained"] += retained_count
        row_cells = [
            f"total={total_at_depth}",
            (f"pruned={pruned_count} " f"{_render_bar(pruned_count, total_at_depth)}"),
            (
                f"retained={retained_count} "
                f"{_render_bar(retained_count, total_at_depth)}"
            ),
        ]
        rows.append((f"Depth {depth}", row_cells))

    if rows:
        buffer.write(_format_table(rows))
    else:
        buffer.write("No depth data available.\n")

    buffer.write("\nReason breakdown\n-----------------\n")
    for reason, count in reason_counts.most_common():
        bar = _render_bar(count, total_events)
        buffer.write(f"{reason:<24} {count:>6} {bar}\n")

    buffer.write(
        "\nTop retained candidates (first 5)\n---------------------------------\n"
    )
    retained_events = [event for event in events if not event.get("pruned")]
    for event in retained_events[:5]:
        buffer.write(
            f"depth={event.get('depth', 0)} "
            f"candidate={event.get('candidate')} "
            f"output={event.get('output')} "
            f"reason={event.get('reason')}\n"
        )

    return buffer.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render a textual visualisation for Malbolge generator trace events."
        )
    )
    parser.add_argument(
        "--path",
        type=Path,
        help=(
            "Path to a JSON file containing trace events "
            "(or CLI output with trace=...)."
        ),
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read trace data from standard input instead of a file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw = _read_source(args.path, args.stdin)
    events = _load_trace_from_text(raw)
    summary = summarise_trace(events)
    print(summary, end="")


if __name__ == "__main__":
    main()
