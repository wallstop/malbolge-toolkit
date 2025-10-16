# SPDX-License-Identifier: MIT

import unittest

from malbolge.generator import GenerationConfig, ProgramGenerator
from malbolge.interpreter import MalbolgeInterpreter


class GeneratorTests(unittest.TestCase):
    def test_generate_simple_string(self) -> None:
        generator = ProgramGenerator()
        config = GenerationConfig(random_seed=1234)
        result = generator.generate_for_string("A", config=config)

        self.assertEqual(result.target, "A")
        self.assertTrue(result.opcodes.endswith("v"))
        self.assertGreater(len(result.malbolge_program), 0)
        self.assertIn("evaluations", result.stats)
        self.assertIn("cache_hits", result.stats)
        self.assertIn("pruned", result.stats)
        self.assertIn("duration_ns", result.stats)
        self.assertGreater(result.stats["evaluations"], 0)
        self.assertGreaterEqual(result.stats["pruned"], 0)
        self.assertGreater(result.stats["duration_ns"], 0)

        interpreter = MalbolgeInterpreter()
        self.assertEqual(interpreter.run(result.opcodes), "A")

    def test_generation_is_deterministic_with_seed(self) -> None:
        config = GenerationConfig(random_seed=42)
        generator_one = ProgramGenerator()
        generator_two = ProgramGenerator()

        result_one = generator_one.generate_for_string("Hi", config=config)
        result_two = generator_two.generate_for_string("Hi", config=config)

        self.assertEqual(result_one.opcodes, result_two.opcodes)
        self.assertEqual(result_one.machine_output, result_two.machine_output)
        stats_one = dict(result_one.stats)
        stats_two = dict(result_two.stats)
        duration_one = stats_one.pop("duration_ns", None)
        duration_two = stats_two.pop("duration_ns", None)
        self.assertIsNotNone(duration_one)
        self.assertIsNotNone(duration_two)
        self.assertGreater(duration_one, 0)
        self.assertGreater(duration_two, 0)
        self.assertEqual(stats_one, stats_two)

    def test_empty_target_fails_fast(self) -> None:
        generator = ProgramGenerator()
        with self.assertRaises(ValueError):
            generator.generate_for_string("")


if __name__ == "__main__":
    unittest.main()
