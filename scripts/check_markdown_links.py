"""
Validate Markdown link text to ensure human readability.

This script enforces the project's documentation guideline that every
Markdown link must use descriptive, human-readable text rather than
bare URLs or placeholder phrases. The checks intentionally avoid
parsing content inside fenced code blocks, since links there are
usually illustrative.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import Path

# The patterns target inline links ([text](url)) and reference links ([text][label]).
INLINE_LINK_RE = re.compile(
    r"(?<!\!)\[(?P<text>[^\]]+)\]\(\s*(?P<url>[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)"
)
REFERENCE_LINK_RE = re.compile(r"(?<!\!)\[(?P<text>[^\]]+)\]\[(?P<label>[^\]]*)\]")

# Terms that should not be used as link text because they fail to describe the target.
PROHIBITED_TEXT = {"click here", "here", "link", "this link"}


def collect_markdown_files(paths: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for entry in paths:
        path = Path(entry)
        if path.is_dir():
            files.update(path.rglob("*.md"))
        elif path.suffix.lower() == ".md":
            files.add(path)
    return sorted(files)


def iter_relevant_lines(path: Path) -> Iterable[tuple[int, str]]:
    """Yield (line_number, content) pairs, skipping fenced code blocks."""
    inside_fence = False
    fence_marker: str | None = None

    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if stripped.startswith(("```", "~~~")):
                marker = stripped[:3]
                if inside_fence and marker == fence_marker:
                    inside_fence = False
                    fence_marker = None
                elif not inside_fence:
                    inside_fence = True
                    fence_marker = marker
                continue

            if inside_fence:
                continue

            yield line_number, raw_line


def is_human_readable(text: str, url: str | None = None) -> bool:
    candidate = text.strip()
    if not candidate:
        return False

    normalized = candidate.lower()
    if normalized in PROHIBITED_TEXT:
        return False

    if url and candidate.lower().strip("<>") == url.lower().strip("<>"):
        return False

    if normalized.startswith("http://") or normalized.startswith("https://"):
        return False

    if re.fullmatch(r"https?://\S+", candidate):
        return False

    # Require at least one alphabetic character to encourage descriptive text.
    if not re.search(r"[A-Za-z]", candidate):
        return False

    return True


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []

    for line_number, line in iter_relevant_lines(path):
        for match in INLINE_LINK_RE.finditer(line):
            link_text = match.group("text")
            url = match.group("url")
            if not is_human_readable(link_text, url):
                errors.append(
                    f"{path}:{line_number} Inline link text '{link_text}' "
                    "should be descriptive."
                )
        for match in REFERENCE_LINK_RE.finditer(line):
            link_text = match.group("text")
            if not is_human_readable(link_text):
                errors.append(
                    f"{path}:{line_number} Reference link text '{link_text}' "
                    "should be descriptive."
                )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ensure Markdown link text is descriptive."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Markdown files or directories to validate (defaults to repository root).",
    )
    args = parser.parse_args(argv)

    targets = args.paths or ["."]
    markdown_files = collect_markdown_files(targets)
    if not markdown_files:
        return 0

    failures: list[str] = []
    for file_path in markdown_files:
        failures.extend(validate_file(file_path))

    if failures:
        print(
            "Markdown link text validation failed for the following links:",
            file=sys.stderr,
        )
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
