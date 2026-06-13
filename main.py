#!/usr/bin/env python3
"""
NeoBank - entry point.

Run the interactive banking application:

    python main.py

This thin launcher simply delegates to the CLI defined in the
``banksystem`` package, keeping the project root clean.
"""

from banksystem.cli import main

if __name__ == "__main__":
    main()
