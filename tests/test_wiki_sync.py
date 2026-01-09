from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.wiki.sync_wiki import (
    generate_sidebar,
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
        self.assertEqual(path_to_wiki_name("docs/TUTORIAL.md"), "Tutorial")
        self.assertEqual(
            path_to_wiki_name("./docs/deep/intro-guide.md"), "Deep-Intro-Guide"
        )
        self.assertEqual(path_to_wiki_name("../README.md"), "Home")

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
