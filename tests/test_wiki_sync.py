from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.wiki.sync_wiki import (
    clear_destination,
    generate_sidebar,
    parse_args,
    path_to_wiki_name,
    prepare_wiki,
    transform_wiki_links,
)


class WikiSyncTests(unittest.TestCase):
    def create_source_tree(self) -> tuple[Path, Path]:
        src_dir = Path(tempfile.mkdtemp())
        docs_dir = src_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        (src_dir / "README.md").write_text(
            "Welcome to the project. See the [primer](docs/MALBOLGE_PRIMER.md) "
            "and [tutorial](docs/TUTORIAL.md#basics).",
            encoding="utf-8",
        )
        (docs_dir / "MALBOLGE_PRIMER.md").write_text("# Primer", encoding="utf-8")
        (docs_dir / "TUTORIAL.md").write_text(
            "![logo](images/logo.png)\n\nMore text.", encoding="utf-8"
        )

        images_dir = docs_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        (images_dir / "logo.png").write_bytes(b"image-bytes")

        dest_dir = Path(tempfile.mkdtemp())
        return src_dir, dest_dir

    def tearDown(self) -> None:
        # Clean up temp directories if a test created them
        for attr in ("src_dir", "dest_dir"):
            directory = getattr(self, attr, None)
            if directory and Path(directory).exists():
                shutil.rmtree(directory, ignore_errors=True)

    def test_path_to_wiki_name_normalizes_paths(self) -> None:
        cases = {
            "docs/TUTORIAL.md": "Tutorial",
            "./docs/deep/intro-guide.md": "Deep-Intro-Guide",
            "../README.md": "Home",
            "../../docs/advanced/guide.md": "Advanced-Guide",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(path_to_wiki_name(raw), expected)

    def test_transform_wiki_links_rewrites_internal_links(self) -> None:
        content = (
            "Refer to the [primer](docs/MALBOLGE_PRIMER.md) and "
            "external [site](https://example.com)."
        )
        transformed = transform_wiki_links(content)
        self.assertIn("[primer](Malbolge-Primer)", transformed)
        self.assertIn("[site](https://example.com)", transformed)

    def test_transform_wiki_links_normalizes_images(self) -> None:
        content = "![logo](../docs/images/logo.png)"
        transformed = transform_wiki_links(content)
        self.assertIn("![logo](images/logo.png)", transformed)

    def test_transform_wiki_links_ignores_mailto_and_tel_images(self) -> None:
        content = "![email](mailto:team@example.com) ![phone](tel:+123456)"
        transformed = transform_wiki_links(content)
        self.assertEqual(content, transformed)

    def test_prepare_wiki_copies_content_and_sidebar(self) -> None:
        self.src_dir, self.dest_dir = self.create_source_tree()
        pages, images = prepare_wiki(self.src_dir, self.dest_dir, clean=True)
        self.assertEqual(pages, 3)  # README + two docs
        self.assertEqual(images, 1)

        self.assertTrue((self.dest_dir / "Home.md").exists())
        self.assertTrue((self.dest_dir / "Malbolge-Primer.md").exists())
        self.assertTrue((self.dest_dir / "Tutorial.md").exists())
        self.assertTrue((self.dest_dir / "images" / "logo.png").exists())

        sidebar = generate_sidebar(self.dest_dir)
        self.assertIn("[Malbolge Primer](Malbolge-Primer)", sidebar)
        self.assertIn("[Tutorial](Tutorial)", sidebar)

    def test_generate_sidebar_categorizes_by_keyword(self) -> None:
        self.dest_dir = Path(tempfile.mkdtemp())
        for name in [
            "Home.md",
            "Tutorial.md",
            "Malbolge-Primer.md",
            "Release-Notes.md",
            "Guide-New-Topic.md",
            "Project-Roadmap.md",
            "Misc.md",
        ]:
            (self.dest_dir / name).write_text("# page", encoding="utf-8")

        sidebar = generate_sidebar(self.dest_dir)

        self.assertIn("### Guides", sidebar)
        self.assertIn("[Tutorial](Tutorial)", sidebar)
        self.assertIn("[Guide New Topic](Guide-New-Topic)", sidebar)

        self.assertIn("### Project", sidebar)
        self.assertIn("[Release Notes](Release-Notes)", sidebar)
        self.assertIn("[Project Roadmap](Project-Roadmap)", sidebar)

        self.assertIn("### Additional Pages", sidebar)
        self.assertIn("[Misc](Misc)", sidebar)

    def test_clear_destination_preserves_git_metadata(self) -> None:
        self.dest_dir = Path(tempfile.mkdtemp())
        (self.dest_dir / ".git").mkdir()
        (self.dest_dir / ".gitignore").write_text("*.tmp", encoding="utf-8")
        (self.dest_dir / ".gitattributes").write_text("* text=auto", encoding="utf-8")
        (self.dest_dir / "remove.me").write_text("junk", encoding="utf-8")

        clear_destination(self.dest_dir)

        self.assertTrue((self.dest_dir / ".git").exists())
        self.assertTrue((self.dest_dir / ".gitignore").exists())
        self.assertTrue((self.dest_dir / ".gitattributes").exists())
        self.assertFalse((self.dest_dir / "remove.me").exists())

    def test_parse_args_pages_url_default_has_trailing_slash(self) -> None:
        args = parse_args([])
        self.assertTrue(
            args.pages_url.endswith("/"),
            f"pages_url default must end with '/': {args.pages_url}",
        )
        self.assertIn("github.io", args.pages_url)
