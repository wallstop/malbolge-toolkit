# Sample Reference Data

This directory contains static reference files that are helpful when working
with Malbolge programs and the generator CLI.

- [ASCII.txt](./ASCII.txt): Printable ASCII table with decimal, hexadecimal,
  and character columns for quick lookups while crafting or inspecting program
  output.
- [OP_CODES.txt](./OP_CODES.txt): Quick reference for the canonical Malbolge
  opcode mnemonics and their decoded behaviours.

These assets pair well with the analysis scripts documented in
[`examples/README.md`](../README.md) and can be supplied to the CLI with the
`--ascii-file` flag when you need to feed a precomputed sequence into the
interpreter.
