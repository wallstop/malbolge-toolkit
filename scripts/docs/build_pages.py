#!/usr/bin/env python3
"""
Build and preview the MkDocs site used for GitHub Pages.

This script prepares a staging directory from the repository content, then
invokes MkDocs with the theme configuration in mkdocs.yml. It is intended to
be the single entry point for local verification and CI builds.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STAGING_DIR = REPO_ROOT / "build" / "site-src"
DEFAULT_SITE_DIR = REPO_ROOT / "build" / "site"
MKDOCS_CONFIG = REPO_ROOT / "mkdocs.yml"


def copy_markdown_sources(staging_dir: Path) -> None:
    """
    Populate the staging directory with markdown sources.

    Currently pulls the project README (as index.md) and the entire docs/
    directory. Additional folders can be added here later without touching
    the MkDocs configuration.
    """
    staging_dir.mkdir(parents=True, exist_ok=True)

    readme_path = REPO_ROOT / "README.md"
    if readme_path.exists():
        shutil.copy2(readme_path, staging_dir / "index.md")

    agents_path = REPO_ROOT / "AGENTS.md"
    if agents_path.exists():
        shutil.copy2(agents_path, staging_dir / "AGENTS.md")

    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        shutil.copytree(
            docs_dir,
            staging_dir / "docs",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"),
        )

    examples_dir = REPO_ROOT / "examples"
    if examples_dir.exists():
        shutil.copytree(
            examples_dir,
            staging_dir / "examples",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"),
        )


def prepare_staging(clean: bool) -> None:
    """Create a fresh staging tree for MkDocs."""
    if clean and DEFAULT_STAGING_DIR.exists():
        shutil.rmtree(DEFAULT_STAGING_DIR)
    if clean and DEFAULT_SITE_DIR.exists():
        shutil.rmtree(DEFAULT_SITE_DIR)

    copy_markdown_sources(DEFAULT_STAGING_DIR)
    rewrite_readme_links(DEFAULT_STAGING_DIR)
    rewrite_directory_links(DEFAULT_STAGING_DIR)


def rewrite_readme_links(staging_dir: Path) -> None:
    """
    Adjust README links in staged files to point at the MkDocs homepage.

    Any relative link to README.md is rewritten to the correct relative path
    to index.md within the staging tree to avoid duplicate homepage content.
    """
    index_path = staging_dir / "index.md"
    if not index_path.exists():
        return

    pattern = re.compile(r"\((?:\.{1,2}/)*README\.md(#[^)]+)?\)")

    for md_file in staging_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")

        def replace(match: re.Match, md_path: Path = md_file) -> str:
            anchor = match.group(1) or ""
            relative_index = Path(
                os.path.relpath(index_path, md_path.parent)
            ).as_posix()
            return f"({relative_index}{anchor})"

        updated = pattern.sub(replace, text)
        if updated != text:
            md_file.write_text(updated, encoding="utf-8")


def rewrite_directory_links(staging_dir: Path) -> None:
    """
    Normalize directory-style links to explicit files where needed.

    Some docs reference folders that contain README files; MkDocs expects a
    direct file target. This keeps those links valid without altering sources.
    """
    replacements = {
        "(../examples/samples)": "(../examples/samples/README.md)",
        "(../examples/samples/)": "(../examples/samples/README.md)",
        "(./samples)": "(samples/README.md)",
        "(./samples/)": "(samples/README.md)",
    }

    for md_file in staging_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != text:
            md_file.write_text(updated, encoding="utf-8")


def run_mkdocs(serve: bool, strict: bool, dev_addr: str) -> None:
    """
    Execute MkDocs with the repository configuration.

    Args:
        serve: Whether to run the development server instead of a build
        strict: Fail on warnings when building
        dev_addr: Address for mkdocs serve
    """
    command = [
        "mkdocs",
        "serve" if serve else "build",
        "--config-file",
        str(MKDOCS_CONFIG),
    ]

    if strict and not serve:
        command.append("--strict")

    if serve:
        command.extend(["--dev-addr", dev_addr])
    else:
        command.append("--clean")

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        message = (
            "mkdocs is not installed. "
            "Run `python -m pip install -r docs/requirements.txt`."
        )
        raise SystemExit(message) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Build or serve the documentation site configured in mkdocs.yml."
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run mkdocs serve for local preview instead of building the static site.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail the build on warnings.",
    )
    parser.add_argument(
        "--dev-addr",
        default="127.0.0.1:8000",
        help="Address for mkdocs serve (default: %(default)s).",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleaning existing build artifacts before preparing sources.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    prepare_staging(clean=not args.no_clean)
    run_mkdocs(serve=args.serve, strict=args.strict, dev_addr=args.dev_addr)


if __name__ == "__main__":
    main()
