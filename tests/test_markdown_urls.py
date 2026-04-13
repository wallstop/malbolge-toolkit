from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from scripts import check_markdown_urls


class ClientConnectorDNSError(Exception):
    pass


class MarkdownUrlChecksTests(unittest.TestCase):
    def test_is_transient_network_error_data_driven(self) -> None:
        cases = [
            (ClientConnectorDNSError("dns failure"), False),
            (RuntimeError("certificate verify failed"), True),
            (RuntimeError("timed out while connecting"), True),
            (RuntimeError("Name or service not known"), False),
            (RuntimeError("nodename nor servname provided"), False),
            (RuntimeError("404 Not Found"), False),
            (ValueError("invalid url"), False),
        ]

        for error, expected in cases:
            with self.subTest(error=repr(error)):
                self.assertEqual(
                    check_markdown_urls.is_transient_network_error(error), expected
                )

    def test_main_ignores_transient_errors_by_default(self) -> None:
        failures = [
            (
                "README.md",
                "https://example.com",
                RuntimeError("certificate verify failed"),
            )
        ]
        stderr = io.StringIO()
        with (
            patch.object(
                check_markdown_urls, "collect_targets", return_value=[Path(".")]
            ),
            patch.object(check_markdown_urls, "check_target", return_value=failures),
            redirect_stderr(stderr),
        ):
            exit_code = check_markdown_urls.main([])

        self.assertEqual(exit_code, 0)
        self.assertIn(
            "Transient Markdown link check failures detected",
            stderr.getvalue(),
        )

    def test_main_strict_network_fails_on_transient_errors(self) -> None:
        failures = [
            (
                "README.md",
                "https://example.com",
                RuntimeError("certificate verify failed"),
            )
        ]
        stderr = io.StringIO()
        with (
            patch.object(
                check_markdown_urls, "collect_targets", return_value=[Path(".")]
            ),
            patch.object(check_markdown_urls, "check_target", return_value=failures),
            redirect_stderr(stderr),
        ):
            exit_code = check_markdown_urls.main(["--strict-network"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Broken Markdown links detected:", stderr.getvalue())

    def test_main_fails_on_unknown_host_errors_by_default(self) -> None:
        failures = [
            (
                "README.md",
                "https://example.com",
                ClientConnectorDNSError("No address associated with hostname"),
            ),
        ]
        stderr = io.StringIO()
        with (
            patch.object(
                check_markdown_urls, "collect_targets", return_value=[Path(".")]
            ),
            patch.object(check_markdown_urls, "check_target", return_value=failures),
            redirect_stderr(stderr),
        ):
            exit_code = check_markdown_urls.main([])

        self.assertEqual(exit_code, 1)
        self.assertIn("Broken Markdown links detected:", stderr.getvalue())

    def test_main_fails_on_non_transient_errors(self) -> None:
        failures = [
            ("README.md", "https://example.com", RuntimeError("404 Not Found")),
        ]
        stderr = io.StringIO()
        with (
            patch.object(
                check_markdown_urls, "collect_targets", return_value=[Path(".")]
            ),
            patch.object(check_markdown_urls, "check_target", return_value=failures),
            redirect_stderr(stderr),
        ):
            exit_code = check_markdown_urls.main([])

        self.assertEqual(exit_code, 1)
        self.assertIn("Broken Markdown links detected:", stderr.getvalue())
