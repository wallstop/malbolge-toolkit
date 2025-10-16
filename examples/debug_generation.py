# SPDX-License-Identifier: MIT
"""
Advanced example: inspect generator traces and interpreter diagnostics.

Run with:
    python examples/debug_generation.py --text "Hi" --seed 42
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from malbolge import GenerationConfig, MalbolgeInterpreter, ProgramGenerator
except ImportError:  # pragma: no cover - fallback for direct script invocation
    REPO_ROOT = Path(__file__).resolve().parents[1]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from malbolge import GenerationConfig, MalbolgeInterpreter, ProgramGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Debug the generator using trace capture and interpreter metadata."
    )
    parser.add_argument("--text", default="Hello", help="Target string to generate.")
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for deterministic search."
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum search depth before randomization.",
    )
    parser.add_argument(
        "--opcodes",
        default="op*",
        help="Opcode choices considered during search (default: op*).",
    )
    parser.add_argument(
        "--trace-limit",
        type=int,
        default=25,
        help="Number of trace events to print (0 for all).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    generator = ProgramGenerator()
    config = GenerationConfig(
        opcode_choices=args.opcodes,
        max_search_depth=args.max_depth,
        random_seed=args.seed,
        capture_trace=True,
    )
    result = generator.generate_for_string(args.text, config=config)

    print("=== Generation Summary ===")
    print(f"Target: {result.target!r}")
    print(f"Opcodes: {result.opcodes[:80]}{'...' if len(result.opcodes) > 80 else ''}")
    print("Stats:")
    print(json.dumps(result.stats, indent=2))

    trace_limit = args.trace_limit if args.trace_limit > 0 else len(result.trace)
    print(f"\nTrace (first {trace_limit} events):")
    for event in result.trace[:trace_limit]:
        print(json.dumps(event, ensure_ascii=False))

    interpreter = MalbolgeInterpreter()
    execution = interpreter.execute(result.opcodes, capture_machine=True)
    print("\n=== Execution Diagnostics ===")
    print(f"Output: {execution.output}")
    print(f"Halt reason: {execution.halt_reason}")
    print(f"Steps: {execution.steps}")
    print(f"Halt instruction: {execution.halt_metadata.last_instruction}")
    if execution.halt_metadata.last_jump_target is not None:
        print(f"Last jump target: {execution.halt_metadata.last_jump_target}")
    print(f"Cycle detected: {execution.halt_metadata.cycle_detected}")
    print(f"Cycle tracking limited: {execution.halt_metadata.cycle_tracking_limited}")
    print(f"Memory expansions: {execution.memory_expansions}")
    print(f"Peak tape cells: {execution.peak_memory_cells}")
    if execution.machine is not None:
        print(f"Tape length: {len(execution.machine.tape)}")


if __name__ == "__main__":
    main()
