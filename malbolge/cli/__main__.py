# SPDX-License-Identifier: MIT
"""
Entry point for running malbolge.cli as a module.

This allows you to run:
    python -m malbolge.cli [command]

instead of:
    python -m malbolge.cli.main [command]
"""

from __future__ import annotations

from .main import app

if __name__ == "__main__":
    app()
