# MalbolgeGenerator

**Automatically generate and execute programs in Malbolge, the most difficult esoteric programming language ever created.**

## What is This?

MalbolgeGenerator is a high-performance Python toolkit that solves an impossible problem: **writing programs in Malbolge**, a programming language so complex that the first "Hello World" program took 2 years and required AI search algorithms to discover.

This project provides:
- **Automatic Program Generation**: Give it text like "Hello", get a working Malbolge program
- **High-Performance Interpreter**: Execute Malbolge programs with full debugging capabilities
- **Clean Python API**: Use it as a library or via command-line tools
- **Educational Resources**: Learn about esoteric languages and automated code synthesis

**New to Malbolge?** Start with our [Malbolge Primer](docs/MALBOLGE_PRIMER.md) to understand what Malbolge is and why this project exists!

## What is Malbolge?

Malbolge (named after the 8th circle of Hell) is an esoteric programming language designed in 1998 to be **as difficult as possible** to program in. It features:
- Self-modifying code that encrypts itself after each instruction
- Base-3 (ternary) arithmetic instead of binary
- Only 8 valid instructions with counter-intuitive behavior
- The "crazy operation" - a ternary logic gate designed to confuse

**Key fact**: Humans don't write Malbolge programs by hand - they use generators like this one!

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
# Clone the repository
git clone https://github.com/yourusername/MalbolgeGenerator.git
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

Generate a program that prints "Hello":

```bash
python -m malbolge.cli generate --text "Hello" --seed 42
```

Output:
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

Run it:
```bash
python -m malbolge.cli run --opcodes "ioooooo...p<v"
```

That's it! You just generated and ran a Malbolge program. No human could write this by hand!

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

**Note**: Legacy scripts can still import `MalbolgeInterpreter.py`; under the hood it proxies to the new package.

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

### 2. Run Programs

```bash
# Run using opcodes
python -m malbolge.cli run --opcodes "v"

# Run using ASCII Malbolge source
python -m malbolge.cli run --ascii "(=<\`#9]~6ZY32Vx/4Rs+0No-&Jk)\"Fh}|Bcy?"
```

### 3. Benchmark Performance

```bash
# Benchmark interpreter
python -m malbolge.cli bench --module interpreter

# Benchmark generator
python -m malbolge.cli bench --module generator

# Benchmark everything
python -m malbolge.cli bench --module all
```

## Examples and Learning Resources

### Beginner Resources

1. **[Malbolge Primer](docs/MALBOLGE_PRIMER.md)** - Start here! Comprehensive guide covering:
   - What Malbolge is and why it's impossible to program by hand
   - The 8 instructions and how they work
   - Ternary arithmetic and the "crazy operation"
   - Working examples with explanations
   - Links to external resources and papers

2. **[Tutorial](docs/TUTORIAL.md)** - End-to-end CLI workflows:
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

| Exception | Cause | Fix |
|-----------|-------|-----|
| `InvalidOpcodeError` | Opcode not in Malbolge instruction table | Verify program source is valid |
| `InputUnderflowError` | `/` instruction with no input buffered | Provide input or avoid `/` instruction |
| `StepLimitExceededError` | Exceeded `max_steps` limit | Increase limit or check for infinite loop |
| `MemoryLimitExceededError` | Tape growth disabled or limit reached | Enable expansion or increase limit |
| `MalbolgeRuntimeError` | Base class for unexpected runtime faults | Inspect message or diagnostics above |

Example error handling:
```python
from malbolge import MalbolgeInterpreter, MalbolgeRuntimeError

try:
    result = interpreter.execute("invalid")
except MalbolgeRuntimeError as e:
    print(f"Execution failed: {e}")
```

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

The generator uses advanced optimization techniques:

1. **Breadth-First Search**: Explores program space systematically
2. **Snapshot Caching**: Reuses interpreter states (avoids re-execution)
3. **Dead Branch Pruning**: Eliminates paths with wrong output immediately
4. **Deterministic Search**: Same seed always produces same program
5. **Depth-Limited Randomization**: Prevents infinite search

**Performance Example** (generating "Hi"):
```
Evaluations: 6,776 candidates tested
Cache hits: 0 (first run, nothing cached)
Pruned: 6,755 dead branches (99.7% eliminated!)
Duration: ~49ms
```

The generator tested thousands of possibilities but pruned 99.7% immediately!

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

### Generation Algorithm (Simplified)

```python
def generate(target):
    program = "i" + "o" * 99  # Bootstrap sequence

    for char in target:
        candidates = []
        for suffix in ["o", "p", "*"]:
            test_program = program + suffix
            output = execute(test_program)

            if output.startswith(target[:len(char)]):
                candidates.append((suffix, output))
            # else: prune this branch (dead end)

        program += choose_best(candidates)

    return program + "v"  # Add halt
```

The real algorithm includes caching, depth limits, and statistical tracking.

## Contributing

Contributions are welcome! Whether you're:
- Improving documentation
- Adding test coverage
- Optimizing the generator
- Creating new examples
- Fixing bugs

Please see [AGENTS.md](AGENTS.md) for coding standards and [PLAN.md](PLAN.md) for the development roadmap.

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
- [Programming in Malbolge by Lou Scheffer](http://www.lscheffer.com/malbolge.shtml) - Technical deep dive
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
  url = {https://github.com/yourusername/MalbolgeGenerator}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/MalbolgeGenerator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/MalbolgeGenerator/discussions)
- **Documentation**: Start with [docs/MALBOLGE_PRIMER.md](docs/MALBOLGE_PRIMER.md)

---

**Ready to explore the most difficult programming language ever created?** Start with the [Malbolge Primer](docs/MALBOLGE_PRIMER.md) and then try generating your first program!
