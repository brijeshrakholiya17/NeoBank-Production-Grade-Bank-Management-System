"""
NeoBank - A Production-Grade Bank Management System.

A clean, layered, object-oriented banking application written in pure
Python (standard library only). Demonstrates professional engineering
practices: domain modelling, custom exceptions, the repository pattern,
a service layer, secure password hashing, structured logging and a
polished command-line interface.

Package layout
--------------
    models       -> domain entities (Account, Transaction, enums)
    exceptions   -> custom exception hierarchy
    security     -> password hashing utilities
    repository   -> JSON-backed persistence (repository pattern)
    services     -> business logic (the BankService facade)
    cli          -> interactive command-line interface
    utils        -> shared helpers (validation, formatting, logging)
"""

__version__ = "1.0.0"
__author__ = "Brijesh Rakholiya"

from .models import Account, AccountType, Transaction, TransactionType
from .services import BankService
from .exceptions import (
    BankError,
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
    AuthenticationError,
    DuplicateAccountError,
    AccountInactiveError,
)

__all__ = [
    "Account",
    "AccountType",
    "Transaction",
    "TransactionType",
    "BankService",
    "BankError",
    "AccountNotFoundError",
    "InsufficientFundsError",
    "InvalidAmountError",
    "AuthenticationError",
    "DuplicateAccountError",
    "AccountInactiveError",
]
