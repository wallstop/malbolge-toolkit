# Malbolge CLI & Toolkit Tutorial

**Complete guide to using MalbolgeGenerator for program synthesis and execution**

## Prerequisites

Before starting, make sure you understand:

- Basic command-line navigation
- Python 3.11+ installed
- Virtual environments (recommended but optional)

**New to Malbolge?** Read the [Malbolge Primer](MALBOLGE_PRIMER.md) first to understand what Malbolge is and why we need automated generation!

**Migrating from earlier releases?** Imports now flow through the modular `malbolge` package. See the [release notes](RELEASE_NOTES.md) for a quick checklist covering the retirement of `MalbolgeInterpreter.py`, new CLI entry points, and other breaking changes.

______________________________________________________________________

## Table of Contents

1. [Environment Setup](#1-environment-setup)
1. [Quick CLI Walkthrough](#2-quick-cli-walkthrough)
1. [Generating Programs](#3-generating-programs)
1. [Running Programs](#4-running-programs)
1. [Analyzing Generated Programs](#5-analyzing-generated-programs)
1. [Performance Profiling](#6-performance-profiling)
1. [Python API Usage](#7-python-api-usage)
1. [Advanced Techniques](#8-advanced-techniques)
1. [Troubleshooting](#9-troubleshooting)

______________________________________________________________________

## 1. Environment Setup

### Step 1: Clone and Navigate

```bash
# Clone the repository (use your fork instead of wallstop if applicable)
git clone https://github.com/wallstop/MalbolgeGenerator.git
cd MalbolgeGenerator
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Verify activation:**
Your prompt should show `(.venv)` at the beginning.

### Step 3: Install Package

```bash
# Install in editable mode (recommended for development)
python -m pip install -e .

# Verify installation
python -c "from malbolge import ProgramGenerator; print('Success!')"
```

### Step 4: Install Development Tools (Optional)

```bash
# For pre-commit hooks (formatting, linting, typing)
pre-commit install

# Run linting and type checks manually
python -m ruff check .
python -m mypy malbolge

# For Jupyter notebooks
pip install jupyter
```

______________________________________________________________________

## 2. Quick CLI Walkthrough

### Your First Generation (2 minutes)

Generate a program that prints "Hi":

```bash
python -m malbolge.cli generate --text "Hi" --seed 42
```

**Output:**

```
ioooooooooooo...***pppopop<v
bCBA@?>=<;:98...srq)(',%*#G4
Hi
{
    'evaluations': 6776,
    'cache_hits': 0,
    'pruned': 6755,
    'repeated_state_pruned': 318,
    'duration_ns': 48074500,
    'trace_length': 0
}
```

**What you see:**

1. **Line 1**: Opcodes (the internal representation)
1. **Line 2**: ASCII Malbolge source (printable characters)
1. **Line 3**: Output (what the program prints)
1. **Line 4**: Statistics (how it was generated)
1. **Lines 5-8**: Interpreter diagnostics (halt reason, last instruction, memory growth)

> Tip: Pass `--log-level INFO` (or DEBUG) to CLI commands to stream diagnostics while troubleshooting.

### Run the Program

Copy the opcodes from line 1 and run:

```bash
python -m malbolge.cli run --opcodes "ioooooooooooo...***pppopop<v"
```

Need to run a saved ASCII source that includes quotes or other shell-sensitive characters? Use the file shortcut:

```bash
python -m malbolge.cli run --ascii-file path/to/program.mal
```

**Output:**

```
Hi
halt_reason=halt_opcode
steps=120
halt_instruction=v
cycle_detected=False
cycle_repeat_length=None
cycle_tracking_limited=False
memory_expansions=0
peak_tape_cells=218
tape_length=218
```

Congratulations! You just generated and executed your first Malbolge program!

The additional diagnostics indicate which opcode halted execution, whether any
memory expansion occurred, and the peak tape size. These values are mirrored in
the Python API via `ExecutionResult.halt_metadata`, `memory_expansions`, and
`peak_memory_cells`. The `cycle_detected` flag exposes loop discovery, `cycle_repeat_length`
reports the number of steps between repeated states, and `cycle_tracking_limited` shows when cycle
detection sampling reached its limit (tune via `MalbolgeInterpreter(..., cycle_detection_limit=...)`).

______________________________________________________________________

## 3. Generating Programs

### Basic Generation

```bash
# Simple string
python -m malbolge.cli generate --text "Hello"

# Single character
python -m malbolge.cli generate --text "A"

# Multiple words (use quotes!)
python -m malbolge.cli generate --text "Hello World"
```

### Deterministic Generation (Reproducibility)

Use `--seed` to get the same program every time:

```bash
# Same seed = same program
python -m malbolge.cli generate --text "Test" --seed 12345
python -m malbolge.cli generate --text "Test" --seed 12345  # Identical output

# Different seed = different program (but same output!)
python -m malbolge.cli generate --text "Test" --seed 99999
```

**Why use seeds?**

- **Reproducible research**: Share seeds with collaborators
- **Testing**: Verify bug fixes produce identical results
- **Comparison**: Test different generator optimizations

### Tuning Search Parameters

Control how the generator explores the program space:

```bash
# Default settings (good balance)
python -m malbolge.cli generate --text "ABC"

# More thorough search (slower but may find shorter programs)
python -m malbolge.cli generate --text "ABC" --max-depth 10

# Faster search (less exploration)
python -m malbolge.cli generate --text "ABC" --max-depth 3

# Change opcode choices (default is "op*")
python -m malbolge.cli generate --text "ABC" --opcodes "o*"  # Only use 'o' and '*'
python -m malbolge.cli generate --text "ABC" --seed 42 --trace  # Emit JSON trace for debugging
```

**Parameters explained:**

- `--max-depth N`: How many levels to explore before randomizing (default: 5)
- `--opcodes STR`: Which opcodes to try during search (default: "op\*")
- `--trace`: Print a JSON array of trace events (also sets `trace_length`) and a summary of reasons.

### Saving Output

```bash
# Save to file (PowerShell)
python -m malbolge.cli generate --text "Hello" --seed 42 > hello.txt

# On Unix systems
python -m malbolge.cli generate --text "Hello" --seed 42 | tee hello.txt
```

______________________________________________________________________

## 4. Running Programs

### Run from Opcodes

```bash
# Simple halt program
python -m malbolge.cli run --opcodes "v"

# Generated program (paste opcodes)
python -m malbolge.cli run --opcodes "iooo*p<v"

# Track up to 250k unique states when checking for loops
python -m malbolge.cli run --opcodes "iooo*p<v" --cycle-limit 250000

# Disable cycle detection entirely while inspecting infinite loops
python -m malbolge.cli run --opcodes "iooo*p<v" --no-cycle-detection
```

### Run from ASCII Source

Use the classic "Hello World" Malbolge program:

```bash
python -m malbolge.cli run --ascii "(=<\`#9]~6ZY32Vx/4Rs+0No-&Jk)\"Fh}|Bcy?\`=*z]Kw%oG4UUS0/@-ejc(:'8dc"
```

**Output:**

```
Hello World!
halt_reason=end_of_program
steps=104572
cycle_detected=False
cycle_repeat_length=None
cycle_tracking_limited=False
tape_length=59049
```

The cycle tracking fields indicate whether the interpreter detected a loop or hit the configured tracking limit.

### Run from File

**PowerShell:**

```powershell
# Extract opcodes from generation output (first line)
$opcodes = (Get-Content hello.txt | Select-Object -First 1)
python -m malbolge.cli run --opcodes "$opcodes"
```

**Unix:**

```bash
# Extract opcodes (first line of file)
opcodes=$(head -n 1 hello.txt)
python -m malbolge.cli run --opcodes "$opcodes"
```

______________________________________________________________________

## 5. Analyzing Generated Programs

### Using analyze_program.py

Get detailed insights into program execution:

```bash
python examples/analyze_program.py --text "Hi" --seed 42
```

**Output:**

```
=== Generation ===
Target: Hi
Opcodes: iooooooo...pppopop<v
Output: Hi
Stats:
{'cache_hits': 0,
 'duration_ns': 49311500,
 'evaluations': 6776,
 'pruned': 6755}

=== Execution ===
Stdout: Hi
Halt reason: halt_opcode
Steps: 120
Tape length: 218
Register A: 29545
Register C: 218
Register D: 120
```

**Understanding the output:**

**Generation Stats:**

- `evaluations`: How many candidate programs were tested (6,776)
- `cache_hits`: Reused machine snapshots (0 on first run)
- `pruned`: Dead branches eliminated (6,755 - that's 99.7%!)
- `repeated_state_pruned`: Branches skipped due to repeated machine signatures
- `trace_length`: Number of trace events captured (0 unless tracing is enabled)
- `duration_ns`: Time taken in nanoseconds (~49ms)

**Execution Stats:**

- `steps`: Instructions executed (120)
- `tape_length`: Memory used (218 cells)
- `Register A/C/D`: Final register values

### Customizing Analysis

```bash
# Different target string
python examples/analyze_program.py --text "Hello World" --seed 100

# Change search parameters
python examples/analyze_program.py --text "Test" --max-depth 10 --opcodes "op"
```

______________________________________________________________________

## 6. Performance Profiling

### Using profile_generator.py

Measure generator performance across multiple runs:

```bash
python examples/profile_generator.py --text "Hello" --runs 5
```

**Output:**

```
[run 1] duration=0.087362s evaluations=12453 cache_hits=0 pruned=12412 repeated_pruned=412
[run 2] duration=0.089104s evaluations=12453 cache_hits=0 pruned=12412 repeated_pruned=409
[run 3] duration=0.086891s evaluations=12453 cache_hits=0 pruned=12412 repeated_pruned=410
[run 4] duration=0.088532s evaluations=12453 cache_hits=0 pruned=12412 repeated_pruned=408
[run 5] duration=0.087745s evaluations=12453 cache_hits=0 pruned=12412 repeated_pruned=411

=== Summary ===
Target: 'Hello'
Runs: 5
Duration fastest: 0.086891s  average: 0.087927s
Evaluations avg: 12453.00
Cache hits avg: 0.00
Pruned avg: 12412.00
Repeated pruned avg: 410.00
```

### Benchmarking Built-in Modules

```bash
# Benchmark interpreter only
python -m malbolge.cli bench --module interpreter

# Benchmark generator only
python -m malbolge.cli bench --module generator

# Benchmark everything
python -m malbolge.cli bench --module all
```

### Capture Baseline JSON

Snapshot interpreter and generator telemetry for regression tracking:

```bash
python -m benchmarks.capture_baseline --output benchmarks/baseline.json
```

The JSON output records cycle detection metadata, memory growth, and generator
heuristic ratios so you can diff performance over time.

Compare a fresh run against the baseline with:

```bash
python -m benchmarks.compare_baseline --candidate benchmarks/latest.json --allow-regression 10

python -m benchmarks.summarize_baseline --baseline benchmarks/baseline.json

python -m benchmarks.cycle_repeat_report --baseline benchmarks/baseline.json
```

The comparison script prints per-case deltas for fastest/average timings and exits with an error when slowdowns exceed the permitted percentage so regressions stand out immediately. The summariser produces a concise text snapshot for dashboards or review notes, the cycle report visualises repeat-length distributions captured during interpreter runs, and the Markdown renderer bundles everything together. Continuous integration uploads the JSON, summary, histogram, and Markdown report so you can inspect performance from any successful build. Interpreter benchmarks include synthetic `loop_small` (repeat length 2) and `loop_limited` (tracking limit reached) cases so histogram trends remain easy to spot.

______________________________________________________________________

## 7. Python API Usage

### Basic Program Generation

```python
from malbolge import ProgramGenerator

# Create generator
generator = ProgramGenerator()

# Generate program
result = generator.generate_for_string("Hello")

# Access results
print(f"Opcodes: {result.opcodes}")
print(f"Output: {result.machine_output}")
print(f"Stats: {result.stats}")
```

### Configured Generation

```python
from malbolge import ProgramGenerator, GenerationConfig

generator = ProgramGenerator()

# Create configuration
config = GenerationConfig(
    random_seed=42,              # Deterministic results
    max_search_depth=5,          # Depth before randomization
    opcode_choices="op*",        # Opcodes to try
    max_program_length=59049     # Safety limit
)

# Generate with config
result = generator.generate_for_string("Test", config=config)

# Analyze performance
stats = result.stats
efficiency = (stats['pruned'] / stats['evaluations'] * 100)
print(f"Pruning efficiency: {efficiency:.1f}%")
```

### Running Programs

```python
from malbolge import MalbolgeInterpreter

# Create interpreter
interpreter = MalbolgeInterpreter(
    allow_memory_expansion=True,
    memory_limit=59049,
    max_steps=1000000
)

# Execute program
result = interpreter.execute("v", capture_machine=True)

# Check results
if result.halted:
    print(f"Program output: {result.output}")
    print(f"Executed {result.steps} steps")
    print(f"Halt reason: {result.halt_reason}")

    if result.machine:
        print(f"Final A register: {result.machine.a}")
        print(f"Memory usage: {len(result.machine.tape)} cells")
```

### Error Handling

```python
from malbolge import (
    MalbolgeInterpreter,
    MalbolgeRuntimeError,
    InvalidOpcodeError,
    StepLimitExceededError
)

interpreter = MalbolgeInterpreter(max_steps=100)

try:
    result = interpreter.execute("ooooooooo...")  # Very long program
except StepLimitExceededError:
    print("Program took too many steps (possible infinite loop)")
except InvalidOpcodeError as e:
    print(f"Invalid opcode encountered: {e}")
except MalbolgeRuntimeError as e:
    print(f"Runtime error: {e}")
```

### End-to-End Workflow

```python
from malbolge import ProgramGenerator, MalbolgeInterpreter, GenerationConfig

# Configure
config = GenerationConfig(random_seed=42, max_search_depth=5)

# Generate
generator = ProgramGenerator()
gen_result = generator.generate_for_string("Hi", config=config)

print(f"Generated in {gen_result.stats['duration_ns']/1e6:.2f}ms")
print(f"Tested {gen_result.stats['evaluations']} candidates")
print(f"Pruned {gen_result.stats['pruned']} dead branches")

# Verify by executing
interpreter = MalbolgeInterpreter()
exec_result = interpreter.execute(gen_result.opcodes)

assert exec_result.output == "Hi", "Output mismatch!"
assert exec_result.halted, "Program didn't halt!"

print("✓ Program verified successfully!")
```

______________________________________________________________________

## 8. Advanced Techniques

### Comparing Different Seeds

Find the "best" program for a target:

```python
from malbolge import ProgramGenerator, GenerationConfig

generator = ProgramGenerator()
target = "Test"

results = []
for seed in range(10):
    config = GenerationConfig(random_seed=seed)
    result = generator.generate_for_string(target, config=config)
    results.append({
        'seed': seed,
        'length': len(result.opcodes),
        'evaluations': result.stats['evaluations'],
        'duration': result.stats['duration_ns']
    })

# Find shortest program
shortest = min(results, key=lambda r: r['length'])
print(f"Shortest program: seed={shortest['seed']}, length={shortest['length']}")

# Find fastest generation
fastest = min(results, key=lambda r: r['duration'])
print(f"Fastest generation: seed={fastest['seed']}, time={fastest['duration']/1e6:.2f}ms")
```

### Resuming from Snapshots

```python
from malbolge import MalbolgeInterpreter

interpreter = MalbolgeInterpreter()

# Execute and capture state
result1 = interpreter.execute("iooo*p", capture_machine=True)
snapshot = result1.machine

# Continue from snapshot
result2 = interpreter.execute_from_snapshot(snapshot, "o*<v")

print(f"Combined output: {result2.output}")
```

### Custom Opcode Exploration

```python
from malbolge import ProgramGenerator, GenerationConfig

generator = ProgramGenerator()

# Try different opcode combinations
configs = [
    ("op*", "All three opcodes"),
    ("op", "Only o and p"),
    ("o*", "Only o and *"),
    ("p*", "Only p and *"),
]

for opcodes, desc in configs:
    config = GenerationConfig(opcode_choices=opcodes, random_seed=42)
    result = generator.generate_for_string("A", config=config)

    print(f"{desc}: {len(result.opcodes)} opcodes, "
          f"{result.stats['evaluations']} evaluations")
```

______________________________________________________________________

## 9. Troubleshooting

### Common Issues and Solutions

| Symptom                                                       | Likely Cause                  | Solution                                                                 |
| ------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------ |
| `No module named 'malbolge'`                                  | Package not installed         | Run `python -m pip install -e .`                                         |
| `'malbolge.cli' is a package and cannot be directly executed` | Missing `__main__.py`         | Use `python -m malbolge.cli.main` or check repo for updates              |
| `[error] Encountered invalid opcode`                          | Invalid ASCII source          | Use `--opcodes` instead of `--ascii`, or verify source                   |
| `[error] Input instruction encountered with empty buffer`     | Program uses `/` (input)      | Generated programs shouldn't need input; check source                    |
| `Halt reason: memory_limit_exceeded`                          | Memory expansion disabled     | Not typically an issue with generated programs; check interpreter config |
| `Generation very slow`                                        | Complex target or deep search | Use smaller `--max-depth`, try different `--seed`                        |
| `Different output each run`                                   | No seed specified             | Add `--seed` parameter for deterministic results                         |
| `Black formatting failures`                                   | Code not formatted (dev only) | Run `black .` or `pre-commit run --all-files`                            |

### Debugging Generation Issues

**Problem: Generation takes too long**

```bash
# Try different seed
python -m malbolge.cli generate --text "Problem" --seed 999

# Reduce search depth
python -m malbolge.cli generate --text "Problem" --max-depth 3

# Try simpler target first
python -m malbolge.cli generate --text "Hi" --seed 42
```

**Problem: Want to understand what generator is doing**

```python
from malbolge import ProgramGenerator, GenerationConfig

generator = ProgramGenerator()
config = GenerationConfig(random_seed=42, capture_trace=True)

result = generator.generate_for_string("A", config=config)

# Analyze search efficiency
stats = result.stats
total = stats['evaluations']
pruned = stats['pruned']
kept = total - pruned

print(f"Total candidates: {total}")
print(f"Kept: {kept} ({kept/total*100:.1f}%)")
print(f"Pruned: {pruned} ({pruned/total*100:.1f}%)")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Repeated state pruned: {stats['repeated_state_pruned']}")
print(f"Trace length: {stats['trace_length']}")

if result.trace:
    print("First trace event:", result.trace[0])
```

### Getting Help

1. **Check documentation**:

   - [Malbolge Primer](MALBOLGE_PRIMER.md) - Language basics
   - [README.md](../README.md) - API reference
   - [AGENTS.md](../AGENTS.md) - Development guidelines

1. **Run examples**:

   ```bash
   python examples/analyze_program.py --text "Test"
   python examples/profile_generator.py --text "Test" --runs 3
   ```

1. **Test installation**:

   ```bash
   python -m unittest discover -v
   ```

1. **Check GitHub Issues**: [GitHub Issues](https://github.com/wallstop/MalbolgeGenerator/issues)

______________________________________________________________________

## Next Steps

1. **Experiment**: Try generating programs for different strings
1. **Analyze**: Use `examples/analyze_program.py` to understand execution
1. **Profile**: Measure performance with `examples/profile_generator.py`
1. **Explore**: Open `notebooks/Malbolge_Advanced_Tour.ipynb` for interactive learning
1. **Learn**: Read the [Malbolge Primer](MALBOLGE_PRIMER.md) for deep understanding

______________________________________________________________________

## Quick Reference

### Essential Commands

```bash
# Generate program
python -m malbolge.cli generate --text "Hello" --seed 42

# Run program
python -m malbolge.cli run --opcodes "v"
python -m malbolge.cli run --ascii "(malbolge source)"
python -m malbolge.cli run --ascii-file path/to/program.mal

# Analyze program
python examples/analyze_program.py --text "Hi" --seed 42

# Profile generator
python examples/profile_generator.py --text "Test" --runs 5

# Run tests
python -m unittest discover -v

# Benchmark
python -m malbolge.cli bench --module all
```

### Python API Quick Reference

```python
# Generation
from malbolge import ProgramGenerator, GenerationConfig
generator = ProgramGenerator()
config = GenerationConfig(random_seed=42)
result = generator.generate_for_string("Text", config=config)

# Execution
from malbolge import MalbolgeInterpreter
interpreter = MalbolgeInterpreter()
result = interpreter.execute("opcodes", capture_machine=True)

# Error handling
from malbolge import MalbolgeRuntimeError
try:
    result = interpreter.execute("opcodes")
except MalbolgeRuntimeError as e:
    print(f"Error: {e}")
```

______________________________________________________________________

## Appendix: Sample Malbolge Programs

The repository ships with ready-made sample programs under
[`examples/samples/`](../examples/samples):

- [PROGRAM_ASCII.txt](../examples/samples/PROGRAM_ASCII.txt): A generated Malbolge program that prints "Hello", as its raw ASCII source.
- [PROGRAM_OP_CODES.txt](../examples/samples/PROGRAM_OP_CODES.txt): A generated Malbolge program that prints "Hello", as the Malbolge's interpreter's op codes.

Use these files as test programs when experimenting with the interpreter via `--ascii-file`:

```bash
python -m malbolge.cli run --ascii-file examples/samples/PROGRAM_ASCII.txt
```

or

```bash
python -m malbolge.cli run --opcodes-file examples/samples/PROGRAM_OP_CODES.txt
```

______________________________________________________________________

**Happy Malbolge programming!** Remember: if you can generate it, you've accomplished what most humans can't do by hand! 🎉

### Visualising Trace Summaries

Trace summaries help identify why candidates are pruned. Generate a summary with:

```bash
python examples/trace_summary.py --text "Hi" --seed 42 --limit 5
```

The script prints aggregated reason counts and the first N events so you can compare heuristics across seeds or configuration tweaks.

For a deeper dive, transform the trace into per-depth histograms:

```bash
python examples/trace_viz.py --path traces/hello-trace.json
# or stream directly from a generator run
python -m malbolge.cli generate --text "Hi" --seed 42 --trace | python examples/trace_viz.py --stdin
```

The visualiser highlights depth hotspots, reason frequencies, and the first few surviving candidates to guide further heuristic tuning.
