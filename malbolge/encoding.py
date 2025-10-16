# SPDX-License-Identifier: MIT
"""Translation helpers between ASCII and Malbolge instruction sets."""

from __future__ import annotations

import functools
from collections.abc import Iterable

NORMAL_TRANSLATE = (
    "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z'"
    ";FNQuY]szf$!BS/|t:Pn6^Ha"
)
ENCRYPTION_TRANSLATE = (
    "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVa"
    "c`uY*MK'X~xDl}REokN:#?G\"i@"
)
VALID_INSTRUCTIONS = "i</*jpov"
MAX_PROGRAM_LENGTH = 59049


class InvalidProgramError(ValueError):
    """Raised when a program cannot be normalized."""


def normalize(instruction_list: Iterable[str]) -> list[str]:
    """
    Convert ASCII characters to Malbolge opcodes.

    Only opcodes in VALID_INSTRUCTIONS are preserved; others are discarded
    to remain compatible with legacy behaviour.
    """
    instruction_list = list(instruction_list)
    if len(instruction_list) > MAX_PROGRAM_LENGTH:
        raise InvalidProgramError("Program exceeds Malbolge maximum length (59049).")

    return_string = ""
    for index, char in enumerate(instruction_list):
        translated = NORMAL_TRANSLATE[((ord(char) + index - 33) % 94)]
        if translated in VALID_INSTRUCTIONS:
            return_string += translated

    return list(return_string)


@functools.cache
def _opcode_offset(opcode: str, index: int) -> int:
    return (NORMAL_TRANSLATE.index(opcode) - index) % 94


def reverse_normalize(
    instruction_list: Iterable[str],
    *,
    start_index: int = 0,
) -> list[str]:
    """Encode Malbolge opcodes back into printable ASCII characters."""
    instruction_list = list(instruction_list)
    total_length = start_index + len(instruction_list)
    if total_length > MAX_PROGRAM_LENGTH:
        raise InvalidProgramError("Program exceeds Malbolge maximum length (59049).")

    return_string = ""
    for offset, char in enumerate(instruction_list):
        if char not in VALID_INSTRUCTIONS:
            raise InvalidProgramError("Invalid opcode encountered during decoding.")
        index = start_index + offset
        translated = chr(_opcode_offset(char, index) + 33)
        return_string += translated

    return list(return_string)
