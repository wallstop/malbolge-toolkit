# Examples

This directory contains runnable scripts that demonstrate common workflows with the modular `malbolge` package.

## analyze_program.py

```
python examples/analyze_program.py --text "Hi"
```

Generates a Malbolge program for the given text, executes it, and prints execution statistics (halt reason, steps, tape length) alongside generation profiling data.

## profile_generator.py

```
python examples/profile_generator.py --text "Hello" --runs 5
```

Warms up the generator, times repeated runs, and reports aggregated statistics (evaluations, cache hits, pruned states). Useful for tuning heuristics or validating performance improvements.

## debug_generation.py

```
python examples/debug_generation.py --text "Hi" --seed 42 --trace-limit 10
```

Captures a full generator trace alongside interpreter diagnostics. Each trace
event is printed as JSON (reason, candidate, cache usage). Handy for debugging
stubborn targets or analyzing search heuristics.

## samples/

Static reference data lives under [`examples/samples/`](./samples). It currently
contains:

- [`ASCII.txt`](./samples/ASCII.txt) — printable ASCII table for quickly mapping characters to numeric codes.
- [`OP_CODES.txt`](./samples/OP_CODES.txt) — opcode cheat sheet that pairs well with the interpreter analyzer scripts.

Feel free to add more scripts here as new features land. Keep example outputs deterministic by seeding through `GenerationConfig(random_seed=...)`.

## trace_summary.py

```
python examples/trace_summary.py --text "Hi" --seed 42 --limit 5
```

Generates a summary of trace reasons and prints the first N trace events. Useful for comparing heuristic behaviour across seeds or configurations.

## trace_viz.py

```
python examples/trace_viz.py --path traces/hello-trace.json
# or stream directly from the generator
python -m malbolge.cli generate --text "Hi" --seed 42 --trace | python examples/trace_viz.py --stdin
```

Transforms saved trace output into per-depth histograms and reason breakdowns, highlighting the first few retained candidates so you can spot heuristic bottlenecks quickly.
