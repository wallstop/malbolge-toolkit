# SPDX-License-Identifier: MIT
"""
Simple example: Generate and run a "Hello" program.

This is the simplest possible example showing the basic workflow.

Run with:
    python examples/simple_hello.py
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from malbolge import MalbolgeInterpreter, ProgramGenerator
except ImportError:  # pragma: no cover - fallback for direct script invocation
    REPO_ROOT = Path(__file__).resolve().parents[1]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from malbolge import MalbolgeInterpreter, ProgramGenerator


def main() -> None:
    print("=== Malbolge Simple Example ===\n")

    # Step 1: Generate a program
    print("Step 1: Generating program for 'Hello'...")
    generator = ProgramGenerator()
    result = generator.generate_for_string("Hello")

    print(f"[OK] Generated in {result.stats['duration_ns']/1e6:.2f}ms")
    print(f"  Opcodes (first 50 chars): {result.opcodes[:50]}...")
    print(f"  Program length: {len(result.opcodes)} opcodes")
    print(f"  Evaluations: {result.stats['evaluations']}")
    pruned = result.stats["pruned"]
    prune_ratio = (pruned / result.stats["evaluations"]) * 100
    print(f"  Pruned: {pruned} ({prune_ratio:.1f}%)")

    # Step 2: Run the program
    print("\nStep 2: Executing generated program...")
    interpreter = MalbolgeInterpreter()
    execution = interpreter.execute(result.opcodes)

    print("[OK] Execution complete")
    print(f"  Output: {execution.output}")
    print(f"  Steps: {execution.steps}")
    print(f"  Halt reason: {execution.halt_reason}")

    # Step 3: Verify correctness
    print("\nStep 3: Verifying correctness...")
    assert execution.output == "Hello", f"Expected 'Hello', got '{execution.output}'"
    assert execution.halted, "Program did not halt properly"
    print("[OK] All checks passed!")

    print("\n=== Summary ===")
    print("Successfully generated and executed a Malbolge program that prints 'Hello'")
    duration_ms = result.stats["duration_ns"] / 1_000_000
    candidates = result.stats["evaluations"]
    print(f"Generation: {candidates} candidates tested, {duration_ms:.2f}ms")
    print(f"Execution: {execution.steps} steps, {execution.halt_reason}")


if __name__ == "__main__":
    main()
