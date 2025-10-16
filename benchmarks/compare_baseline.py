# SPDX-License-Identifier: MIT
"""
Compare benchmark baselines and highlight performance deltas.

Usage examples:
    python benchmarks/compare_baseline.py \
        --baseline benchmarks/baseline.json \
        --candidate benchmarks/new_run.json
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - manual tool
        raise SystemExit(f"[error] baseline file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[error] failed to parse JSON from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"[error] baseline file must contain a JSON object: {path}")
    return cast(dict[str, Any], data)


def _lookup(items: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {entry["case"]: entry for entry in items}


def _format_delta(old: float, new: float) -> tuple[float, float]:
    absolute = new - old
    if old == 0:
        percent = math.inf if new != 0 else 0.0
    else:
        percent = (absolute / old) * 100.0
    return absolute, percent


def _summarise_section(
    name: str,
    baseline: Iterable[dict[str, Any]],
    candidate: Iterable[dict[str, Any]],
    *,
    fastest_key: str,
    average_key: str,
    units: str,
) -> tuple[str, list[tuple[str, float]]]:
    baseline_map = _lookup(baseline)
    candidate_map = _lookup(candidate)
    lines: list[str] = [f"{name} Benchmarks"]
    lines.append("-" * len(lines[0]))
    header = (
        "Case",
        f"Fastest ({units})",
        "Delta Fastest",
        f"Average ({units})",
        "Delta Average",
    )
    widths = [len(column) for column in header]
    rows: list[tuple[str, str, str, str, str]] = []

    regressions: list[tuple[str, float]] = []

    for case_name, base_entry in sorted(baseline_map.items()):
        if case_name not in candidate_map:
            rows.append(
                (
                    case_name,
                    f"{base_entry[fastest_key]:.3f}",
                    "missing",
                    f"{base_entry[average_key]:.3f}",
                    "missing",
                )
            )
            continue
        cand_entry = candidate_map[case_name]
        fastest_delta = _format_delta(base_entry[fastest_key], cand_entry[fastest_key])
        average_delta = _format_delta(base_entry[average_key], cand_entry[average_key])
        fastest_str = f"{cand_entry[fastest_key]:.3f}"
        average_str = f"{cand_entry[average_key]:.3f}"
        fastest_delta_str = f"{fastest_delta[0]:+.3f} ({fastest_delta[1]:+.1f}%)"
        average_delta_str = f"{average_delta[0]:+.3f} ({average_delta[1]:+.1f}%)"
        if fastest_delta[1] == math.inf:
            regressions.append((case_name, math.inf))
        else:
            regressions.append((case_name, fastest_delta[1]))
        rows.append(
            (
                case_name,
                fastest_str,
                fastest_delta_str,
                average_str,
                average_delta_str,
            )
        )

    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    lines.append("  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(header)))
    lines.append("  ".join("-" * widths[idx] for idx in range(len(header))))
    for row in rows:
        lines.append("  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)))
    lines.append("")
    return "\n".join(lines), regressions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Malbolge benchmark baselines."
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("benchmarks") / "baseline.json",
        help="Reference baseline JSON (default: benchmarks/baseline.json).",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
        help="Newly captured benchmark JSON to compare against the baseline.",
    )
    parser.add_argument(
        "--allow-regression",
        type=float,
        default=5.0,
        help=(
            "Maximum allowed slowdown percentage before failing "
            "(applies to fastest measurement; default: 5%%)."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline = _load(args.baseline)
    candidate = _load(args.candidate)

    interpreter_section, interpreter_regressions = _summarise_section(
        "Interpreter",
        baseline.get("interpreter", []),
        candidate.get("interpreter", []),
        fastest_key="fastest_us",
        average_key="average_us",
        units="us",
    )
    generator_section, generator_regressions = _summarise_section(
        "Generator",
        baseline.get("generator", []),
        candidate.get("generator", []),
        fastest_key="fastest_s",
        average_key="average_s",
        units="s",
    )
    print(interpreter_section)
    print(generator_section)
    threshold = args.allow_regression
    offending = [
        (name, value)
        for name, value in interpreter_regressions + generator_regressions
        if value > threshold
    ]
    if offending:
        formatted = ", ".join(f"{case} (+{delta:.1f}%)" for case, delta in offending)
        raise SystemExit(
            f"[error] benchmark regressions exceed {threshold:.1f}%: {formatted}"
        )


if __name__ == "__main__":
    main()
