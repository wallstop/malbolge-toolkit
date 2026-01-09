#!/usr/bin/env python3
"""
Generate GitHub Wiki content from the repository markdown files.

Copies README.md and docs/*.md into a wiki-friendly structure, rewrites links
to point at the generated pages, and builds a simple sidebar/footer for the
wiki. Used by CI and by local verification.
"""

from __future__ import annotations

import argparse
import re
import shutil
from collections.abc import Callable, Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEST = REPO_ROOT / "build" / "wiki"


def _title_case_segment(segment: str) -> str:
    words = re.split(r"[-_\s]+", segment)
    return "-".join(word.capitalize() for word in words if word)


def path_to_wiki_name(relative_path: str) -> str:
    """
    Convert a repository-relative path to a wiki page name (no extension).

    Examples:
        docs/TUTORIAL.md -> Tutorial
        docs/MALBOLGE_PRIMER.md -> Malbolge-Primer
        README.md -> Home
    """
    path = relative_path.strip().replace("\\", "/")
    path = re.sub(r"^(?:\./|\.\./)+", "", path)

    if path.lower() == "readme.md":
        return "Home"

    if path.lower().startswith("docs/"):
        path = path[5:]

    if path.endswith(".md"):
        path = path[:-3]

    parts = [part for part in re.split(r"[\\/]+", path) if part]
    if not parts:
        return "Page"

    return "-".join(_title_case_segment(part) for part in parts)


def _split_anchor(target: str) -> tuple[str, str]:
    if "#" in target:
        base, anchor = target.split("#", 1)
        return base, f"#{anchor}"
    return target, ""


def transform_link_target(target: str) -> str:
    """
    Turn a relative markdown link target into a wiki link target.

    Leaves external links and pure anchors untouched.
    """
    if target.startswith("#"):
        return target
    if re.match(r"^[a-zA-Z]+://", target):
        return target

    base, anchor = _split_anchor(target)
    if not base.lower().endswith(".md"):
        return target

    wiki_name = path_to_wiki_name(base)
    return f"{wiki_name}{anchor}"


def _transform_preserving_code_blocks(
    content: str, transform_fn: Callable[[str], str]
) -> str:
    fenced_pattern = r"(```[\s\S]*?```|~~~[\s\S]*?~~~)"
    parts = re.split(fenced_pattern, content)

    result_parts: list[str] = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            result_parts.append(part)
        else:
            result_parts.append(transform_fn(part))

    return "".join(result_parts)


def _transform_links_in_text(text: str) -> str:
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def replace(match: re.Match[str]) -> str:
        label = match.group(1)
        target = match.group(2)

        if target.startswith(("http://", "https://", "#", "mailto:", "tel:")):
            return match.group(0)

        new_target = transform_link_target(target)
        return f"[{label}]({new_target})"

    return re.sub(pattern, replace, text)


def _transform_images_in_text(text: str) -> str:
    pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

    def replace(match: re.Match[str]) -> str:
        alt = match.group(1)
        target = match.group(2)

        if target.startswith(("http://", "https://", "//", "mailto:", "tel:")):
            return match.group(0)

        images_index = target.lower().find("images/")
        if images_index != -1:
            normalized = target[images_index:]
            return f"![{alt}]({normalized})"

        return match.group(0)

    return re.sub(pattern, replace, text)


def transform_wiki_links(content: str) -> str:
    with_links = _transform_preserving_code_blocks(content, _transform_links_in_text)
    return _transform_preserving_code_blocks(with_links, _transform_images_in_text)


def copy_markdown_file(src: Path, dest: Path) -> None:
    text = src.read_text(encoding="utf-8")
    transformed = transform_wiki_links(text)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(transformed, encoding="utf-8")


def clear_destination(dest_dir: Path) -> None:
    if not dest_dir.exists():
        return
    for entry in dest_dir.iterdir():
        if entry.name in {".git", ".gitignore", ".gitattributes"}:
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def collect_markdown_sources(source_dir: Path) -> Iterable[tuple[Path, str]]:
    docs_dir = source_dir / "docs"

    if (source_dir / "README.md").exists():
        yield source_dir / "README.md", "Home.md"

    if docs_dir.exists():
        for md_file in sorted(docs_dir.rglob("*.md")):
            relative_path = md_file.relative_to(source_dir)
            wiki_name = path_to_wiki_name(str(relative_path)) + ".md"
            yield md_file, wiki_name


def copy_images(source_dir: Path, dest_dir: Path) -> int:
    docs_dir = source_dir / "docs"
    images_dir = docs_dir / "images"
    if not images_dir.exists():
        return 0

    copied = 0
    for image in images_dir.rglob("*"):
        if image.is_dir():
            continue
        relative = image.relative_to(images_dir)
        target = dest_dir / "images" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image, target)
        copied += 1
    return copied


def prepare_wiki(source_dir: Path, dest_dir: Path, clean: bool) -> tuple[int, int]:
    if clean:
        clear_destination(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    pages = 0
    for src, name in collect_markdown_sources(source_dir):
        copy_markdown_file(src, dest_dir / name)
        pages += 1

    images = copy_images(source_dir, dest_dir)
    return pages, images


def display_name(stem: str) -> str:
    if stem == "Home":
        return "Home"
    return stem.replace("-", " ")


def _categorize_page(stem: str) -> str:
    """
    Assign a sidebar category based on common naming conventions.

    This avoids hardcoding specific filenames while keeping predictable
    sections for guides and project docs.
    """
    lower = stem.lower()

    guide_keywords = ("tutorial", "guide", "primer", "howto", "walkthrough")
    project_keywords = ("release", "changelog", "roadmap", "project", "architecture")

    if any(keyword in lower for keyword in guide_keywords):
        return "Guides"
    if any(keyword in lower for keyword in project_keywords):
        return "Project"
    return "Additional Pages"


def generate_sidebar(dest_dir: Path) -> str:
    pages = sorted(
        f.stem
        for f in dest_dir.glob("*.md")
        if f.name not in {"_Sidebar.md", "_Footer.md"}
    )

    lines = ["## Documentation", ""]

    if "Home" in pages:
        lines.append("- [Home](Home)")
    categorized: dict[str, list[str]] = {
        "Guides": [],
        "Project": [],
        "Additional Pages": [],
    }
    for page in pages:
        if page == "Home":
            continue
        category = _categorize_page(page)
        categorized.setdefault(category, []).append(page)

    def section(title: str, items: Iterable[str]) -> None:
        items = sorted(items)
        if not items:
            return
        lines.append("")
        lines.append(f"### {title}")
        for item in items:
            lines.append(f"- [{display_name(item)}]({item})")

    section("Guides", categorized.get("Guides", []))
    section("Project", categorized.get("Project", []))
    section("Additional Pages", categorized.get("Additional Pages", []))

    return "\n".join(lines) + "\n"


def generate_footer(repo_url: str, pages_url: str) -> str:
    lines = [
        "---",
        f"📦 [Repository]({repo_url}) |",
        f"📖 [Documentation]({pages_url}) |",
        f"🐛 [Issues]({repo_url}/issues) |",
        f"📜 [License]({repo_url}/blob/main/LICENSE)",
    ]
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate GitHub Wiki content from repository markdown files."
    )
    parser.add_argument(
        "--source",
        default=str(REPO_ROOT),
        help="Repository root containing README.md and docs/ (default: repo root).",
    )
    parser.add_argument(
        "--dest",
        default=str(DEFAULT_DEST),
        help="Destination directory for wiki content (default: build/wiki).",
    )
    parser.add_argument(
        "--repo-url",
        default="https://github.com/wallstop/MalbolgeGenerator",
        help="Repository URL for footer links.",
    )
    parser.add_argument(
        "--pages-url",
        default="https://wallstop.github.io/MalbolgeGenerator/",
        help="Documentation URL for footer links (GitHub Pages).",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleaning the destination directory before writing.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    source_dir = Path(args.source).resolve()
    dest_dir = Path(args.dest).resolve()

    if not source_dir.exists():
        raise SystemExit(f"Source directory does not exist: {source_dir}")

    pages, images = prepare_wiki(source_dir, dest_dir, clean=not args.no_clean)

    sidebar = generate_sidebar(dest_dir)
    (dest_dir / "_Sidebar.md").write_text(sidebar, encoding="utf-8")

    footer = generate_footer(args.repo_url, args.pages_url)
    (dest_dir / "_Footer.md").write_text(footer, encoding="utf-8")

    print(f"Generated wiki at {dest_dir} " f"(pages: {pages}, images: {images})")


if __name__ == "__main__":
    main()
