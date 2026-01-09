from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MKDOCS_PATH = REPO_ROOT / "mkdocs.yml"
TRAILING_SLASH_JS = REPO_ROOT / "docs" / "assets" / "trailing-slash.js"


def _load_mkdocs_lines() -> list[str]:
    return MKDOCS_PATH.read_text(encoding="utf-8").splitlines()


def _extract_setting(lines: list[str], key: str) -> str | None:
    """
    Lightweight parser for simple top-level key/value settings in mkdocs.yml.

    This intentionally avoids a YAML dependency while providing better
    diagnostics than raw string searching.
    """
    prefix = f"{key}:"
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not stripped.startswith(prefix):
            continue
        value = stripped.split(":", 1)[1].split("#", 1)[0].strip()
        return value.strip('"').strip("'")
    return None


class DocsConfigTests(unittest.TestCase):
    def test_site_url_configuration(self) -> None:
        """
        Prevent regressions where a missing trailing slash strips the repo path
        on GitHub Pages, breaking relative links like Beginner Resources.
        Also guard against accidentally pointing site_url at the repository
        view instead of the published GitHub Pages site.
        """
        lines = _load_mkdocs_lines()
        site_url = _extract_setting(lines, "site_url")
        self.assertIsNotNone(
            site_url, f"mkdocs.yml missing site_url setting (searched {MKDOCS_PATH})"
        )

        requirements = [
            (
                "trailing_slash",
                lambda value: value.endswith("/"),
                "mkdocs site_url must end with '/' for correct base resolution",
            ),
            (
                "github_pages_scope",
                lambda value: "github.io" in value and "/MalbolgeGenerator/" in value,
                "site_url should target the published GitHub Pages path "
                "to preserve the repository scope",
            ),
        ]
        assert site_url is not None  # Narrow type for mypy
        for name, predicate, message in requirements:
            with self.subTest(check=name, site_url=site_url):
                self.assertTrue(predicate(site_url), f"{message}: {site_url}")

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
        seen_assets: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("extra_javascript:"):
                in_extra_js = True
                continue
            if in_extra_js:
                if stripped.startswith("-"):
                    asset = stripped.lstrip("-").strip()
                    seen_assets.append(asset)
                    if asset == "assets/trailing-slash.js":
                        found = True
                        break
                elif stripped and not stripped.startswith("#"):
                    # End of extra_javascript block
                    break
        self.assertTrue(
            found,
            "mkdocs.yml must include assets/trailing-slash.js in extra_javascript "
            f"(found: {seen_assets or 'none'})",
        )
