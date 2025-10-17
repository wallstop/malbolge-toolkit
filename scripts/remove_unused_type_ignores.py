from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path

TYPE_IGNORE_PATTERN = re.compile(r"#\s*type:\s*ignore(?:\[[^\]]+\])?", re.IGNORECASE)
UNUSED_IGNORE_PATTERN = re.compile(
    r"^(?P<path>.*?):(?P<line>\d+): error: Unused \"type: ignore\" comment"
    r"\s+\[unused-ignore\]$"
)
SUMMARY_PREFIXES = ("Found ", "Success: ")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove unused `type: ignore` annotations using mypy output."
    )
    parser.add_argument("filenames", nargs="*")
    return parser.parse_args(argv)


def files_with_type_ignore(paths: Iterable[str]) -> list[Path]:
    result: list[Path] = []
    for name in paths:
        path = Path(name)
        if path.suffix != ".py":
            continue
        try:
            if "type: ignore" not in path.read_text(encoding="utf-8"):
                continue
        except FileNotFoundError:
            continue
        result.append(path)
    return result


def run_mypy(paths: Sequence[Path]) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "-m",
        "mypy",
        "--warn-unused-ignores",
        "--hide-error-context",
        "--no-error-summary",
    ]
    command.extend(str(path) for path in paths)
    return subprocess.run(command, check=False, capture_output=True, text=True)


def collect_unused_ignores(
    stdout: str,
) -> tuple[dict[Path, set[int]], list[str]]:
    unused: dict[Path, set[int]] = defaultdict(set)
    other_lines: list[str] = []

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = UNUSED_IGNORE_PATTERN.match(line)
        if match:
            location = Path(match.group("path"))
            if not location.is_absolute():
                location = (Path.cwd() / location).resolve()
            unused[location].add(int(match.group("line")))
            continue
        if any(line.startswith(prefix) for prefix in SUMMARY_PREFIXES):
            continue
        other_lines.append(raw_line)

    return unused, other_lines


def strip_unused_ignores(locations: dict[Path, set[int]]) -> list[str]:
    updated: list[str] = []
    for absolute_path, lines in locations.items():
        try:
            content = absolute_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        segments = content.splitlines(keepends=True)
        changed = False
        for line_number in sorted(lines):
            index = line_number - 1
            if not 0 <= index < len(segments):
                continue
            line = segments[index]

            if line.endswith("\r\n"):
                line_body = line[:-2]
                line_ending = "\r\n"
            elif line.endswith("\n"):
                line_body = line[:-1]
                line_ending = "\n"
            else:
                line_body = line
                line_ending = ""

            if TYPE_IGNORE_PATTERN.search(line_body) is None:
                continue

            new_body = TYPE_IGNORE_PATTERN.sub("", line_body).rstrip()
            segments[index] = (new_body + line_ending) if new_body else line_ending
            changed = True

        if changed:
            absolute_path.write_text("".join(segments), encoding="utf-8")
            try:
                updated.append(str(absolute_path.relative_to(Path.cwd())))
            except ValueError:
                updated.append(str(absolute_path))

    return updated


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    candidates = files_with_type_ignore(args.filenames)
    if not candidates:
        return 0

    result = run_mypy(candidates)

    if result.returncode == 0:
        return 0

    locations, other_errors = collect_unused_ignores(result.stdout)

    if other_errors or result.stderr:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        return result.returncode

    if not locations:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        return result.returncode

    updated = strip_unused_ignores(locations)
    for path in updated:
        print(f"Removed unused type: ignore comment(s) in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
