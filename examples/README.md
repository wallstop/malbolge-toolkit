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

Feel free to add more scripts here as new features land. Keep example outputs deterministic by seeding through `GenerationConfig(random_seed=...)`.
