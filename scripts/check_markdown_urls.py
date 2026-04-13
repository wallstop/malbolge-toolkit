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

SKIP_SCHEMES = {"mailto", "tel", "irc", "ssh"}
ALLOWED_URL_PATTERNS = [
    re.compile(r"^https://www\.trs\.cm\.is\.nagoya-u\.ac\.jp/"),
]
# Network and certificate transport failures that are often transient and
# outside repository control. Error names are sourced from aiohttp 3.x client
# exceptions and Python built-in timeout errors. We keep deterministic content
# failures (e.g. 404, malformed URLs, persistent DNS unknown-host such as
# "No address associated with hostname", which is intentionally not listed in
# TRANSIENT_ERROR_SUBSTRINGS) as hard failures.
TRANSIENT_ERROR_CLASS_NAMES = {
    "ClientConnectorCertificateError",
    "ClientProxyConnectionError",
    "ClientOSError",
    "ClientConnectionError",
    "ServerTimeoutError",
    "ConnectionTimeoutError",
    "SocketTimeoutError",
    "TimeoutError",
}
TRANSIENT_ERROR_SUBSTRINGS = (
    "certificate verify failed",
    "temporary failure in name resolution",
    "network is unreachable",
    "connection reset",
    "timed out",
)


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


def is_transient_network_error(error: object) -> bool:
    """Return True when link-check errors are likely transient transport failures."""
    if not isinstance(error, Exception):
        return False
    if any(cls.__name__ in TRANSIENT_ERROR_CLASS_NAMES for cls in type(error).__mro__):
        return True
    message = summarize_error(error).lower()
    return any(marker in message for marker in TRANSIENT_ERROR_SUBSTRINGS)


def check_target(path: Path) -> Iterable[tuple[str, str, object]]:
    # Imported locally to allow unit tests to mock linkcheck behavior without
    # requiring linkcheckmd as a test dependency.
    import linkcheckmd

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
    parser.add_argument(
        "--strict-network",
        action="store_true",
        help=(
            "Treat transient network/certificate/timeout failures as hard failures "
            "(default: report diagnostics but do not fail)."
        ),
    )
    args = parser.parse_args(argv)

    failures: list[tuple[str, str, object]] = []
    transient_failures: list[tuple[str, str, object]] = []
    for target in collect_targets(args.paths):
        for origin, url, error in check_target(target):
            if should_skip_link(url):
                continue
            if not args.strict_network and is_transient_network_error(error):
                transient_failures.append((origin, url, error))
                continue
            failures.append((origin, url, error))

    if transient_failures:
        print(
            (
                "Transient Markdown link check failures detected "
                f"(ignored): {len(transient_failures)}"
            ),
            file=sys.stderr,
        )
        for origin, url, error in transient_failures:
            print(f"  - {origin}: {url} -> {summarize_error(error)}", file=sys.stderr)
        print(
            "Re-run with --strict-network to fail on transient network errors.",
            file=sys.stderr,
        )

    if failures:
        print("Broken Markdown links detected:", file=sys.stderr)
        for origin, url, error in failures:
            print(f"  - {origin}: {url} -> {summarize_error(error)}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
