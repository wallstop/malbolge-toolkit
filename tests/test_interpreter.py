# SPDX-License-Identifier: MIT

import unittest
from types import MethodType
from typing import Any, cast

from malbolge.interpreter import (
    ExecutionResult,
    InputUnderflowError,
    InvalidOpcodeError,
    MalbolgeInterpreter,
    MalbolgeMachine,
    MemoryLimitExceededError,
    StepLimitExceededError,
)


class InterpreterTests(unittest.TestCase):
    def test_execute_returns_structured_result(self) -> None:
        interpreter = MalbolgeInterpreter()
        result = interpreter.execute("v", capture_machine=True)

        self.assertIsInstance(result, ExecutionResult)
        self.assertEqual(result.output, "")
        self.assertTrue(result.halted)
        self.assertEqual(result.steps, 1)
        self.assertEqual(result.halt_reason, "halt_opcode")
        self.assertIsNotNone(result.machine)
        machine = cast(MalbolgeMachine, result.machine)
        self.assertEqual(len(machine.tape), 1)
        self.assertEqual(result.halt_metadata.last_instruction, "v")
        self.assertIsNone(result.halt_metadata.last_jump_target)
        self.assertFalse(result.halt_metadata.cycle_detected)
        self.assertEqual(result.memory_expansions, 0)
        self.assertGreaterEqual(result.peak_memory_cells, 1)

    def test_input_instruction_consumes_buffer(self) -> None:
        interpreter = MalbolgeInterpreter()
        result = interpreter.execute("/<v", input_buffer=["A"])
        self.assertEqual(result.output, "A")

    def test_input_underflow_raises(self) -> None:
        interpreter = MalbolgeInterpreter()
        with self.assertRaises(InputUnderflowError):
            interpreter.execute("/v")

    def test_execute_from_snapshot_extends_program(self) -> None:
        interpreter = MalbolgeInterpreter()
        base = interpreter.execute("ov", capture_machine=True)
        self.assertIsNotNone(base.machine)
        base_machine = cast(MalbolgeMachine, base.machine)

        extended = interpreter.execute_from_snapshot(
            base_machine,
            "v",
            capture_machine=True,
        )
        self.assertTrue(extended.halted)
        self.assertIsNotNone(extended.machine)
        extended_machine = cast(MalbolgeMachine, extended.machine)
        self.assertEqual(len(extended_machine.tape), 3)
        self.assertEqual(extended.steps, 1)
        self.assertEqual(extended.halt_reason, "halt_opcode")
        self.assertEqual(extended.halt_metadata.last_instruction, "v")
        self.assertEqual(extended.memory_expansions, 0)

    def test_invalid_opcode_raises(self) -> None:
        interpreter = MalbolgeInterpreter()
        with self.assertRaises(InvalidOpcodeError):
            interpreter.execute("z")

    def test_step_limit_exceeded(self) -> None:
        interpreter = MalbolgeInterpreter()
        with self.assertRaises(StepLimitExceededError):
            interpreter.execute("v", max_steps=0)

    def test_memory_limit_enforced_when_disabled(self) -> None:
        interpreter = MalbolgeInterpreter(allow_memory_expansion=False)
        base = MalbolgeInterpreter().execute("ov", capture_machine=True)
        state = base.machine
        self.assertIsNotNone(state)
        machine_state = cast(MalbolgeMachine, state)
        machine_state.c = len(machine_state.tape)  # point at appended instruction slot
        machine_state.d = len(machine_state.tape) + 5  # force out-of-bounds data access
        machine_state.halted = False
        with self.assertRaises(MemoryLimitExceededError):
            interpreter.execute_from_snapshot(machine_state, "p")

    def test_jump_metadata_records_last_target(self) -> None:
        interpreter = MalbolgeInterpreter()
        interpreter.machine = MalbolgeMachine(tape=[0, 0])
        interpreter._program_length = 2
        interpreter._reset_diagnostics()

        instruction_map = {0: "i", 1: "v"}

        def fake_instruction(self: MalbolgeInterpreter, index: int) -> str:
            return instruction_map.get(index, "v")

        cast(Any, interpreter)._instruction_at = MethodType(
            fake_instruction, interpreter
        )
        result = interpreter._execute_loaded(
            input_buffer=None, max_steps=None, capture_machine=False
        )
        self.assertEqual(result.halt_metadata.last_instruction, "v")
        self.assertEqual(result.halt_metadata.last_jump_target, 0)
        self.assertFalse(result.halt_metadata.cycle_detected)

    def test_memory_expansion_counter(self) -> None:
        interpreter = MalbolgeInterpreter()
        interpreter.machine = MalbolgeMachine(tape=[0])
        interpreter._program_length = 6
        interpreter._reset_diagnostics()

        def fake_instruction(self: MalbolgeInterpreter, index: int) -> str:
            return "o" if index < 5 else "v"

        cast(Any, interpreter)._instruction_at = MethodType(
            fake_instruction, interpreter
        )
        result = interpreter._execute_loaded(
            input_buffer=None, max_steps=None, capture_machine=False
        )
        self.assertGreater(result.memory_expansions, 0)
        self.assertGreaterEqual(result.peak_memory_cells, 2)


if __name__ == "__main__":
    unittest.main()
