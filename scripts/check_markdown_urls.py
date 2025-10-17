"""
Verify that Markdown hyperlinks resolve successfully.

The script is designed to run under pre-commit and in CI to catch
broken links early. It wraps linkcheckmd so we can centralise project
specific allowlists (for example known certificates that fail validation)
and collect consistent failure messages.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

import linkcheckmd

SKIP_SCHEMES = {"mailto", "tel", "irc", "ssh"}
ALLOWED_URL_PATTERNS = [
    re.compile(r"^https://www\.trs\.cm\.is\.nagoya-u\.ac\.jp/"),
]


def collect_targets(arguments: Sequence[str]) -> list[Path]:
    if not arguments:
        return [Path(".")]
    return [Path(arg) for arg in arguments]


def should_skip_link(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        return True
    if parsed.scheme.lower() in SKIP_SCHEMES:
        return True
    for pattern in ALLOWED_URL_PATTERNS:
        if pattern.match(url):
            return True
    return False


def summarize_error(error: object) -> str:
    if isinstance(error, Exception):
        return repr(error)
    return str(error)


def check_target(path: Path) -> Iterable[tuple[str, str, object]]:
    result = linkcheckmd.check_links(
        path=path,
        ext=".md",
        method="get",
        use_async=True,
        recurse=path.is_dir(),
    )
    return cast(Iterable[tuple[str, str, object]], result)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown hyperlinks.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional paths (files or directories). Defaults to the repository root.",
    )
    args = parser.parse_args(argv)

    failures: list[tuple[str, str, object]] = []
    for target in collect_targets(args.paths):
        for origin, url, error in check_target(target):
            if should_skip_link(url):
                continue
            failures.append((origin, url, error))

    if failures:
        print("Broken Markdown links detected:", file=sys.stderr)
        for origin, url, error in failures:
            print(f"  - {origin}: {url} -> {summarize_error(error)}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
