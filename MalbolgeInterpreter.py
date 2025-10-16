# SPDX-License-Identifier: MIT
"""
Compatibility layer exposing legacy entry points for the Malbolge toolkit.

New code should prefer importing from the `malbolge` package directly.
"""

from __future__ import annotations

from typing import Sequence

from malbolge.encoding import normalize, reverse_normalize
from malbolge.generator import GenerationConfig, ProgramGenerator
from malbolge.interpreter import (
    InvalidOpcodeError,
    InputUnderflowError,
    MalbolgeInterpreter,
    MalbolgeRuntimeError,
    MemoryLimitExceededError,
    StepLimitExceededError,
)
from malbolge.utils import (
    convert_to_base10,
    convert_to_base3,
    crazy_operation,
    ternary_rotate,
)

__all__ = [
    "normalize",
    "reverse_normalize",
    "convert_to_base3",
    "convert_to_base10",
    "crazy_operation",
    "ternary_rotate",
    "interpret",
    "feed_instructions",
    "feedInstructions",
    "print_malbolge_program",
    "printMalbolgeProgram",
    "find_string",
    "findString",
    "InvalidOpcodeError",
    "InputUnderflowError",
    "MemoryLimitExceededError",
    "StepLimitExceededError",
    "MalbolgeRuntimeError",
]

_DEFAULT_INTERPRETER = MalbolgeInterpreter()
_DEFAULT_GENERATOR = ProgramGenerator(_DEFAULT_INTERPRETER)


def interpret(opcodes: Sequence[str]) -> str:
    """Execute normalized Malbolge opcodes and return their output."""
    return _DEFAULT_INTERPRETER.run(opcodes)


def feed_instructions(ascii_program: Sequence[str]) -> str:
    """Normalize an ASCII Malbolge program and interpret it."""
    return interpret(normalize(ascii_program))


def print_malbolge_program(opcodes: Sequence[str]) -> None:
    """Print the ASCII representation of Malbolge opcodes."""
    print("".join(reverse_normalize(opcodes)))


def find_string(
    target: str,
    *,
    config: GenerationConfig | None = None,
    show_progress: bool = True,
) -> str:
    """
    Generate a Malbolge program that prints `target`.

    Returns the opcode sequence so callers can feed it directly to `interpret`.
    """
    result = _DEFAULT_GENERATOR.generate_for_string(target, config=config)
    if show_progress:
        print(target)
        print(result.malbolge_program)
    return result.opcodes


# Backwards-compatible camelCase alias.
def feedInstructions(ascii_program: Sequence[str]) -> str:
    return feed_instructions(ascii_program)


def printMalbolgeProgram(opcodes: Sequence[str]) -> None:
    print_malbolge_program(opcodes)


def findString(
    target: str, config: GenerationConfig | None = None, show_progress: bool = True
) -> str:
    return find_string(target, config=config, show_progress=show_progress)
