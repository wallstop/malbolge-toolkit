# Sample Malbolge Programs

**Welcome!** This directory contains pre-generated Malbolge programs that you can use for testing, learning, or experimentation.

**Why are these useful?** Since Malbolge programs are impossible to write by hand, having working examples is helpful for:

- Testing the interpreter without generating new programs
- Learning what valid Malbolge programs look like
- Quick experimentation without waiting for generation
- Comparing against your own generated programs

## What's Inside

- **[ASCII.txt](./ASCII.txt)**: A generated Malbolge program that prints the printable ASCII character set

  - Great for understanding character encoding
  - Useful as a comprehensive test program

- **[OP_CODES.txt](./OP_CODES.txt)**: A generated Malbolge program demonstrating various opcode sequences

  - Shows different instruction patterns
  - Perfect for testing the interpreter's functionality

## How to Use These

Run them directly with the CLI:

```bash
# Run the ASCII program
python -m malbolge.cli run --ascii-file examples/samples/ASCII.txt

# Run the opcodes program
python -m malbolge.cli run --opcodes-file examples/samples/OP_CODES.txt
```

Or use them with the analysis scripts:

```bash
# Analyze one of the samples
python examples/analyze_program.py --ascii-file examples/samples/ASCII.txt
```

These samples work great with all the example scripts documented in [`examples/README.md`](../README.md)!
