# SPDX-License-Identifier: MIT

import unittest

from malbolge.interpreter import (
    ExecutionResult,
    InvalidOpcodeError,
    InputUnderflowError,
    MalbolgeInterpreter,
    MalbolgeRuntimeError,
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
        self.assertEqual(len(result.machine.tape), 1)

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

        extended = interpreter.execute_from_snapshot(
            base.machine,
            "v",
            capture_machine=True,
        )
        self.assertTrue(extended.halted)
        self.assertEqual(len(extended.machine.tape), 3)
        self.assertEqual(extended.steps, 1)
        self.assertEqual(extended.halt_reason, "halt_opcode")

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
        state.c = len(state.tape)  # point at appended instruction slot
        state.d = len(state.tape) + 5  # force out-of-bounds data access
        state.halted = False
        with self.assertRaises(MemoryLimitExceededError):
            interpreter.execute_from_snapshot(state, "p")


if __name__ == "__main__":
    unittest.main()
