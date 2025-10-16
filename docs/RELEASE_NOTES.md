# Release Notes

## 2024-09-Restructure — Modular Package Migration

We reorganised the public API into the `malbolge/` package so the interpreter, generator, and helpers ship as a cohesive Python package. The legacy `MalbolgeInterpreter.py` entry point has been removed during this refactor.

- **New imports:** Replace `from MalbolgeInterpreter import ...` with `from malbolge import MalbolgeInterpreter, ProgramGenerator, GenerationConfig`. The package re-exports interpreter types, generator utilities, and encoding helpers for convenience.
- **CLI usage:** Invoke tooling through the module namespace (`python -m malbolge.cli ...`) instead of calling files inside the repository root.
- **Examples and notebooks:** Update any `%run MalbolgeInterpreter.py` or relative imports to point at the `malbolge` package. All bundled documentation and examples have been migrated and can be used as references.
- **Compatibility shims:** The legacy shim previously located at the repository root is no longer published. Downstream projects should depend on the package layout introduced in this release.
- **Cycle detection controls:** The `run` command now accepts `--cycle-limit N` to raise or lower tracking bounds and `--no-cycle-detection` to disable loop tracking outright. CLI output now always reports `cycle_detected`, `cycle_repeat_length`, and `cycle_tracking_limited` to surface the interpreter's diagnostics.
- **Thread safety improvements:** `MalbolgeInterpreter` now serializes access with an internal re-entrant lock; concurrent calls reuse the same machine safely, while still encouraging per-thread instances for maximum throughput.
- **Benchmark comparisons:** The committed `benchmarks/baseline.json` stores reference metrics. Use `benchmarks/compare_baseline.py` to diff new captures against it, surfacing fastest/average timing deltas and enforcing regression budgets in CI.
- **Baseline summaries:** Run `benchmarks/summarize_baseline.py` to dump a compact text summary suitable for dashboards or change discussions.
- **Cycle repeat histograms:** `benchmarks/cycle_repeat_report.py` renders ASCII histograms of repeat-length telemetry so cycle diagnostics are easy to review, and CI attaches the generated summary/histogram artifacts to every run. The interpreter benchmark suite now includes a synthetic `loop_small` case that forces a repeat length of two, keeping the histogram meaningful. `benchmarks/render_benchmark_reports.py` also produces a Markdown bundle combining summary and histogram outputs for dashboards.

Refer to `AGENTS.md` and `docs/TUTORIAL.md` for the latest development workflow, testing commands, and deep dives into the CLI and API surface.
