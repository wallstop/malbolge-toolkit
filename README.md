# MalbolgeGenerator

**Automatically generate and execute programs in Malbolge, the most difficult esoteric programming language ever created.**

## What is This?

MalbolgeGenerator is a Python toolkit that solves a fascinating challenge: **automatically writing programs in Malbolge**, a programming language so intentionally difficult that the first "Hello World" program took 2 years to create and required computer search algorithms to discover (no human could write it by hand!).

**Think of it this way:** Malbolge is to programming what a Rubik's Cube with 1000 sides would be to puzzles - theoretically possible but practically impossible for humans to solve directly.

### What This Project Does For You

- **Automatic Program Generation**: Simply provide text like "Hello" and get a working Malbolge program instantly
- **High-Performance Interpreter**: Run and debug Malbolge programs with detailed execution information
- **Easy-to-Use API**: Work with Malbolge through simple Python code or command-line tools
- **Learning Resources**: Comprehensive guides to understand this fascinating esoteric language

**Complete Beginner?** No problem! Start with our [Malbolge Primer](docs/MALBOLGE_PRIMER.md) - it explains everything from scratch with no prior knowledge assumed.

## What You'll Learn

By using this project, you'll gain hands-on experience with:

- **Automated Code Generation**: See how AI search algorithms can write code that humans can't
- **Constraint Solving**: Understanding breadth-first search, branch pruning, and state caching
- **Esoteric Computing**: Explore ternary arithmetic and non-binary computing models
- **Language Design**: Appreciate what makes a language "hard" and how complexity emerges
- **Performance Optimization**: Learn about caching strategies and search space reduction

This isn't just about Malbolge - it's about algorithm design, optimization, and computational thinking!

## What is Malbolge?

Malbolge (named after the 8th circle of Hell in Dante's Inferno) is an esoteric programming language intentionally designed in 1998 to be **as difficult as possible** to program in. Here's what makes it so challenging:

- **Self-modifying code**: Instructions literally change themselves after running, like a book that rewrites its own pages as you read
- **Ternary arithmetic**: Uses base-3 math (0, 1, 2) instead of binary (0, 1), which is unfamiliar to most programmers
- **Limited instructions**: Only 8 valid operations, each behaving in counter-intuitive ways
- **The "crazy operation"**: A specially designed logic operation that's nearly impossible to reason about

**Important**: Malbolge programs are NOT written by hand - even experts use generators like this one! The language was specifically designed to make manual programming impossible.

## Features

This project ships as a modular Python package (`malbolge`) with:

- **`ProgramGenerator`**: Deterministic, cache-aware synthesis engine with repeated-state pruning and optional trace capture for any target string
- **`MalbolgeInterpreter`**: High-performance execution engine with configurable memory limits and structured results
- **Utility Modules**: Encoding/decoding, base-3 arithmetic, and crazy-operation simulation
- **CLI Tools**: Command-line interface for generation, execution, and benchmarking
- **Examples & Notebooks**: Working code examples and interactive Jupyter tutorials

## Quick Start

### Installation

```bash
# Clone the repository (use your fork instead of wallstop if applicable)
git clone https://github.com/wallstop/MalbolgeGenerator.git
cd MalbolgeGenerator

# Create a virtual environment (recommended)
python -m venv .venv

# Activate it
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
# source .venv/bin/activate

# Install the package
python -m pip install -e .
```

### Your First Malbolge Program (60 seconds)

Let's create your first Malbolge program! This command will generate a program that prints "Hello":

```bash
python -m malbolge.cli generate --text "Hello" --seed 42
```

**What you'll see:**

```
Opcodes: ioooooo...p<v
ASCII: (scrambled characters)
Output: Hello
Stats: {
    'evaluations': 12453,
    'cache_hits': 42,
    'pruned': 11890,
    'repeated_state_pruned': 512,
    'duration_ns': 80432123,
    'trace_length': 0
}
```

**Understanding the output:**

- **Opcodes**: The internal representation (like machine code)
- **ASCII**: The actual Malbolge program (looks like gibberish - that's normal!)
- **Output**: What your program prints when run
- **Stats**: Performance metrics showing how the program was found

Now run your generated program:

```bash
python -m malbolge.cli run --opcodes "ioooooo...p<v"
```

Congratulations! You just generated and ran a Malbolge program - something no human could write by hand!

**Quick Test**: Verify your installation works:

```bash
python -c "from malbolge import ProgramGenerator, MalbolgeInterpreter; print('Installation successful!')"
```

### Using the Python API

```python
from malbolge import ProgramGenerator, MalbolgeInterpreter

# Generate a program
generator = ProgramGenerator()
result = generator.generate_for_string("Hi")

print(f"Opcodes: {result.opcodes}")
print(f"Output: {result.machine_output}")
print(f"Generated in: {result.stats['duration_ns'] / 1e6:.2f}ms")

# Run it through the interpreter
interpreter = MalbolgeInterpreter()
execution = interpreter.execute(result.opcodes)

print(f"Verified output: {execution.output}")
print(f"Steps executed: {execution.steps}")
print(f"Halt reason: {execution.halt_reason}")
```

**Note**: Legacy imports are now fully superseded by the modular `malbolge` package—update any remaining references to `MalbolgeInterpreter.py`.

## Command-Line Interface (CLI)

The CLI provides three main commands:

### 1. Generate Programs

```bash
# Basic generation
python -m malbolge.cli generate --text "Hello"

# With deterministic seed for reproducibility
python -m malbolge.cli generate --text "Hello" --seed 42

# Tune search parameters
python -m malbolge.cli generate --text "ABC" --max-depth 10 --opcodes "op*"

# Capture a detailed search trace (JSON printed to stdout)
python -m malbolge.cli generate --text "ABC" --seed 42 --trace
```

Tip: use `--log-level INFO` or `--log-level DEBUG` with any CLI command to see structured log output.

### 2. Run Programs

```bash
# Run using opcodes
python -m malbolge.cli run --opcodes "v"

# Run using ASCII Malbolge source
python -m malbolge.cli run --ascii "(=<\`#9]~6ZY32Vx/4Rs+0No-&Jk)\"Fh}|Bcy?"

# Raise the cycle detection cap to track more unique states
python -m malbolge.cli run --opcodes "ioooooo...p<v" --cycle-limit 200000

# Disable cycle detection entirely while investigating infinite loops
python -m malbolge.cli run --opcodes "ioooooo...p<v" --no-cycle-detection
```

Each run prints `cycle_detected=`, `cycle_repeat_length=`, and `cycle_tracking_limited=` so you can tell whether loops were detected, how long the repeat was, and whether the configured limit truncated tracking.

> Interpreter benchmarks now include synthetic `loop_small` (forces repeat length 2) and `loop_limited` (hits the tracking-limit path) cases so telemetry remains easy to validate.

### 3. Benchmark Performance

```bash
# Benchmark interpreter
python -m malbolge.cli bench --module interpreter

# Benchmark generator
python -m malbolge.cli bench --module generator

# Benchmark everything
python -m malbolge.cli bench --module all

# Capture baseline metrics (JSON)
python -m benchmarks.capture_baseline --output benchmarks/baseline.json

# Compare a fresh run against the saved baseline
python -m benchmarks.compare_baseline --candidate benchmarks/latest.json --allow-regression 10

# Summarise the committed baseline for dashboards or quick checks
python -m benchmarks.summarize_baseline --baseline benchmarks/baseline.json

# Render cycle repeat-length histograms from interpreter baselines
python -m benchmarks.cycle_repeat_report --baseline benchmarks/baseline.json

# Generate CI-friendly markdown summary with histogram blocks
python -m benchmarks.render_benchmark_reports --baseline benchmarks/baseline.json --output benchmarks/benchmark_report.md
```

The comparison script prints per-case deltas for fastest and average timings, failing the run when slowdowns exceed the allowed percentage so regressions surface quickly. The summariser produces a concise text snapshot you can drop into dashboards or share in review threads, the cycle report highlights repeat-length distributions, and the Markdown renderer rolls everything into a single artifact. CI publishes `latest.json`, the text summary, the histogram report, and the Markdown bundle for every push.

## Examples and Learning Resources

### Beginner Resources

1. **[Malbolge Primer](docs/MALBOLGE_PRIMER.md)** - Start here! Comprehensive guide covering:

   - What Malbolge is and why it's impossible to program by hand
   - The 8 instructions and how they work
   - Ternary arithmetic and the "crazy operation"
   - Working examples with explanations
   - Links to external resources and papers

1. **[Tutorial](docs/TUTORIAL.md)** - End-to-end CLI workflows:

   - Environment setup
   - Command-line usage patterns
   - Troubleshooting common issues
   - Advanced profiling techniques

### Example Scripts

The `examples/` directory contains working code you can run immediately:

#### Analyze Generated Programs

```bash
python examples/analyze_program.py --text "Hi" --seed 42
```

Generates a program and shows detailed statistics:

- Target string and actual output
- Opcode sequence
- Execution steps and register states
- Memory tape length

#### Profile Generator Performance

```bash
python examples/profile_generator.py --text "Hello" --runs 5
```

Runs multiple generation cycles and reports:

- Average evaluation count
- Cache hit rates
- Branch pruning efficiency (including repeated-state prunes)
- Duration statistics
- Trace length (if `capture_trace` is enabled)

### Interactive Notebook

Explore Malbolge interactively with Jupyter:

```bash
jupyter notebook notebooks/Malbolge_Advanced_Tour.ipynb
```

The notebook includes:

- Step-by-step program generation
- Visual execution tracing
- Heuristic comparison experiments
- Register and memory inspection

## API Documentation

### Running Malbolge Programs

The `MalbolgeInterpreter` executes Malbolge opcodes with configurable limits:

```python
from malbolge import MalbolgeInterpreter

# Create interpreter with memory limits
interpreter = MalbolgeInterpreter(
    allow_memory_expansion=True,  # Allow tape to grow
    memory_limit=59049,            # Max cells (3^10)
    max_steps=100000               # Prevent infinite loops
)

# Execute opcodes
result = interpreter.execute("iooo*p<v", capture_machine=True)

# Inspect results
print(f"Output: {result.output}")           # Text output
print(f"Halted: {result.halted}")           # True if program finished
print(f"Steps: {result.steps}")             # Instructions executed
print(f"Halt reason: {result.halt_reason}") # e.g., "halt_opcode", "end_of_program"
print(f"Halt instruction: {result.halt_metadata.last_instruction}")
print(f"Cycle repeat length: {result.halt_metadata.cycle_repeat_length}")
print(f"Cycle tracking limited: {result.halt_metadata.cycle_tracking_limited}")
print(f"Memory expansions: {result.memory_expansions}")
print(f"Peak tape cells: {result.peak_memory_cells}")
if result.halt_metadata.last_jump_target is not None:
    print(f"Last jump target: {result.halt_metadata.last_jump_target}")
if result.halt_metadata.cycle_detected:
    print("Cycle detected during execution")

# Access machine state (if capture_machine=True)
if result.machine:
    print(f"Register A: {result.machine.a}")
    print(f"Register C: {result.machine.c}")
    print(f"Register D: {result.machine.d}")
    print(f"Tape length: {len(result.machine.tape)}")
```

#### Runtime Exceptions

The interpreter raises specific exceptions for different error conditions:

| Exception                  | Cause                                    | Fix                                       |
| -------------------------- | ---------------------------------------- | ----------------------------------------- |
| `InvalidOpcodeError`       | Opcode not in Malbolge instruction table | Verify program source is valid            |
| `InputUnderflowError`      | `/` instruction with no input buffered   | Provide input or avoid `/` instruction    |
| `StepLimitExceededError`   | Exceeded `max_steps` limit               | Increase limit or check for infinite loop |
| `MemoryLimitExceededError` | Tape growth disabled or limit reached    | Enable expansion or increase limit        |
| `MalbolgeRuntimeError`     | Base class for unexpected runtime faults | Inspect message or diagnostics above      |

Example error handling:

```python
from malbolge import MalbolgeInterpreter, MalbolgeRuntimeError

try:
    result = interpreter.execute("invalid")
except MalbolgeRuntimeError as e:
    print(f"Execution failed: {e}")
```

> **Thread safety:** Interpreters guard execution with an internal re-entrant lock, so sharing one instance across threads is safe but serialized. For throughput, prefer creating a dedicated interpreter per worker.

### Generating Malbolge Programs

The `ProgramGenerator` automatically synthesizes programs using breadth-first search:

```python
from malbolge import GenerationConfig, ProgramGenerator

# Create generator (no configuration needed!)
generator = ProgramGenerator()

# Generate with default settings
result = generator.generate_for_string("Hello")

# Or customize the search algorithm
config = GenerationConfig(
    random_seed=42,          # For reproducible results
    max_search_depth=5,      # Depth before randomization
    opcode_choices="op*",    # Which opcodes to try
    max_program_length=59049 # Safety limit
)
result = generator.generate_for_string("Hello", config=config)

# Inspect the results
print(f"Opcodes: {result.opcodes}")              # Raw opcode string (ends with 'v')
print(f"ASCII: {result.malbolge_program}")       # Printable Malbolge source
print(f"Output: {result.machine_output}")        # What it actually prints
print(f"Target: {result.target}")                # What you requested

# Analyze performance
stats = result.stats
print(f"Evaluations: {stats['evaluations']}")    # Programs tested
print(f"Cache hits: {stats['cache_hits']}")      # Reused snapshots
print(f"Pruned: {stats['pruned']}")              # Dead branches eliminated
print(f"Duration: {stats['duration_ns']/1e6}ms") # Time taken
print(f"Repeated state pruned: {stats['repeated_state_pruned']}")
print(f"Pruned ratio: {stats['pruned_ratio']:.3f}")
print(f"Repeated state ratio: {stats['repeated_state_ratio']:.3f}")
print(f"Trace length: {stats['trace_length']} (events captured)")
```

#### Capture Trace Data for Debugging

Enable tracing to inspect each candidate the generator evaluates:

```python
config = GenerationConfig(random_seed=42, capture_trace=True)
result = generator.generate_for_string("Hi", config=config)

print(f"Trace events: {result.stats['trace_length']}")
print("First event:", result.trace[0])
```

Each trace entry records the candidate suffix, whether it was pruned, and the
reason (`prefix_mismatch`, `repeated_state`, `accepted`, etc.), making it easy to
replay the search.

#### How Generation Works

The generator uses several smart techniques to find working programs efficiently:

1. **Breadth-First Search**: Systematically explores possible programs, like searching every branch of a decision tree
1. **Snapshot Caching**: Remembers previous states to avoid repeating work (like bookmarking your place in a book)
1. **Dead Branch Pruning**: Immediately discards programs that produce wrong output (like throwing out puzzle pieces that don't fit)
1. **Deterministic Search**: Using the same seed always produces the same program (reproducible results for testing)
1. **Depth-Limited Randomization**: Prevents the search from running forever by introducing controlled randomness

**Real Performance Example** (generating the word "Hi"):

```
Evaluations: 6,776 candidate programs tested
Cache hits: 0 (first run, nothing cached)
Pruned: 6,755 dead branches (99.7% eliminated!)
Duration: ~49ms
```

**What this means:** The generator intelligently tested thousands of possibilities but eliminated 99.7% of them immediately because they couldn't possibly work. This is why generation is so fast despite the enormous search space!

## Testing and Development

### Running Tests

The project includes comprehensive test coverage:

```bash
# Run all tests
python -m unittest discover -v

# Run specific test module
python -m unittest tests.test_interpreter -v
python -m unittest tests.test_generator -v
python -m unittest tests.test_encoding -v
```

Test coverage includes:

- Interpreter execution and error handling
- Generator determinism and configuration
- Encoding/normalization round-trips
- CLI command parsing
- Interpreter halt metadata (jump targets, memory diagnostics)
- Generator heuristics (repeated-state pruning, trace capture)
- Encoding helper cache behaviour (LRU) and opcode validation

### Benchmark Baselines

Capture and persist performance telemetry for regression checks:

```bash
python -m benchmarks.capture_baseline --output benchmarks/baseline.json
```

The resulting JSON summarises interpreter cycle/memory metadata and generator
heuristic ratios for each benchmark case.

### Development Setup

```bash
# Install development dependencies
python -m pip install -e .

# Install pre-commit hooks (auto-formatting, linting, type checks)
pre-commit install

# Run code formatter
black .

# Run linters
python -m ruff check .

# Run type checker
python -m mypy malbolge

# Run pre-commit checks manually
pre-commit run --all-files
```

Ruff and mypy respect the settings in `pyproject.toml` and will run automatically
through the configured pre-commit hooks.

### Project Structure

```
MalbolgeGenerator/
├── malbolge/              # Main package
│   ├── __init__.py        # Public API exports
│   ├── interpreter.py     # Execution engine
│   ├── generator.py       # Program synthesis
│   ├── encoding.py        # ASCII ↔ opcode translation
│   ├── utils.py           # Ternary arithmetic
│   ├── cli/               # Command-line interface
│   │   ├── __main__.py    # Module entry point
│   │   └── main.py        # CLI implementation
│   └── advanced/          # Future features
├── examples/              # Runnable example scripts
├── tests/                 # Unit test suite
├── benchmarks/            # Performance benchmarks
├── docs/                  # Documentation
└── notebooks/             # Jupyter tutorials
```

## How It Works

### Architecture Overview

```
User Request: "Generate program for 'Hello'"
        ↓
┌─────────────────────────────────────────┐
│ ProgramGenerator                        │
│ - Breadth-first search                  │
│ - Branch pruning                        │
│ - State caching                         │
└─────────────────┬───────────────────────┘
                  ↓
        ┌─────────────────────┐
        │ MalbolgeInterpreter  │
        │ - Execute opcodes    │
        │ - Track state        │
        │ - Return snapshots   │
        └─────────────────────┘
                  ↓
        Generated Program: "iooo*p<...v"
```

### Generation Algorithm (Simplified for Understanding)

Here's a simplified version of how the generator works - the real version is more sophisticated, but this shows the core idea:

```python
def generate(target):
    # Start with a bootstrap sequence that sets up the Malbolge interpreter
    program = "i" + "o" * 99  # Bootstrap sequence

    # Build the program one character at a time
    for char in target:
        candidates = []

        # Try adding each possible opcode
        for suffix in ["o", "p", "*"]:
            test_program = program + suffix
            output = execute(test_program)

            # Keep programs that produce the right output so far
            if output.startswith(target[:len(char)]):
                candidates.append((suffix, output))
            # If output doesn't match, discard this path (pruning!)

        # Pick the best candidate and continue building
        program += choose_best(candidates)

    return program + "v"  # Add halt instruction to end the program
```

**Note:** The actual algorithm includes many optimizations like caching, depth limits, repeated-state detection, and statistical tracking to make it much faster and more efficient.

## Contributing

Contributions are welcome! Whether you're:

- Improving documentation
- Adding test coverage
- Optimizing the generator
- Creating new examples
- Fixing bugs

Please see the [Agent directory](AGENTS.md) for coding standards and the [project roadmap](PLAN.md) for upcoming milestones.

## License

MIT License - see LICENSE file for details.

Copyright (c) Eli Pinkerton

## Acknowledgments

- **Ben Olmstead**: Creator of Malbolge (1998)
- **Andrew Cooke**: First automated Malbolge program generator (2000)
- **Lou Scheffer**: Comprehensive technical documentation
- **Esoteric Programming Community**: Research and tooling

## External Resources

### Malbolge References

- [Malbolge on Esolang Wiki](https://esolangs.org/wiki/Malbolge) - Comprehensive reference
- [Programming in Malbolge by Lou Scheffer](http://www.lscheffer.com/malbolge.shtml) - Technical deep dive (Note: SSL certificate may be expired, but content is accessible)
- [LMAO Assembler](https://github.com/esoteric-programmer/LMAO) - HeLL to Malbolge compiler
- [Try It Online](https://tio.run/#malbolge) - Run Malbolge in your browser

### Academic Papers

- [Introduction to Esoteric Language Malbolge](https://www.trs.cm.is.nagoya-u.ac.jp/projects/Malbolge/papers/JVSE2010-Malbolge.pdf) - Masahiko Sakai (2010)

### Tutorials

- [Matthias Ernst's Malbolge Tutorial](http://www.matthias-ernst.eu/malbolge/tutorial/01/learning-malbolge.html)
- [Lutter.cc Malbolge Cat Program Tutorial](https://lutter.cc/malbolge/tutorial/cat.html)

## Citation

If you use this project in academic work, please cite:

```bibtex
@software{malbolge_generator,
  author = {Pinkerton, Eli},
  title = {MalbolgeGenerator: Automated Malbolge Program Synthesis},
  year = {2024},
  url = {https://github.com/wallstop/MalbolgeGenerator}
}
```

## Common Issues for Beginners

### Installation Problems

**Issue**: `No module named 'malbolge'`

```bash
# Solution: Install the package in editable mode
python -m pip install -e .
```

**Issue**: `python command not found`

```bash
# Solution: Use python3 on macOS/Linux
python3 -m pip install -e .
```

### Running Commands

**Issue**: Benchmark scripts fail with `ModuleNotFoundError: No module named 'benchmarks'`

```bash
# Solution: Run as a module with -m flag
python -m benchmarks.capture_baseline --output benchmarks/baseline.json
```

**Issue**: Generation is very slow

```bash
# Solution: Try a different seed or reduce search depth
python -m malbolge.cli generate --text "Test" --seed 999
python -m malbolge.cli generate --text "Test" --max-depth 3
```

### Getting Help

Not sure where to start? Follow this path:

1. **Installation Check**: Run `python -c "from malbolge import ProgramGenerator; print('Success!')"`
1. **First Program**: `python -m malbolge.cli generate --text "Hi" --seed 42`
1. **Learn Basics**: Read the [Malbolge Primer](docs/MALBOLGE_PRIMER.md)
1. **Tutorial**: Follow the [Hands-on Tutorial](docs/TUTORIAL.md)
1. **Examples**: Try scripts in `examples/`

## Support

- **Issues**: [GitHub Issues](https://github.com/wallstop/MalbolgeGenerator/issues)
- **Documentation**: Start with the [Malbolge Primer](docs/MALBOLGE_PRIMER.md)

______________________________________________________________________

**Ready to explore the most difficult programming language ever created?** Start with the [Malbolge Primer](docs/MALBOLGE_PRIMER.md) and then try generating your first program!

### Trace Summaries

Inspect pruning reasons quickly using:

```bash
python examples/trace_summary.py --text "Hi" --seed 42 --limit 5
```

This prints combined stats, a reason histogram, and the first N trace events for deeper analysis or regression comparisons.

Need a richer view? Turn the trace into depth/ reason histograms:

```bash
python examples/trace_viz.py --path traces/hello-trace.json
# or stream directly from the generator
python -m malbolge.cli generate --text "Hi" --seed 42 --trace | python examples/trace_viz.py --stdin
```

The visualiser renders per-depth bars, reason counts, and the first few retained candidates so you can spot heuristic bottlenecks at a glance.
