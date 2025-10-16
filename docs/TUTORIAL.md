# Malbolge CLI & Toolkit Tutorial

**Complete guide to using MalbolgeGenerator for program synthesis and execution**

## Prerequisites

Before starting, make sure you understand:
- Basic command-line navigation
- Python 3.11+ installed
- Virtual environments (recommended but optional)

**New to Malbolge?** Read [MALBOLGE_PRIMER.md](MALBOLGE_PRIMER.md) first to understand what Malbolge is and why we need automated generation!

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Quick CLI Walkthrough](#2-quick-cli-walkthrough)
3. [Generating Programs](#3-generating-programs)
4. [Running Programs](#4-running-programs)
5. [Analyzing Generated Programs](#5-analyzing-generated-programs)
6. [Performance Profiling](#6-performance-profiling)
7. [Python API Usage](#7-python-api-usage)
8. [Advanced Techniques](#8-advanced-techniques)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Environment Setup

### Step 1: Clone and Navigate

```bash
git clone https://github.com/yourusername/MalbolgeGenerator.git
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
# For pre-commit hooks (auto-formatting)
pre-commit install

# For Jupyter notebooks
pip install jupyter
```

---

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
{'evaluations': 6776, 'cache_hits': 0, 'pruned': 6755, 'duration_ns': 48074500}
```

**What you see:**
1. **Line 1**: Opcodes (the internal representation)
2. **Line 2**: ASCII Malbolge source (printable characters)
3. **Line 3**: Output (what the program prints)
4. **Line 4**: Statistics (how it was generated)

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
tape_length=218
```

Congratulations! You just generated and executed your first Malbolge program!

---

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
```

**Parameters explained:**
- `--max-depth N`: How many levels to explore before randomizing (default: 5)
- `--opcodes STR`: Which opcodes to try during search (default: "op*")

### Saving Output

```bash
# Save to file (PowerShell)
python -m malbolge.cli generate --text "Hello" --seed 42 > hello.txt

# On Unix systems
python -m malbolge.cli generate --text "Hello" --seed 42 | tee hello.txt
```

---

## 4. Running Programs

### Run from Opcodes

```bash
# Simple halt program
python -m malbolge.cli run --opcodes "v"

# Generated program (paste opcodes)
python -m malbolge.cli run --opcodes "iooo*p<v"
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
tape_length=59049
```

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

---

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

---

## 6. Performance Profiling

### Using profile_generator.py

Measure generator performance across multiple runs:

```bash
python examples/profile_generator.py --text "Hello" --runs 5
```

**Output:**
```
[run 1] duration=0.087362s evaluations=12453 cache_hits=0 pruned=12412
[run 2] duration=0.089104s evaluations=12453 cache_hits=0 pruned=12412
[run 3] duration=0.086891s evaluations=12453 cache_hits=0 pruned=12412
[run 4] duration=0.088532s evaluations=12453 cache_hits=0 pruned=12412
[run 5] duration=0.087745s evaluations=12453 cache_hits=0 pruned=12412

=== Summary ===
Target: 'Hello'
Runs: 5
Duration fastest: 0.086891s  average: 0.087927s
Evaluations avg: 12453.00
Cache hits avg: 0.00
Pruned avg: 12412.00
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

---

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

---

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

---

## 9. Troubleshooting

### Common Issues and Solutions

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| `No module named 'malbolge'` | Package not installed | Run `python -m pip install -e .` |
| `'malbolge.cli' is a package and cannot be directly executed` | Missing `__main__.py` | Use `python -m malbolge.cli.main` or check repo for updates |
| `[error] Encountered invalid opcode` | Invalid ASCII source | Use `--opcodes` instead of `--ascii`, or verify source |
| `[error] Input instruction encountered with empty buffer` | Program uses `/` (input) | Generated programs shouldn't need input; check source |
| `Halt reason: memory_limit_exceeded` | Memory expansion disabled | Not typically an issue with generated programs; check interpreter config |
| `Generation very slow` | Complex target or deep search | Use smaller `--max-depth`, try different `--seed` |
| `Different output each run` | No seed specified | Add `--seed` parameter for deterministic results |
| `Black formatting failures` | Code not formatted (dev only) | Run `black .` or `pre-commit run --all-files` |

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
config = GenerationConfig(random_seed=42)

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
```

### Getting Help

1. **Check documentation**:
   - [MALBOLGE_PRIMER.md](MALBOLGE_PRIMER.md) - Language basics
   - [README.md](../README.md) - API reference
   - [AGENTS.md](../AGENTS.md) - Development guidelines

2. **Run examples**:
   ```bash
   python examples/analyze_program.py --text "Test"
   python examples/profile_generator.py --text "Test" --runs 3
   ```

3. **Test installation**:
   ```bash
   python -m unittest discover -v
   ```

4. **Check GitHub Issues**: [github.com/yourusername/MalbolgeGenerator/issues](https://github.com/yourusername/MalbolgeGenerator/issues)

---

## Next Steps

1. **Experiment**: Try generating programs for different strings
2. **Analyze**: Use `examples/analyze_program.py` to understand execution
3. **Profile**: Measure performance with `examples/profile_generator.py`
4. **Explore**: Open `notebooks/Malbolge_Advanced_Tour.ipynb` for interactive learning
5. **Learn**: Read [MALBOLGE_PRIMER.md](MALBOLGE_PRIMER.md) for deep understanding

---

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

---

**Happy Malbolge programming!** Remember: if you can generate it, you've accomplished what most humans can't do by hand! 🎉
