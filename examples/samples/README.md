# Sample Reference Data

This directory contains static reference files that are helpful when working
with Malbolge programs and the generator CLI.

- [ASCII.txt](./ASCII.txt): A generated Malbolge program that outputs the printable
  ASCII character set. Useful for understanding character encodings and as a test program.
- [OP_CODES.txt](./OP_CODES.txt): A generated Malbolge program demonstrating various
  opcode sequences. Use this as a sample program for testing the interpreter.

These sample programs pair well with the analysis scripts documented in
[`examples/README.md`](../README.md) and can be supplied to the CLI with the
`--ascii-file` flag when you need to test precomputed Malbolge programs.
