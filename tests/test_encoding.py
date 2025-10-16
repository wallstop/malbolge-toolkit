# SPDX-License-Identifier: MIT

import unittest

from malbolge.encoding import (
    MAX_PROGRAM_LENGTH,
    InvalidProgramError,
    normalize,
    reverse_normalize,
)


class EncodingTests(unittest.TestCase):
    def test_round_trip_opcodes(self) -> None:
        opcodes = list("i<ov")
        ascii_chars = reverse_normalize(opcodes)
        self.assertEqual(normalize(ascii_chars), opcodes)

    def test_round_trip_with_offset(self) -> None:
        prefix = list("i<")
        suffix = list("p")
        ascii_prefix = reverse_normalize(prefix)
        ascii_suffix = reverse_normalize(suffix, start_index=len(prefix))
        combined = ascii_prefix + ascii_suffix
        self.assertEqual(normalize(combined), prefix + suffix)

    def test_normalize_max_length_guard(self) -> None:
        with self.assertRaises(InvalidProgramError):
            normalize(["!"] * (MAX_PROGRAM_LENGTH + 1))

    def test_reverse_normalize_invalid_opcode(self) -> None:
        with self.assertRaises(InvalidProgramError):
            reverse_normalize(["x"])

    def test_reverse_normalize_max_length_guard(self) -> None:
        with self.assertRaises(InvalidProgramError):
            reverse_normalize(["i"] * (MAX_PROGRAM_LENGTH + 1))


if __name__ == "__main__":
    unittest.main()
