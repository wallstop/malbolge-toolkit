# SPDX-License-Identifier: MIT

import io
import tempfile
import unittest
from collections.abc import Sequence
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from malbolge.cli.main import main


class CLITests(unittest.TestCase):
    def invoke(self, argv: Sequence[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(list(argv))
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_run_command_with_opcodes(self) -> None:
        code, out, err = self.invoke(["run", "--opcodes", "v"])
        self.assertEqual(code, 0)
        self.assertIn("halt_reason=halt_opcode", out)
        self.assertIn("steps=", out)
        self.assertIn("halt_instruction=v", out)
        self.assertIn("memory_expansions=", out)
        self.assertIn("peak_tape_cells=", out)
        self.assertIn("tape_length=", out)
        self.assertEqual(err, "")

    def test_run_command_reports_errors(self) -> None:
        code, out, err = self.invoke(["run", "--opcodes", "z"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("[error]", err)

    def test_generate_command_outputs_stats(self) -> None:
        code, out, err = self.invoke(["generate", "--text", "Hi", "--seed", "123"])
        self.assertEqual(code, 0)
        self.assertIn("evaluations", out)
        self.assertIn("cache_hits", out)
        self.assertIn("pruned", out)
        self.assertIn("repeated_state_pruned", out)
        self.assertIn("duration_ns", out)
        self.assertIn("trace_length", out)
        self.assertEqual(err, "")

    def test_run_command_accepts_ascii_file(self) -> None:
        program = "'\""
        with tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(program)
            file_path = Path(temp_file.name)

        try:
            code, out, err = self.invoke(["run", "--ascii-file", str(file_path)])
        finally:
            file_path.unlink(missing_ok=True)

        self.assertEqual(code, 0)
        self.assertIn("halt_reason=", out)
        self.assertIn("memory_expansions=", out)
        self.assertEqual(err, "")

    def test_bench_command_runs_interpreter_benchmarks(self) -> None:
        code, out, err = self.invoke(["bench", "--module", "interpreter"])
        self.assertEqual(code, 0)
        self.assertIn("Interpreter Benchmarks", out)
        self.assertEqual(err, "")

    def test_generate_command_with_trace(self) -> None:
        code, out, err = self.invoke(
            ["generate", "--text", "Hi", "--seed", "42", "--trace"]
        )
        self.assertEqual(code, 0)
        self.assertIn("trace=", out)
        self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()
