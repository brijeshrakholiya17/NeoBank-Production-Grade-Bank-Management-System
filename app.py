#!/usr/bin/env python3
"""
NeoBank - Desktop GUI entry point.

Launch the modern Tkinter banking interface:

    python app.py

This is a graphical alternative to the terminal interface (``python main.py``).
Both share the exact same business engine (``BankService``) and data file,
demonstrating a clean separation between presentation and logic.
"""

from banksystem.gui import launch

if __name__ == "__main__":
    launch()
