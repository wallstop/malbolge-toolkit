# Contributor Guidelines

**Welcome to the MalbolgeGenerator project!** Whether you're fixing a bug, adding a feature, or improving documentation, we appreciate your contribution. This guide will help you understand how the project is organized and what standards we follow.

## Project Structure & Module Organization

**Where the code lives:** The main codebase is in the `malbolge/` package. Here's what each part does:

- **`malbolge/interpreter.py`** — The Malbolge execution engine (`MalbolgeInterpreter`), error classes (like `InvalidOpcodeError`), and execution results
- **`malbolge/generator.py`** — The program generator (`ProgramGenerator`), configuration (`GenerationConfig`), and performance statistics
- **`malbolge/encoding.py` / `utils.py`** — Helper functions for converting between ASCII and opcodes, plus ternary arithmetic utilities

**Where to put new code:**

- **Experiments and demos** → `examples/` directory
- **Advanced experimental features** → `malbolge/advanced/`
- **Core functionality** → Appropriate file in `malbolge/` (discuss first in an issue)

## Getting Started: Build, Test, and Development Commands

**Setting up your development environment:**

1. **Create a virtual environment** (keeps dependencies isolated):

   ```bash
   python -m venv .venv
   ```

1. **Activate it**:

   - Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
   - macOS/Linux: `source .venv/bin/activate`

1. **Install the package in editable mode** (changes take effect immediately):

   ```bash
   python -m pip install -e .
   ```

1. **Install pre-commit hooks** (automatically formats code before commits):

   ```bash
   pre-commit install
   ```

**Running tests and checks:**

- **Run all tests**: `python -m unittest discover -v`

  - Tests cover interpreter execution, generator logic, encoding/decoding, and CLI commands

- **Quick smoke test**: `python -c "from malbolge import ProgramGenerator; print(ProgramGenerator().generate_for_string('Hi').opcodes)"`

  - Verifies basic generation works

- **Run benchmarks**: `python -m malbolge.cli bench`

  - Tests performance before/after changes
  - Important for performance-sensitive modifications

## Coding Style & Naming Conventions

**We follow standard Python conventions with automatic formatting:**

### Formatting (Automated)

- **Black** automatically formats all code (configured in `pyproject.toml`)
- Run `pre-commit run --all-files` before pushing to ensure formatting is correct
- Pre-commit hooks will catch issues before they reach GitHub

### Naming Rules

- **Functions and variables**: `snake_case` (e.g., `generate_program`, `max_depth`)
- **Classes**: `UpperCamelCase` (e.g., `ProgramGenerator`, `MalbolgeInterpreter`)
- **Constants**: `ALL_CAPS` (e.g., `ENCRYPTION_TRANSLATE`, `MAX_ADDRESS_SPACE`)
- **Private/internal functions**: Prefix with `_` (e.g., `_calculate_opcode`)

### Code Organization

- **Constants** at the top of files (translation tables, limits, etc.)
- **Documentation** in docstrings (not inline comments) for complex logic
- **Type hints** on all public functions (helps users and catches bugs early)
- **4 spaces** for indentation (handled by Black automatically)

### Example of Good Code Style

```python
# Constants at the top
MAX_SEARCH_DEPTH = 5
DEFAULT_OPCODES = "op*"


def generate_for_string(
    target: str, config: GenerationConfig | None = None
) -> GenerationResult:
    """
    Generate a Malbolge program that prints the target string.

    Args:
        target: The string to generate a program for
        config: Optional configuration (uses defaults if None)

    Returns:
        GenerationResult containing the program and statistics
    """
    # Implementation here
    pass
```

## Testing Guidelines

**All code contributions should include tests.** Here's how to write good tests:

### Test Organization

- **Location**: `tests/` directory
- **File naming**: Mirror module names (e.g., `tests/test_interpreter.py` for `malbolge/interpreter.py`)
- **Test naming**: Use descriptive names like `test_generate_hello_world_with_seed_42`

### Writing Tests

**1. Use deterministic seeds** (for consistent results):

```python
def test_generation_is_deterministic(self):
    config = GenerationConfig(random_seed=42)

    # Fresh generators ensure determinism test is valid
    generator1 = ProgramGenerator()
    generator2 = ProgramGenerator()

    result1 = generator1.generate_for_string("Hi", config=config)
    result2 = generator2.generate_for_string("Hi", config=config)

    self.assertEqual(result1.opcodes, result2.opcodes)  # Same seed = same program
```

**2. Test both success and failure cases**:

```python
# Success case
def test_valid_program_executes(self):
    interpreter = MalbolgeInterpreter()
    result = interpreter.execute("v")  # Simple halt
    self.assertTrue(result.halted)
    self.assertEqual(result.halt_reason, "halt_opcode")


# Failure case
def test_invalid_opcode_raises_error(self):
    interpreter = MalbolgeInterpreter()
    with self.assertRaises(InvalidOpcodeError):
        interpreter.execute("xyz")  # Invalid opcodes
```

**3. Test edge cases**:

- Empty strings
- Very long strings
- Special characters
- Memory limits
- Maximum step limits

### Coverage Goals

- **Target**: ≥80% code coverage
- **Check with**: `python -m coverage run -m unittest discover && python -m coverage report`
- Add tests when adding features, not later!

## Commit & Pull Request Guidelines

**Good commits and PRs make collaboration easier for everyone!**

### Commit Messages

**Format**: Use the imperative mood (like giving commands)

```
Good: "Add support for custom opcode sets"
Bad:  "Added support for custom opcode sets"
Bad:  "Adding support for custom opcode sets"
```

**Structure**:

```
Short summary (≤60 characters)

Longer explanation if needed. Explain WHY the change was made,
not just WHAT changed (the code shows what).

Fixes #123
```

**Examples**:

```
Fix interpreter crash on empty input (#42)

Add trace visualization to debug module

Optimize cache hit rate in generator
The old implementation was re-computing states unnecessarily.
This change improves cache hits by 15% on average.

Related to #87
```

### Pull Requests

**Your PR should include**:

1. **Clear description** of what changed and why
1. **How to test** the changes (specific commands to run)
1. **Example output** if the change affects program generation or execution
1. **Tests** for new functionality
1. **Documentation updates** if you changed the API

**Example PR description**:

```markdown
## What Changed
Added support for configurable cycle detection limits in the interpreter.

## Why
Users reported needing different limits for different program types.

## How to Test
python -m malbolge.cli run --opcodes "iooo..." --cycle-limit 100000

## Example Output
[paste example showing new behavior]

## Checklist
- [x] Added tests
- [x] Updated documentation
- [x] All tests pass
```

## Important: Reproducibility & Safety

**When working on the generator or interpreter, keep these rules in mind:**

### Generator Performance Metrics

The `ProgramGenerator` tracks important statistics that you should always check when making changes:

- `evaluations` - How many candidates were tested
- `cache_hits` - How often cached states were reused
- `pruned` - How many dead ends were eliminated
- `duration_ns` - How long generation took

**When tuning heuristics**: Always capture and compare these metrics before and after your changes!

### Modifying Translation Tables

If you edit encoding tables (ASCII ↔ opcode mappings):

1. **Update all related constants together** (don't leave mismatches)
1. **Run normalization tests** to ensure existing programs still work
1. **Document the reason** for the change (why was the old version wrong?)

### Committing Generated Programs

**Never commit generated Malbolge programs** unless you document:

- The exact seed used
- The configuration (max depth, opcode choices, etc.)
- Why this specific program is being committed (e.g., "test case for X")
- How to regenerate it

This ensures others can reproduce the program and understand its purpose.

## Adding Examples & Demos

**Examples help users understand how to use the project!**

### Where Examples Go

- **Short scripts** (\< 100 lines) → `examples/` directory

  - Good for: `analyze_program.py`, `profile_generator.py`
  - Show one specific feature or workflow
  - Include clear docstrings and comments

- **Interactive tutorials** → `notebooks/` directory

  - Good for: Step-by-step walkthroughs with explanations
  - Use Jupyter notebooks (`.ipynb` files)
  - Example: `Malbolge_Advanced_Tour.ipynb`

### When Adding Examples

1. **Keep them updated**: If you change the API, update affected examples
1. **Make them runnable**: Examples should work without modification
1. **Add clear output**: Show users what they should expect to see
1. **Document parameters**: Explain what each flag/option does

## Documentation

**Good documentation is as important as good code!**

### When to Update Documentation

Update documentation whenever you:

- Add a new feature or command
- Change default behavior
- Add/remove/rename parameters
- Fix a bug that users might encounter

### Key Documentation Files

- **`docs/TUTORIAL.md`** - Complete CLI tutorial with troubleshooting

  - Update when adding CLI commands or changing workflows

- **`docs/MALBOLGE_PRIMER.md`** - Beginner's guide to Malbolge

  - Update rarely (only for major conceptual additions)

- **`README.md`** - Quick start and API overview

  - Update for new features or major changes

- **`benchmarks/`** - Performance baselines

  - Refresh when you change heuristics or add optimizations

## Code Quality Tools

**We use automated tools to maintain code quality:**

### Linting (Catches Common Mistakes)

```bash
python -m ruff check .
```

Run this before committing to catch:

- Unused imports
- Undefined variables
- Style violations
- Common bugs

### Type Checking (Catches Type Errors)

```bash
python -m mypy malbolge
```

Ensures type hints are correct and consistent. All public APIs should have type hints!

### Continuous Integration

GitHub Actions runs these checks automatically:

- All tests (`unittest`)
- Linting (`ruff`)
- Type checking (`mypy`)
- Code formatting (`black`)

**Keep `pyproject.toml` in sync** with these tools' configurations.

## Logging Best Practices

**Use proper logging instead of `print()` statements:**

```python
import logging

logger = logging.getLogger(__name__)

# Good - structured logging
logger.info("Generated program in %.2fms", duration_ms)
logger.debug("Candidate pruned: %s", reason)

# Bad - print statements
print(f"Generated program in {duration_ms}ms")
```

### Logging Levels

- **DEBUG**: Detailed diagnostic information (algorithm internals)
- **INFO**: Confirmation that things are working (progress updates)
- **WARNING**: Something unexpected but not an error
- **ERROR**: An error occurred but program can continue
- **CRITICAL**: Serious error, program might crash

### User-Facing Errors

Combine logging with user-friendly error messages:

```python
try:
    result = execute_program(opcodes)
except InvalidOpcodeError as e:
    logger.debug("Full error context: %s", e, exc_info=True)
    print(f"Error: Invalid Malbolge opcode encountered. Check your program.")
    sys.exit(1)
```

Users can enable verbose logging with: `--log-level DEBUG`
