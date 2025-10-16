# SPDX-License-Identifier: MIT

import threading
import unittest
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
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
        self.assertFalse(result.halt_metadata.cycle_tracking_limited)
        self.assertIsNone(result.halt_metadata.cycle_repeat_length)
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
        result = interpreter.resume_execution(
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

    def test_cycle_detection_limit_flags(self) -> None:
        interpreter = MalbolgeInterpreter(cycle_detection_limit=0)
        result = interpreter.execute("v", capture_machine=True)
        self.assertTrue(result.halt_metadata.cycle_tracking_limited)
        self.assertFalse(result.halt_metadata.cycle_detected)
        self.assertIsNone(result.halt_metadata.cycle_repeat_length)

    def test_resume_after_step_limit(self) -> None:
        interpreter = MalbolgeInterpreter()
        with self.assertRaises(StepLimitExceededError):
            interpreter.execute("ov", max_steps=1)
        resume_output = interpreter.resume()
        self.assertEqual(resume_output, "")
        self.assertTrue(interpreter.machine.halted)

    def test_resume_after_step_limit_with_output(self) -> None:
        interpreter = MalbolgeInterpreter()
        with self.assertRaises(StepLimitExceededError):
            interpreter.execute("/<v", input_buffer=["Z"], max_steps=1)

        result = interpreter.resume_execution(capture_machine=True)
        self.assertEqual(result.output, "Z")
        self.assertTrue(result.halted)
        self.assertEqual(result.halt_reason, "halt_opcode")
        self.assertEqual(result.steps, 2)
        self.assertIsNotNone(result.machine)

    def test_cycle_repeat_length_reported(self) -> None:
        interpreter = MalbolgeInterpreter(cycle_detection_limit=5)
        machine = MalbolgeMachine(tape=[33, 33, 33])
        interpreter.machine = machine
        interpreter._program_length = 3
        interpreter._reset_diagnostics()

        instruction_iter = iter(["o", "o", "v"])

        def fake_instruction(self: MalbolgeInterpreter, index: int) -> str:
            try:
                return next(instruction_iter)
            except StopIteration:
                return "v"

        def fake_encrypt(self: MalbolgeMachine) -> None:
            self.c -= 1
            self.d -= 1

        cast(Any, interpreter)._instruction_at = MethodType(
            fake_instruction, interpreter
        )
        cast(Any, machine).encrypt_current_cell = MethodType(fake_encrypt, machine)

        result = interpreter.resume_execution()
        self.assertTrue(result.halt_metadata.cycle_detected)
        self.assertEqual(result.halt_metadata.cycle_repeat_length, 1)
        self.assertFalse(result.halt_metadata.cycle_tracking_limited)
        self.assertEqual(result.halt_reason, "halt_opcode")

    def test_jump_instruction_expands_capacity(self) -> None:
        interpreter = MalbolgeInterpreter()
        result = interpreter.execute("iv", capture_machine=True)
        self.assertTrue(result.halted)

    def test_separate_interpreters_run_in_parallel(self) -> None:
        def execute_program(_: int) -> str:
            return MalbolgeInterpreter().execute("v").output

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(execute_program, range(8)))
        self.assertTrue(all(result == "" for result in results))

    def test_shared_interpreter_serializes_threads(self) -> None:
        interpreter = MalbolgeInterpreter()
        original = interpreter._execute_loaded
        active = 0
        active_lock = threading.Lock()

        def wrapped(
            self: MalbolgeInterpreter,
            *,
            input_buffer: Iterable[str] | None,
            max_steps: int | None,
            capture_machine: bool,
        ) -> ExecutionResult:
            nonlocal active
            with active_lock:
                if active:
                    raise AssertionError("concurrent execution detected")
                active += 1
            try:
                return original(
                    input_buffer=input_buffer,
                    max_steps=max_steps,
                    capture_machine=capture_machine,
                )
            finally:
                with active_lock:
                    active -= 1

        cast(Any, interpreter)._execute_loaded = MethodType(wrapped, interpreter)

        def run_program(_: int) -> str:
            return interpreter.execute("v").halt_reason

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(run_program, range(8)))
        self.assertTrue(all(reason == "halt_opcode" for reason in results))


if __name__ == "__main__":
    unittest.main()
