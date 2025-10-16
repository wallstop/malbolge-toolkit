# Repository Guidelines
## Project Structure & Module Organization
The public API now lives in the `malbolge/` package:
- `malbolge/interpreter.py` — `MalbolgeInterpreter`, error subclasses, and execution results
- `malbolge/generator.py` — `ProgramGenerator`, `GenerationConfig`, profiling stats
- `malbolge/encoding.py` / `utils.py` — translation tables and arithmetic helpers
`MalbolgeInterpreter.py` remains as a thin compatibility shim for legacy imports. Place experiments under `examples/` and document any advanced tooling inside `malbolge/advanced/`.

## Build, Test, and Development Commands
- `python -m venv .venv` — create an isolated Python 3.11+ environment (Python 3.11 or newer).
- `.\.venv\Scripts\Activate.ps1` / `source .venv/bin/activate` — activate the environment.
- `python -m pip install -e .` — install the package in editable mode for local development.
- `pre-commit install` — install Git hooks (runs Black before every commit).
- `python -m unittest discover -v` — run the full regression suite covering encoding, interpreter, and generator behaviour.
- `python -c "from malbolge import ProgramGenerator; print(ProgramGenerator().generate_for_string('Hi').opcodes)"` — quick smoke test for program generation.
- `python -m malbolge.cli bench` — exercise interpreter/generator benchmarks before and after performance-sensitive changes.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indents, snake_case functions, and UpperCamelCase only for classes you add. Code is auto-formatted with Black (see pyproject.toml); run `pre-commit run --all-files` before pushing. Keep constants like the translation tables in ALL_CAPS near the top and document tricky transformations with docstrings instead of inline notes. Add type hints on public entry points and prefix internal helpers with `_`.

## Testing Guidelines
Place tests under `tests/`, mirroring module names (`tests/test_interpreter.py`, `tests/test_generator.py`). Seed the RNG through `GenerationConfig(random_seed=...)` for deterministic runs. Assert both success paths (output matches, halt reason is expected) and failure paths using the dedicated exceptions (`InvalidOpcodeError`, `InputUnderflowError`, `MemoryLimitExceededError`, `StepLimitExceededError`). Target ≥80% coverage as features expand and add benchmarks for heuristics when stabilised.

## Commit & Pull Request Guidelines
History uses concise imperative subjects with optional issue references (for example `Initialize repo, fix bug... (#2)`). Keep subjects under 60 characters, add detail in the body, and reference issues or discussions in the footer. Pull requests must describe behaviour changes, share repro or verification steps, and paste interpreter output whenever program generation changes.

## Reproducibility & Safety Notes
`ProgramGenerator` memoizes interpreter snapshots, prunes dead branches, and reports stats (`evaluations`, `cache_hits`, `pruned`, `duration_ns`). Always capture these metrics when tuning heuristics. When editing translation tables, update related constants together and rerun normalization checks to avoid corrupting existing Malbolge snippets. Commit generated programs only when their provenance, seed, and configuration are documented in the commit message or accompanying notes.

## Examples & Demos
Use the scripts under `examples/` (e.g., `examples/analyze_program.py`, `examples/profile_generator.py`) to showcase interpreter statistics and generator performance. Keep these examples in sync with CLI capabilities and update them whenever public APIs change. Longer walkthroughs belong in `notebooks/` (see `Malbolge_Advanced_Tour.ipynb`).

## Documentation
- `docs/TUTORIAL.md` captures full CLI workflows, troubleshooting, and links to examples/notebooks. Update it whenever you add new commands or change default behaviour.
- `benchmarks/capture_baseline.py` records interpreter/generator telemetry snapshots; refresh the baseline when heuristics change.

## Typing & Linting
- Run `python -m ruff check .` before committing to maintain style and catch common issues.
- Run `python -m mypy malbolge` to ensure new APIs remain type-safe.
- CI enforces both commands along with the unittest suite; keep the `pyproject.toml` config in sync with project conventions.

**Log & Error Handling**
- Prefer the standard logging module over bare print statements in CLI or library code.
- Use logging.getLogger(__name__) per module and configure handlers in the CLI entrypoint.
- Emit structured messages (status, module, context) to simplify downstream parsing.
- Continue surfacing user-friendly error messages while logging detailed context at debug level.
- Use the CLI `--log-level` flag (DEBUG/INFO/...) when you need verbose diagnostics during manual testing.

