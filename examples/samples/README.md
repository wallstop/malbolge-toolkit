# Sample Malbolge Programs

**Welcome!** This directory contains pre-generated Malbolge programs that you can use for testing, learning, or experimentation.

**Why are these useful?** Since Malbolge programs are impossible to write by hand, having working examples is helpful for:

- Testing the interpreter without generating new programs
- Learning what valid Malbolge programs look like
- Quick experimentation without waiting for generation
- Comparing against your own generated programs

## What's Inside

- **[PROGRAM_ASCII.txt](./PROGRAM_ASCII.txt)**: A generated Malbolge program that prints "Hello", stored as its raw ASCII source

  - Great for testing the interpreter with ASCII input
  - Shows what Malbolge source code looks like

- **[PROGRAM_OP_CODES.txt](./PROGRAM_OP_CODES.txt)**: A generated Malbolge program that prints "Hello", stored as the interpreter's opcodes

  - Shows the internal opcode representation
  - Perfect for testing the interpreter's functionality

## How to Use These

Run them directly with the CLI:

```bash
# Run the ASCII program
python -m malbolge.cli run --ascii-file examples/samples/PROGRAM_ASCII.txt

# Run the opcodes program
python -m malbolge.cli run --opcodes-file examples/samples/PROGRAM_OP_CODES.txt
```

Or use them with the Python API:

```python
from malbolge import MalbolgeInterpreter
from pathlib import Path

interpreter = MalbolgeInterpreter()
opcodes = Path("examples/samples/PROGRAM_OP_CODES.txt").read_text().strip()
result = interpreter.execute(opcodes)
print(result.output)  # "Hello"
```

These samples work great with all the example scripts documented in [`examples/README.md`](../README.md)!
