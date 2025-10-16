# SPDX-License-Identifier: MIT
"""
Command-line entry point for Malbolge tools.

Usage examples:
    python -m malbolge.cli run --opcodes "v"
    python -m malbolge.cli run --opcodes-file program.op
    python -m malbolge.cli generate --text "Hello"
    python -m malbolge.cli bench
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Sequence

from malbolge import (
    GenerationConfig,
    ProgramGenerator,
    MalbolgeInterpreter,
    MalbolgeRuntimeError,
    normalize,
)
from malbolge.encoding import InvalidProgramError


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="malbolge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="Execute Malbolge opcodes or ASCII source."
    )
    run_group = run_parser.add_mutually_exclusive_group(required=True)
    run_group.add_argument("--opcodes", help="Raw opcode string ending with 'v'.")
    run_group.add_argument(
        "--opcodes-file",
        type=Path,
        help="Path to a file containing raw opcodes; whitespace is stripped.",
    )
    run_group.add_argument(
        "--ascii",
        help="ASCII Malbolge program that will be normalized before execution.",
    )
    run_group.add_argument(
        "--ascii-file",
        type=Path,
        help="Path to a file containing ASCII Malbolge source to normalize before execution.",
    )

    generate_parser = subparsers.add_parser(
        "generate", help="Generate a Malbolge program for a target string."
    )
    generate_parser.add_argument("--text", required=True, help="Desired output string.")
    generate_parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for deterministic search."
    )
    generate_parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum search depth before randomization.",
    )
    generate_parser.add_argument(
        "--opcodes", default="op*", help="Opcode choices considered during search."
    )

    bench_parser = subparsers.add_parser(
        "bench", help="Run interpreter and generator micro-benchmarks."
    )
    bench_parser.add_argument(
        "--module", choices=("interpreter", "generator", "all"), default="all"
    )

    return parser.parse_args(argv)


def handle_run(args: argparse.Namespace) -> int:
    interpreter = MalbolgeInterpreter()
    try:
        if args.opcodes:
            opcodes = args.opcodes
        elif args.opcodes_file is not None:
            opcode_text = args.opcodes_file.read_text(encoding="utf-8")
            opcodes = "".join(ch for ch in opcode_text if not ch.isspace())
            if not opcodes:
                raise InvalidProgramError("Opcode file is empty.")
        else:
            if args.ascii is not None:
                ascii_source = args.ascii
            elif args.ascii_file is not None:
                ascii_source = args.ascii_file.read_text(encoding="utf-8")
            else:
                raise InvalidProgramError("No ASCII source provided.")
            opcodes = "".join(normalize(ascii_source))
        result = interpreter.execute(opcodes, capture_machine=True)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"[error] failed to read program input: {exc}", file=sys.stderr)
        return 1
    except InvalidProgramError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    except MalbolgeRuntimeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(result.output)
    print(f"halt_reason={result.halt_reason}")
    print(f"steps={result.steps}")
    if result.machine is not None:
        print(f"tape_length={len(result.machine.tape)}")
    return 0


def handle_generate(args: argparse.Namespace) -> int:
    generator = ProgramGenerator()
    config = GenerationConfig(
        opcode_choices=args.opcodes,
        max_search_depth=args.max_depth,
        random_seed=args.seed,
    )
    try:
        result = generator.generate_for_string(args.text, config=config)
    except MalbolgeRuntimeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(result.opcodes)
    print(result.malbolge_program)
    print(result.machine_output)
    print(result.stats)
    return 0


def handle_bench(args: argparse.Namespace) -> int:
    modules = []
    if args.module in ("interpreter", "all"):
        modules.append("benchmarks.bench_interpreter")
    if args.module in ("generator", "all"):
        modules.append("benchmarks.bench_generator")

    for module_name in modules:
        module = importlib.import_module(module_name)
        if hasattr(module, "main"):
            module.main()
        else:
            print(f"[warn] module {module_name} has no main()", file=sys.stderr)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "run":
        return handle_run(args)
    if args.command == "generate":
        return handle_generate(args)
    if args.command == "bench":
        return handle_bench(args)
    print(f"[error] unknown command {args.command}", file=sys.stderr)
    return 1


def app() -> None:
    sys.exit(main())


if __name__ == "__main__":
    app()
