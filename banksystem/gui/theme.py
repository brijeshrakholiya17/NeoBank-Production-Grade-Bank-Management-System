"""
Design system for the NeoBank GUI.

A single source of truth for colours, fonts, spacing and reusable widget
factories. Centralising the visual language here is what gives the app a
consistent, polished, "designed" feel instead of default-grey Tkinter.

Highlights
----------
* A cohesive dark palette with a teal/violet accent.
* Custom rounded "card" frames drawn on a Canvas (Tkinter has no native
  rounded corners) - this is the key trick behind the modern look.
* Hover-animated flat buttons.
* A reusable labelled entry field.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional


# --------------------------------------------------------------------------- #
# Palette
# --------------------------------------------------------------------------- #
class C:
    BG          = "#0E1117"   # app background (near-black)
    SIDEBAR     = "#151A23"   # sidebar
    CARD        = "#1B2230"   # raised card surface
    CARD_HI     = "#232C3D"   # hovered/lighter card
    STROKE      = "#2A3344"   # subtle borders

    TEXT        = "#E6EAF2"   # primary text
    MUTED       = "#8A93A6"   # secondary text
    FAINT       = "#6B7384"   # placeholder / disabled text

    ACCENT      = "#2DD4BF"   # teal - primary accent
    ACCENT_DK   = "#14B8A6"
    VIOLET      = "#8B5CF6"   # secondary accent
    BLUE        = "#3B82F6"

    GOOD        = "#34D399"   # success green
    WARN        = "#FBBF24"   # warning amber
    BAD         = "#F87171"   # error red

    GRAD_TOP    = "#1E293B"
    GRAD_BOT    = "#0E1117"

    # Solid "tint" shades used for decorative overlays (Tkinter has no alpha).
    TINT_LIGHT  = "#A78BFA"   # light violet ring on the brand panel
    TINT_SOFT   = "#7C6CC4"   # softer ring
    TINT_CARD   = "#A89BE0"   # light ring on the balance card


# --------------------------------------------------------------------------- #
# Fonts
# --------------------------------------------------------------------------- #
def fonts():
    """Pick the nicest available sans-serif family on the host system."""
    import tkinter.font as tkfont

    families = set(tkfont.families())
    family = next(
        (f for f in ("Segoe UI", "SF Pro Display", "Helvetica Neue",
                     "Inter", "Roboto", "DejaVu Sans", "Arial")
         if f in families),
        "Arial",
    )
    return {
        "display": (family, 26, "bold"),
        "h1":      (family, 18, "bold"),
        "h2":      (family, 14, "bold"),
        "body":    (family, 11),
        "body_b":  (family, 11, "bold"),
        "small":   (family, 9),
        "mono":    ("Consolas" if "Consolas" in families else "Courier", 10),
        "logo":    (family, 20, "bold"),
    }


# --------------------------------------------------------------------------- #
# Rounded rectangle helper (the core of the modern look)
# --------------------------------------------------------------------------- #
def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r=18, **kw):
    """Draw a smooth rounded rectangle on a canvas and return the item id."""
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(*pts, smooth=True, **kw)


# --------------------------------------------------------------------------- #
# Card: a rounded, optionally bordered surface
# --------------------------------------------------------------------------- #
class Card(tk.Canvas):
    """A rounded rectangle surface that can host other widgets via a window."""

    def __init__(self, parent, width, height, fill=C.CARD, radius=18,
                 stroke=None, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"], highlightthickness=0, bd=0, **kw)
        self._cw, self._ch, self._cr = width, height, radius
        self._fill, self._stroke = fill, stroke
        self._draw()

    def _draw(self):
        self.delete("all")
        round_rect(self, 1, 1, self._cw - 1, self._ch - 1, r=self._cr,
                   fill=self._fill,
                   outline=self._stroke or self._fill,
                   width=1.4 if self._stroke else 0)


# --------------------------------------------------------------------------- #
# Modern flat button with hover animation
# --------------------------------------------------------------------------- #
class Button(tk.Canvas):
    def __init__(self, parent, text, command: Callable, *, width=180, height=44,
                 fill=C.ACCENT, hover=C.ACCENT_DK, fg="#06231F", radius=12,
                 font=None, icon: str = ""):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"], highlightthickness=0, bd=0)
        self._cw, self._ch, self._cr = width, height, radius
        self._fill, self._hover = fill, hover
        self._command = command
        self._bg_item = round_rect(self, 0, 0, width, height, r=radius, fill=fill)
        label = (f"{icon}  {text}" if icon else text)
        self._txt = self.create_text(width / 2, height / 2, text=label,
                                     fill=fg, font=font or fonts()["body_b"])
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.config(cursor="hand2")

    def _on_enter(self, _):
        self.itemconfig(self._bg_item, fill=self._hover)

    def _on_leave(self, _):
        self.itemconfig(self._bg_item, fill=self._fill)

    def _on_click(self, _):
        if self._command:
            self._command()


# --------------------------------------------------------------------------- #
# Labelled entry field with a clean underline style
# --------------------------------------------------------------------------- #
class Field(tk.Frame):
    def __init__(self, parent, label: str, *, show: str = "", width=26):
        super().__init__(parent, bg=parent["bg"])
        f = fonts()
        tk.Label(self, text=label.upper(), bg=parent["bg"], fg=C.MUTED,
                 font=f["small"]).pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self, textvariable=self.var, show=show, width=width,
            bg=C.CARD_HI, fg=C.TEXT, insertbackground=C.ACCENT,
            relief="flat", font=f["body"], highlightthickness=1.4,
            highlightbackground=C.STROKE, highlightcolor=C.ACCENT,
        )
        self.entry.pack(fill="x", ipady=7, pady=(4, 0))

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self.var.set(value)

    def focus(self) -> None:
        self.entry.focus_set()


def vgradient(canvas: tk.Canvas, w: int, h: int, top: str, bottom: str):
    """Paint a vertical gradient as the canvas background (subtle depth)."""
    steps = max(h, 1)
    r1, g1, b1 = canvas.winfo_rgb(top)
    r2, g2, b2 = canvas.winfo_rgb(bottom)
    for i in range(steps):
        r = int(r1 + (r2 - r1) * i / steps) >> 8
        g = int(g1 + (g2 - g1) * i / steps) >> 8
        b = int(b1 + (b2 - b1) * i / steps) >> 8
        canvas.create_line(0, i, w, i, fill=f"#{r:02x}{g:02x}{b:02x}")
