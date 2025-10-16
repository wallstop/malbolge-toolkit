# SPDX-License-Identifier: MIT
"""
Public package interface for Malbolge tools.

This module intentionally exposes only stable entry points while the internal
modules remain free to evolve. During the migration period we re-export legacy
helpers so existing imports keep working.
"""

from .encoding import (
    ENCRYPTION_TRANSLATE,
    NORMAL_TRANSLATE,
    VALID_INSTRUCTIONS,
    normalize,
    reverse_normalize,
)
from .generator import GenerationConfig, GenerationResult, ProgramGenerator
from .interpreter import (
    ExecutionResult,
    HaltMetadata,
    InputUnderflowError,
    InvalidOpcodeError,
    MalbolgeInterpreter,
    MalbolgeMachine,
    MalbolgeRuntimeError,
    MemoryLimitExceededError,
    StepLimitExceededError,
)
from .utils import (
    MAX_ADDRESS_SPACE,
    POWERS_OF_THREE,
    TERNARY_DIGITS,
    convert_to_base3,
    convert_to_base10,
    crazy_operation,
    ternary_rotate,
)

__all__ = [
    "NORMAL_TRANSLATE",
    "ENCRYPTION_TRANSLATE",
    "VALID_INSTRUCTIONS",
    "normalize",
    "reverse_normalize",
    "GenerationConfig",
    "GenerationResult",
    "ProgramGenerator",
    "ExecutionResult",
    "HaltMetadata",
    "InvalidOpcodeError",
    "InputUnderflowError",
    "MalbolgeInterpreter",
    "MalbolgeMachine",
    "MalbolgeRuntimeError",
    "MemoryLimitExceededError",
    "StepLimitExceededError",
    "MAX_ADDRESS_SPACE",
    "TERNARY_DIGITS",
    "POWERS_OF_THREE",
    "convert_to_base3",
    "convert_to_base10",
    "ternary_rotate",
    "crazy_operation",
]
