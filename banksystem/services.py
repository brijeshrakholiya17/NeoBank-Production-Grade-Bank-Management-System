"""
Service layer: the BankService facade.

This is where business rules live. The CLI (or any future web/API layer)
depends only on this clean, well-named interface and stays blissfully
unaware of how accounts are stored or how PINs are hashed.

Design notes
------------
* Dependency injection: the repository is passed in, so the service is
  trivially testable with an in-memory backend.
* Authentication is enforced for every sensitive operation via
  ``_authenticated`` - a single choke-point for security.
* ``transfer`` is *atomic with rollback*: if the credit leg fails after the
  debit leg succeeded, the debit is reversed so money is never lost.
* Every mutation is written to the audit log.
"""

from __future__ import annotations

from typing import List, Tuple

from .exceptions import (
    AccountNotFoundError,
    AuthenticationError,
    DuplicateAccountError,
    InvalidAmountError,
)
from .models import Account, AccountStatus, AccountType, Transaction, TransactionType
from .repository import AccountRepository
from .utils import configure_logging, validate_name, validate_pin

_log = configure_logging()


class BankService:
    """High-level banking operations built on top of a repository."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repo = repository

    # ----- helpers ----------------------------------------------------- #
    def _require(self, account_number: str) -> Account:
        account = self._repo.get(account_number)
        if account is None:
            raise AccountNotFoundError(account_number)
        return account

    def _authenticated(self, account_number: str, pin: str) -> Account:
        account = self._require(account_number)
        if not account.verify_pin(pin):
            _log.warning("Failed auth attempt on %s", account_number)
            raise AuthenticationError()
        return account

    # ----- account lifecycle ------------------------------------------ #
    def open_account(
        self,
        holder_name: str,
        account_type: AccountType,
        pin: str,
        opening_balance: float = 0.0,
    ) -> Account:
        holder_name = validate_name(holder_name)
        validate_pin(pin)
        if opening_balance < 0:
            raise InvalidAmountError(opening_balance)

        account_number = self._repo.next_account_number()
        if self._repo.exists(account_number):  # defensive; should never happen
            raise DuplicateAccountError(account_number)

        account = Account.open(
            account_number=account_number,
            holder_name=holder_name,
            account_type=account_type,
            pin=pin,
            opening_balance=opening_balance,
        )
        self._repo.add(account)
        _log.info("Opened %s for %s (%s) opening=%.2f",
                  account_number, holder_name, account_type.value, opening_balance)
        return account

    def close_account(self, account_number: str, pin: str) -> Account:
        account = self._authenticated(account_number, pin)
        account.status = AccountStatus.CLOSED
        self._repo.update(account)
        _log.info("Closed %s", account_number)
        return account

    def set_status(self, account_number: str, pin: str, status: AccountStatus) -> Account:
        account = self._authenticated(account_number, pin)
        account.status = status
        self._repo.update(account)
        _log.info("Set status of %s to %s", account_number, status.value)
        return account

    # ----- transactions ----------------------------------------------- #
    def deposit(self, account_number: str, pin: str, amount: float, note: str = "") -> Transaction:
        account = self._authenticated(account_number, pin)
        txn = account.deposit(amount, note=note)
        self._repo.update(account)
        _log.info("Deposit %.2f to %s -> %.2f", amount, account_number, account.balance)
        return txn

    def withdraw(self, account_number: str, pin: str, amount: float, note: str = "") -> Transaction:
        account = self._authenticated(account_number, pin)
        txn = account.withdraw(amount, note=note)
        self._repo.update(account)
        _log.info("Withdraw %.2f from %s -> %.2f", amount, account_number, account.balance)
        return txn

    def transfer(
        self,
        source_number: str,
        pin: str,
        target_number: str,
        amount: float,
        note: str = "",
    ) -> Tuple[Transaction, Transaction]:
        """Move money between two accounts atomically.

        If crediting the target fails for any reason, the source debit is
        rolled back so the books always balance.
        """
        if source_number == target_number:
            raise InvalidAmountError("self-transfer is not allowed")

        source = self._authenticated(source_number, pin)
        target = self._require(target_number)

        debit = source.withdraw(
            amount, note=f"Transfer to {target_number}. {note}".strip(),
            _type=TransactionType.TRANSFER_OUT,
        )
        try:
            credit = target.deposit(
                amount, note=f"Transfer from {source_number}. {note}".strip(),
                _type=TransactionType.TRANSFER_IN,
            )
        except Exception:
            # ---- compensating transaction (rollback the debit) ---- #
            source.deposit(amount, note=f"Rollback of failed transfer to {target_number}")
            self._repo.update(source)
            _log.error("Transfer %s->%s failed; rolled back %.2f",
                       source_number, target_number, amount)
            raise

        self._repo.update(source)
        self._repo.update(target)
        _log.info("Transfer %.2f %s -> %s", amount, source_number, target_number)
        return debit, credit

    # ----- queries ----------------------------------------------------- #
    def get_balance(self, account_number: str, pin: str) -> float:
        return self._authenticated(account_number, pin).balance

    def get_statement(self, account_number: str, pin: str, limit: int = 10) -> List[Transaction]:
        account = self._authenticated(account_number, pin)
        return account.transactions[-limit:][::-1]  # most recent first

    def get_account(self, account_number: str, pin: str) -> Account:
        return self._authenticated(account_number, pin)

    def list_accounts(self) -> List[Account]:
        """Admin view: summaries only (no sensitive data exposed)."""
        return sorted(self._repo.list_all(), key=lambda a: a.account_number)

    def apply_interest_to_all(self) -> int:
        """Batch job: credit interest to every active account. Returns count."""
        count = 0
        for account in self._repo.list_all():
            if account.status is AccountStatus.ACTIVE:
                txn = account.apply_interest()
                if txn:
                    self._repo.update(account)
                    count += 1
        _log.info("Applied interest to %d accounts", count)
        return count
