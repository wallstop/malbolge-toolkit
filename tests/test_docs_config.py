from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MKDOCS_PATH = REPO_ROOT / "mkdocs.yml"
TRAILING_SLASH_JS = REPO_ROOT / "docs" / "assets" / "trailing-slash.js"


def _load_mkdocs_lines() -> list[str]:
    return MKDOCS_PATH.read_text(encoding="utf-8").splitlines()


class DocsConfigTests(unittest.TestCase):
    def test_site_url_has_trailing_slash(self) -> None:
        """
        Prevent regressions where a missing trailing slash strips the repo path
        on GitHub Pages, breaking relative links like Beginner Resources.
        """
        lines = _load_mkdocs_lines()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("site_url:"):
                value = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                self.assertTrue(
                    value.endswith("/"),
                    "mkdocs site_url must end with '/' for correct base resolution",
                )
                return
        self.fail("mkdocs.yml missing site_url setting")

    def test_trailing_slash_guard_is_included(self) -> None:
        """
        Ensure the JS guard that normalizes trailing slashes is bundled into the site.
        """
        self.assertTrue(
            TRAILING_SLASH_JS.exists(), "trailing-slash guard asset is missing"
        )

        lines = _load_mkdocs_lines()
        in_extra_js = False
        found = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("extra_javascript:"):
                in_extra_js = True
                continue
            if in_extra_js:
                if stripped.startswith("-"):
                    asset = stripped.lstrip("-").strip()
                    if asset == "assets/trailing-slash.js":
                        found = True
                        break
                elif stripped and not stripped.startswith("#"):
                    # End of extra_javascript block
                    break
        self.assertTrue(
            found,
            "mkdocs.yml must include assets/trailing-slash.js in extra_javascript",
        )
