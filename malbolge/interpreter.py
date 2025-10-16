# SPDX-License-Identifier: MIT
"""
High-performance Malbolge interpreter.

The interpreter operates on an explicit machine instance instead of globals
and avoids unnecessary allocations in tight loops.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from .encoding import (
    ENCRYPTION_TRANSLATE,
    NORMAL_TRANSLATE,
    VALID_INSTRUCTIONS,
    reverse_normalize,
)
from .utils import MAX_ADDRESS_SPACE, crazy_operation, ternary_rotate

CYCLE_DETECTION_LIMIT = 100_000


class MalbolgeRuntimeError(RuntimeError):
    """Raised when a program violates machine constraints."""


class InvalidOpcodeError(MalbolgeRuntimeError):
    """Raised when an opcode outside the Malbolge instruction set is encountered."""


class InputUnderflowError(MalbolgeRuntimeError):
    """Raised when a `/` instruction executes without available input."""


class StepLimitExceededError(MalbolgeRuntimeError):
    """Raised when execution surpasses the configured maximum number of steps."""


class MemoryLimitExceededError(MalbolgeRuntimeError):
    """Raised when the interpreter would access memory beyond the allowed limit."""


@dataclass(slots=True)
class MalbolgeMachine:
    tape: list[int] = field(default_factory=list)
    a: int = 0
    c: int = 0
    d: int = 0
    halted: bool = False

    def reset(self) -> None:
        self.a = 0
        self.c = 0
        self.d = 0
        self.halted = False

    def load_tape(self, ascii_tape: Sequence[str]) -> None:
        self.tape = [ord(ch) for ch in ascii_tape]
        if len(self.tape) > MAX_ADDRESS_SPACE:
            raise MalbolgeRuntimeError("Program exceeds maximum addressable tape size.")
        self.reset()

    def copy(self) -> MalbolgeMachine:
        return MalbolgeMachine(self.tape.copy(), self.a, self.c, self.d, self.halted)

    def encrypt_current_cell(self) -> None:
        cell_value = self.tape[self.c]
        if 33 <= cell_value <= 126:
            self.tape[self.c] = ord(ENCRYPTION_TRANSLATE[cell_value - 33])


@dataclass(slots=True)
class HaltMetadata:
    last_instruction: str | None = None
    last_jump_target: int | None = None
    cycle_detected: bool = False


@dataclass(slots=True)
class ExecutionResult:
    output: str
    halted: bool
    steps: int
    halt_reason: str
    machine: MalbolgeMachine | None = None
    halt_metadata: HaltMetadata = field(default_factory=HaltMetadata)
    memory_expansions: int = 0
    peak_memory_cells: int = 0


class MalbolgeInterpreter:
    """
    Execute normalized Malbolge opcodes and capture output.

    A single interpreter instance can run multiple programs sequentially.
    """

    def __init__(
        self,
        *,
        allow_memory_expansion: bool = True,
        memory_limit: int | None = MAX_ADDRESS_SPACE,
    ) -> None:
        self.machine = MalbolgeMachine()
        self._allow_memory_expansion = allow_memory_expansion
        self._memory_limit = (
            memory_limit if memory_limit is not None else MAX_ADDRESS_SPACE
        )
        self._program_length = 0
        self._memory_expansions = 0
        self._peak_tape_length = 0

    def load_program(self, opcodes: Sequence[str]) -> None:
        if len(opcodes) == 0:
            raise InvalidOpcodeError("Opcode sequence is empty.")
        if any(opcode not in VALID_INSTRUCTIONS for opcode in opcodes):
            raise InvalidOpcodeError("Encountered invalid opcode during load.")

        ascii_tape = reverse_normalize(opcodes)
        self.machine.load_tape(ascii_tape)
        self._program_length = len(opcodes)
        self._reset_diagnostics()

    def _reset_diagnostics(self) -> None:
        self._memory_expansions = 0
        self._peak_tape_length = len(self.machine.tape)

    def execute(
        self,
        opcodes: Sequence[str],
        *,
        input_buffer: Iterable[str] | None = None,
        max_steps: int | None = None,
        capture_machine: bool = False,
    ) -> ExecutionResult:
        self.load_program(opcodes)
        return self.resume_execution(
            input_buffer=input_buffer,
            max_steps=max_steps,
            capture_machine=capture_machine,
        )

    def run(
        self,
        opcodes: Sequence[str],
        *,
        input_buffer: Iterable[str] | None = None,
        max_steps: int | None = None,
    ) -> str:
        result = self.execute(
            opcodes,
            input_buffer=input_buffer,
            max_steps=max_steps,
            capture_machine=False,
        )
        return result.output

    def resume(
        self,
        *,
        input_buffer: Iterable[str] | None = None,
        max_steps: int | None = None,
    ) -> str:
        result = self.resume_execution(
            input_buffer=input_buffer,
            max_steps=max_steps,
            capture_machine=False,
        )
        return result.output

    def resume_execution(
        self,
        *,
        input_buffer: Iterable[str] | None = None,
        max_steps: int | None = None,
        capture_machine: bool = False,
    ) -> ExecutionResult:
        self._reset_diagnostics()
        return self._execute_loaded(
            input_buffer=input_buffer,
            max_steps=max_steps,
            capture_machine=capture_machine,
        )

    def execute_from_snapshot(
        self,
        snapshot: MalbolgeMachine,
        suffix_opcodes: Sequence[str],
        *,
        input_buffer: Iterable[str] | None = None,
        max_steps: int | None = None,
        capture_machine: bool = False,
    ) -> ExecutionResult:
        machine = snapshot.copy()
        prefix_length = len(machine.tape)
        if suffix_opcodes:
            ascii_suffix = reverse_normalize(suffix_opcodes, start_index=prefix_length)
            machine.tape.extend(ord(ch) for ch in ascii_suffix)
        self.machine = machine
        self._program_length = prefix_length + len(suffix_opcodes)
        self._reset_diagnostics()
        return self._execute_loaded(
            input_buffer=input_buffer,
            max_steps=max_steps,
            capture_machine=capture_machine,
        )

    def _execute_loaded(
        self,
        *,
        input_buffer: Iterable[str] | None,
        max_steps: int | None,
        capture_machine: bool,
    ) -> ExecutionResult:
        machine = self.machine
        machine.halted = False
        output_chars: list[str] = []
        input_iter = iter(input_buffer or [])

        steps_remaining = max_steps
        steps_executed = 0
        halt_reason: str | None = None
        metadata = HaltMetadata()
        seen_states: set[tuple[int, int, int, int]] = set()

        while not machine.halted:
            if steps_remaining is not None:
                if steps_remaining <= 0:
                    raise StepLimitExceededError("Maximum step count exceeded.")
                steps_remaining -= 1
            if machine.c >= self._program_length:
                machine.halted = True
                halt_reason = "program_end"
                break

            self._ensure_capacity(machine.c)
            cell_value = machine.tape[machine.c]
            if len(seen_states) < CYCLE_DETECTION_LIMIT:
                state_key = (machine.c, cell_value, machine.a, machine.d)
                if state_key in seen_states:
                    metadata.cycle_detected = True
                else:
                    seen_states.add(state_key)
            instruction = self._instruction_at(machine.c)
            metadata.last_instruction = instruction
            metadata.last_jump_target = None

            if instruction == "i":
                self._ensure_capacity(machine.d)
                jump_target = machine.tape[machine.d]
                machine.c = jump_target
                metadata.last_jump_target = jump_target
            elif instruction == "<":
                output_chars.append(chr(machine.a % 256))
            elif instruction == "/":
                try:
                    next_input = next(input_iter)
                except StopIteration as exc:
                    raise InputUnderflowError(
                        "Input instruction encountered with empty buffer."
                    ) from exc
                if not next_input:
                    raise InputUnderflowError("Input buffer supplied an empty string.")
                machine.a = ord(next_input[0])
            elif instruction == "*":
                self._ensure_capacity(machine.d)
                machine.a = ternary_rotate(machine.tape[machine.d])
                machine.tape[machine.d] = machine.a
            elif instruction == "j":
                self._ensure_capacity(machine.d)
                jump_target = machine.tape[machine.d]
                machine.d = jump_target
                metadata.last_jump_target = jump_target
            elif instruction == "p":
                self._ensure_capacity(machine.d)
                machine.a = crazy_operation(machine.a, machine.tape[machine.d])
                machine.tape[machine.d] = machine.a
            elif instruction == "o":
                # NOP / placeholder used by generator to advance D.
                pass
            elif instruction == "v":
                machine.halted = True
                halt_reason = "halt_opcode"
            else:
                raise MalbolgeRuntimeError(f"Unsupported opcode '{instruction}'.")

            machine.encrypt_current_cell()

            machine.c += 1
            machine.d += 1
            steps_executed += 1

        if halt_reason is None:
            halt_reason = "unknown"
        snapshot = machine.copy() if capture_machine else None
        return ExecutionResult(
            output="".join(output_chars),
            halted=machine.halted,
            steps=steps_executed,
            halt_reason=halt_reason,
            machine=snapshot,
            halt_metadata=metadata,
            memory_expansions=self._memory_expansions,
            peak_memory_cells=self._peak_tape_length,
        )

    def _ensure_capacity(self, index: int) -> None:
        machine = self.machine
        initial_length = len(machine.tape)
        if index < initial_length:
            return

        if not self._allow_memory_expansion:
            raise MemoryLimitExceededError(
                "Memory expansion is disabled for this interpreter."
            )

        if index >= self._memory_limit:
            raise MemoryLimitExceededError("Memory limit exceeded.")

        limit = min(self._memory_limit, MAX_ADDRESS_SPACE)
        while len(machine.tape) <= index:
            if len(machine.tape) >= 2:
                next_value = crazy_operation(machine.tape[-2], machine.tape[-1])
            elif len(machine.tape) == 1:
                next_value = crazy_operation(machine.tape[0], machine.tape[0])
            else:
                next_value = 0

            machine.tape.append(next_value)
            if len(machine.tape) >= limit:
                break

        if index >= len(machine.tape):
            raise MemoryLimitExceededError(
                "Unable to expand memory to requested index."
            )
        appended = len(machine.tape) - initial_length
        if appended > 0:
            self._memory_expansions += appended
            if len(machine.tape) > self._peak_tape_length:
                self._peak_tape_length = len(machine.tape)

    def _instruction_at(self, index: int) -> str:
        value = self.machine.tape[index]
        return NORMAL_TRANSLATE[(value - 33 + index) % 94]
