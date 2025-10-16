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
import json
import logging
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from malbolge import (
    GenerationConfig,
    MalbolgeInterpreter,
    MalbolgeRuntimeError,
    ProgramGenerator,
    normalize,
)
from malbolge.encoding import InvalidProgramError
from malbolge.interpreter import DEFAULT_CYCLE_DETECTION_LIMIT

logger = logging.getLogger(__name__)
log = logging.LoggerAdapter(logger, {"component": __name__})


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="malbolge")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging verbosity (default: WARNING).",
    )
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
        help=(
            "Path to a file containing ASCII Malbolge source to normalize before "
            "execution."
        ),
    )
    cycle_group = run_parser.add_mutually_exclusive_group()
    cycle_group.add_argument(
        "--cycle-limit",
        type=int,
        help=(
            "Override the number of unique states tracked for cycle detection "
            f"(default: {DEFAULT_CYCLE_DETECTION_LIMIT})."
        ),
    )
    cycle_group.add_argument(
        "--no-cycle-detection",
        action="store_true",
        help="Disable cycle detection tracking entirely.",
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
    generate_parser.add_argument(
        "--trace",
        action="store_true",
        help="Capture a detailed search trace (printed as JSON).",
    )

    bench_parser = subparsers.add_parser(
        "bench", help="Run interpreter and generator micro-benchmarks."
    )
    bench_parser.add_argument(
        "--module", choices=("interpreter", "generator", "all"), default="all"
    )

    return parser.parse_args(argv)


def handle_run(args: argparse.Namespace) -> int:
    if args.no_cycle_detection:
        cycle_limit: int | None = None
    elif args.cycle_limit is not None:
        if args.cycle_limit < 0:
            _emit_error(
                "cycle detection limit must be non-negative",
                context={"command": "run"},
            )
            return 1
        cycle_limit = args.cycle_limit
    else:
        cycle_limit = DEFAULT_CYCLE_DETECTION_LIMIT

    interpreter = MalbolgeInterpreter(cycle_detection_limit=cycle_limit)
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
        _emit_error(
            f"failed to read program input: {exc}",
            context={"command": "run"},
            exc=exc,
        )
        return 1
    except InvalidProgramError as exc:
        _emit_error(str(exc), context={"command": "run"})
        return 1
    except MalbolgeRuntimeError as exc:
        _emit_error(str(exc), context={"command": "run"}, exc=exc)
        return 1

    print(result.output)
    print(f"halt_reason={result.halt_reason}")
    print(f"steps={result.steps}")
    if result.halt_metadata.last_instruction is not None:
        print(f"halt_instruction={result.halt_metadata.last_instruction}")
    if result.halt_metadata.last_jump_target is not None:
        print(f"last_jump_target={result.halt_metadata.last_jump_target}")
    print(f"cycle_detected={result.halt_metadata.cycle_detected}")
    print(f"cycle_tracking_limited={result.halt_metadata.cycle_tracking_limited}")
    print(f"cycle_repeat_length={result.halt_metadata.cycle_repeat_length}")
    print(f"memory_expansions={result.memory_expansions}")
    print(f"peak_tape_cells={result.peak_memory_cells}")
    if result.machine is not None:
        print(f"tape_length={len(result.machine.tape)}")
    return 0


def handle_generate(args: argparse.Namespace) -> int:
    generator = ProgramGenerator()
    config = GenerationConfig(
        opcode_choices=args.opcodes,
        max_search_depth=args.max_depth,
        random_seed=args.seed,
        capture_trace=args.trace,
    )
    try:
        result = generator.generate_for_string(args.text, config=config)
    except MalbolgeRuntimeError as exc:
        _emit_error(str(exc), context={"command": "generate"}, exc=exc)
        return 1

    print(result.opcodes)
    print(result.malbolge_program)
    print(result.machine_output)
    print(result.stats)
    if args.trace:
        print(f"trace={json.dumps(result.trace, ensure_ascii=False)}")
        reason_counts = Counter(
            event.get("reason", "unknown") for event in result.trace
        )
        print(f"trace_summary={json.dumps(reason_counts, ensure_ascii=False)}")
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
            _emit_warning(
                f"module {module_name} has no main()",
                context={"command": "bench", "module": module_name},
            )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_logging(args.log_level)
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


def _configure_logging(level_str: str) -> None:
    level = getattr(logging, level_str.upper(), logging.WARNING)
    logging.basicConfig(level=level, format="%(levelname)s:%(name)s:%(message)s")


def _emit_error(
    message: str,
    *,
    context: dict[str, object] | None = None,
    exc: Exception | None = None,
) -> None:
    extra: dict[str, object] = {"status": "error"}
    if context:
        extra.update(context)
    log.error(message, extra=extra, exc_info=exc)
    print(f"[error] {message}", file=sys.stderr)


def _emit_warning(message: str, *, context: dict[str, object] | None = None) -> None:
    extra: dict[str, object] = {"status": "warn"}
    if context:
        extra.update(context)
    log.warning(message, extra=extra)
    print(f"[warn] {message}", file=sys.stderr)


if __name__ == "__main__":
    app()
