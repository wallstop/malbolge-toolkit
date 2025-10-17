# SPDX-License-Identifier: MIT
"""
Analyze Malbolge generator trace output captured from the CLI.

Usage:
    python examples/trace_analyzer.py --input trace.txt --top 10

The tool expects a file containing the CLI output from running
    python -m malbolge.cli generate --text "Hi" --trace > trace.txt
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize generator trace output.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to CLI output containing trace JSON.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of trace events to print (0 for all).",
    )
    return parser.parse_args()


def extract_trace_data(output: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    trace_line = None
    summary_line = None
    for line in output.splitlines():
        if line.startswith("trace="):
            trace_line = line[len("trace=") :]
        elif line.startswith("trace_summary="):
            summary_line = line[len("trace_summary=") :]
    if trace_line is None:
        raise ValueError(
            "No trace= line found in the provided file. Re-run the CLI with --trace."
        )
    trace_events = json.loads(trace_line)
    if not isinstance(trace_events, list):
        raise ValueError("Trace JSON is not a list of events.")
    summary = json.loads(summary_line) if summary_line else {}
    return trace_events, summary


def render_summary(
    trace_events: list[dict[str, Any]], summary: dict[str, int], top: int
) -> None:
    reason_counts = Counter(event.get("reason", "unknown") for event in trace_events)
    if summary:
        print("Reason summary (from CLI):")
        for reason, count in sorted(
            summary.items(), key=lambda item: item[1], reverse=True
        ):
            print(f"  {reason:20s} {count}")
    print("\nReason summary (recomputed):")
    for reason, count in reason_counts.most_common():
        print(f"  {reason:20s} {count}")
    if not trace_events:
        print("\nNo trace events found.")
        return
    limit = len(trace_events) if top <= 0 else min(top, len(trace_events))
    print(f"\nFirst {limit} trace events (candidate / pruned / reason):")
    for event in trace_events[:limit]:
        candidate = event.get("candidate", "")
        pruned = event.get("pruned", False)
        reason = event.get("reason", "unknown")
        depth = event.get("depth", "-")
        print(
            "  "
            + f"depth={depth:>3} "
            + f"pruned={str(pruned):5s} "
            + f"reason={reason:15s} "
            + f"candidate={candidate}"
        )


def main() -> None:
    args = parse_args()
    output_text = args.input.read_text(encoding="utf-8")
    trace_events, summary = extract_trace_data(output_text)
    render_summary(trace_events, summary, args.top)


if __name__ == "__main__":
    main()
