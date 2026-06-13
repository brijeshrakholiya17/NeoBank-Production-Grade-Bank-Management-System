"""
Shared helpers: logging configuration, validation and pretty formatting.

Keeping cross-cutting concerns here keeps the rest of the codebase focused
on its single responsibility.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def configure_logging(log_path: str = "data/bank.log", level: int = logging.INFO) -> logging.Logger:
    """Configure a module-level logger that writes structured audit lines
    to a file. Every significant action (open/deposit/withdraw/transfer)
    is logged - exactly what an auditor would expect from a banking app."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("neobank")
    logger.setLevel(level)
    if not logger.handlers:  # avoid duplicate handlers on re-import
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
        )
        logger.addHandler(handler)
    return logger


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,49}$")
_PIN_RE = re.compile(r"^\d{4,6}$")


def validate_name(name: str) -> str:
    name = (name or "").strip()
    if not _NAME_RE.match(name):
        raise ValueError("Name must be 2-50 letters (spaces, ., ', - allowed).")
    return name


def validate_pin(pin: str) -> str:
    if not _PIN_RE.match(pin or ""):
        raise ValueError("PIN must be 4 to 6 digits.")
    return pin


# --------------------------------------------------------------------------- #
# Formatting helpers (for a clean CLI)
# --------------------------------------------------------------------------- #
def money(amount: float) -> str:
    return f"Rs. {amount:,.2f}"


def render_table(headers: Iterable[str], rows: Iterable[Iterable[str]]) -> str:
    """Render a simple, dependency-free ASCII table."""
    headers = list(headers)
    rows = [list(map(str, r)) for r in rows]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def line(char: str = "-") -> str:
        return "+".join(char * (w + 2) for w in widths).join(["+", "+"])

    def fmt(cols: list[str]) -> str:
        return "|".join(f" {c:<{widths[i]}} " for i, c in enumerate(cols)).join(["|", "|"])

    out = [line(), fmt(headers), line("=")]
    out.extend(fmt(r) for r in rows)
    out.append(line())
    return "\n".join(out)
