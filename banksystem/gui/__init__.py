"""
Graphical user interface package for NeoBank.

The GUI is a *presentation layer* only. Exactly like the CLI, it depends
solely on the ``BankService`` facade and never touches storage, hashing or
domain rules directly. This keeps the clean layered architecture intact:

    gui  ->  services  ->  repository  ->  models

Entry point:  ``from banksystem.gui import launch``  or  ``python app.py``
"""

from .app import launch

__all__ = ["launch"]
