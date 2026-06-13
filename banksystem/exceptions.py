"""
Custom exception hierarchy for the banking domain.

Defining a dedicated exception tree (rather than raising bare
``Exception`` or ``ValueError`` everywhere) lets callers catch
errors at exactly the level of granularity they need and keeps the
business rules self-documenting.

    BankError                  (base for everything in this app)
    +- AccountNotFoundError
    +- DuplicateAccountError
    +- AuthenticationError
    +- AccountInactiveError
    +- InvalidAmountError
    +- InsufficientFundsError
"""

from __future__ import annotations


class BankError(Exception):
    """Base class for all exceptions raised by the banking system."""


class AccountNotFoundError(BankError):
    """Raised when an account number does not exist in the system."""

    def __init__(self, account_number: str) -> None:
        self.account_number = account_number
        super().__init__(f"No account found with number '{account_number}'.")


class DuplicateAccountError(BankError):
    """Raised when attempting to create an account that already exists."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"An account already exists for '{identifier}'.")


class AuthenticationError(BankError):
    """Raised when a PIN/credential check fails."""

    def __init__(self, message: str = "Authentication failed: invalid credentials.") -> None:
        super().__init__(message)


class AccountInactiveError(BankError):
    """Raised when an operation is attempted on a closed/frozen account."""

    def __init__(self, account_number: str) -> None:
        self.account_number = account_number
        super().__init__(f"Account '{account_number}' is not active.")


class InvalidAmountError(BankError):
    """Raised when a monetary amount is non-positive or malformed."""

    def __init__(self, amount: object) -> None:
        self.amount = amount
        super().__init__(f"Invalid amount: {amount!r}. Amount must be a positive number.")


class InsufficientFundsError(BankError):
    """Raised when a withdrawal/transfer exceeds the available balance."""

    def __init__(self, balance: float, requested: float) -> None:
        self.balance = balance
        self.requested = requested
        super().__init__(
            f"Insufficient funds: balance is {balance:.2f} but {requested:.2f} was requested."
        )
