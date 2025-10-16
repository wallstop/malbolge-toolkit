# SPDX-License-Identifier: MIT
"""
Example: inspect interpreter results for a generated Malbolge program.

Run with:
    python examples/analyze_program.py --text "Hi"
"""

from __future__ import annotations

import argparse
from pprint import pprint

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from malbolge import GenerationConfig, ProgramGenerator, MalbolgeInterpreter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a generated Malbolge program."
    )
    parser.add_argument("--text", default="Hello", help="Target string to generate.")
    parser.add_argument(
        "--seed", type=int, default=1234, help="Random seed for deterministic search."
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum search depth before randomization.",
    )
    parser.add_argument(
        "--opcodes", default="op*", help="Opcode choices considered during search."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    generator = ProgramGenerator()
    config = GenerationConfig(
        opcode_choices=args.opcodes,
        max_search_depth=args.max_depth,
        random_seed=args.seed,
    )
    result = generator.generate_for_string(args.text, config=config)

    interpreter = MalbolgeInterpreter()
    execution = interpreter.execute(result.opcodes, capture_machine=True)

    print("=== Generation ===")
    print("Target:", result.target)
    print("Opcodes:", result.opcodes)
    print("Output:", result.machine_output)
    print("Stats:")
    pprint(result.stats)

    print("\n=== Execution ===")
    print("Stdout:", execution.output)
    print("Halt reason:", execution.halt_reason)
    print("Steps:", execution.steps)
    if execution.machine is not None:
        print("Tape length:", len(execution.machine.tape))
        print("Register A:", execution.machine.a)
        print("Register C:", execution.machine.c)
        print("Register D:", execution.machine.d)


if __name__ == "__main__":
    main()
