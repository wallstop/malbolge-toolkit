# Examples

**Welcome!** This directory contains ready-to-run example scripts that show you how to use MalbolgeGenerator. Each script demonstrates a specific feature or workflow, with clear output so you can see what's happening.

**Complete Beginner?** Start with `analyze_program.py` - it's the simplest and shows you the basics of generating and running Malbolge programs.

All examples use the modular `malbolge` package and work right out of the box after installation.

## analyze_program.py

**What it does:** Generates a Malbolge program for any text you provide, runs it, and shows you detailed statistics about both the generation process and execution.

**Perfect for:** Beginners wanting to see how generation works and what statistics mean.

```bash
python examples/analyze_program.py --text "Hi"
```

**Output includes:**

- The generated opcodes and ASCII source
- How long generation took and how many candidates were tested
- How the program executed (steps, memory usage, register values)
- Easy-to-read statistics explaining what happened

## profile_generator.py

**What it does:** Runs the generator multiple times on the same text and reports performance statistics. Great for seeing how consistent the generator is and identifying performance patterns.

**Perfect for:** Understanding generator performance or comparing different seeds/settings.

```bash
python examples/profile_generator.py --text "Hello" --runs 5
```

**Output includes:**

- Timing for each run (fastest, average, slowest)
- Aggregated statistics (evaluations, cache hits, pruned states)
- Performance consistency across multiple runs
- Useful for validating optimizations or tuning heuristics

## debug_generation.py

**What it does:** Captures a detailed trace of the generation process, showing every candidate program that was considered and why it was kept or discarded.

**Perfect for:** Advanced users debugging tricky generation cases or analyzing search heuristics.

```bash
python examples/debug_generation.py --text "Hi" --seed 42 --trace-limit 10
```

**Output includes:**

- Full trace of the search process (JSON format)
- Why each candidate was accepted or rejected
- Cache usage patterns
- Deep insights into the generation algorithm's decisions

## samples/

Sample Malbolge programs live under [`examples/samples/`](./samples). It currently
contains:

- [PROGRAM_ASCII.txt](./samples/PROGRAM_ASCII.txt): A generated Malbolge program that prints "Hello", as its raw ASCII source.
- [PROGRAM_OP_CODES.txt](./samples/PROGRAM_OP_CODES.txt): A generated Malbolge program that prints "Hello", as the Malbolge's interpreter's op codes.

Feel free to add more scripts here as new features land. Keep example outputs deterministic by seeding through `GenerationConfig(random_seed=...)`.

## trace_summary.py

**What it does:** Analyzes the generation trace and produces a human-readable summary showing why candidates were accepted or rejected.

**Perfect for:** Comparing how different seeds or configurations affect the search process.

```bash
python examples/trace_summary.py --text "Hi" --seed 42 --limit 5
```

**Output includes:**

- Count of each pruning reason (prefix mismatch, repeated state, etc.)
- The first N trace events for detailed inspection
- Useful for understanding search behavior across different configurations

## trace_viz.py

**What it does:** Creates visual histograms and breakdowns from trace data, making it easy to spot patterns and bottlenecks in the search algorithm.

**Perfect for:** Advanced analysis of generator behavior and optimization opportunities.

```bash
python examples/trace_viz.py --path traces/hello-trace.json
# or stream directly from the generator
python -m malbolge.cli generate --text "Hi" --seed 42 --trace | python examples/trace_viz.py --stdin
```

**Output includes:**

- Per-depth histograms showing search activity at each level
- Breakdown of pruning reasons
- First few retained candidates for context
- Quick identification of heuristic bottlenecks
