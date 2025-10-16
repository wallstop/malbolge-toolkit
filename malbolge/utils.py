# SPDX-License-Identifier: MIT
"""Utility functions that implement Malbolge arithmetic primitives."""

from __future__ import annotations

from collections.abc import Sequence

MAX_ADDRESS_SPACE = 59049
TERNARY_DIGITS = 10
POWERS_OF_THREE: tuple[int, ...] = tuple(3**i for i in range(TERNARY_DIGITS))
MAX_TERNARY_POWER: int = POWERS_OF_THREE[-1]
_CRAZY_TABLE: tuple[int, ...] = (1, 1, 2, 0, 0, 2, 0, 2, 1)


def convert_to_base3(value: int, digits: int = TERNARY_DIGITS) -> list[int]:
    """Return the ternary representation (least significant digit first)."""
    if value < 0:
        raise ValueError("Malbolge numbers must be non-negative.")

    result: list[int] = [0] * digits
    current = value
    idx = 0
    while current and idx < digits:
        current, remainder = divmod(current, 3)
        result[idx] = remainder
        idx += 1

    return result


def convert_to_base10(values: Sequence[int]) -> int:
    """Convert a sequence of ternary digits (LSB first) back to base 10."""
    total = 0
    for index, digit in enumerate(values):
        total += digit * POWERS_OF_THREE[index]
    return total


def ternary_rotate(value: int) -> int:
    """Rotate the ternary representation left by one position."""
    least_significant = value % 3
    return (value // 3) + (least_significant * MAX_TERNARY_POWER)


def crazy_operation(first: int, second: int) -> int:
    """
    Execute the Malbolge 'crazy' operation on two values.

    The transformation is defined digit-wise using Malbolge's custom truth table.
    """
    total = 0
    power = 1
    local_first = first
    local_second = second
    for _ in range(TERNARY_DIGITS):
        total += _CRAZY_TABLE[(local_first % 3) * 3 + (local_second % 3)] * power
        local_first //= 3
        local_second //= 3
        power *= 3
    return total
