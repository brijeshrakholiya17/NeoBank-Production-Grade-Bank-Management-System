"""
Domain models: the core entities of the banking system.

Highlights of the design
------------------------
* ``Enum`` classes give us type-safe, self-documenting categories instead of
  magic strings ("SAVINGS", "DEPOSIT", ...).
* ``@dataclass`` reduces boilerplate while keeping the code explicit.
* ``Account`` encapsulates its own invariants: the balance can only change
  through ``deposit`` / ``withdraw`` (encapsulation), and the raw PIN hash is
  protected behind validation methods (information hiding).
* ``to_dict`` / ``from_dict`` provide clean serialization for persistence,
  decoupling the domain from the storage format.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from .exceptions import (
    AccountInactiveError,
    InsufficientFundsError,
    InvalidAmountError,
)
from .security import hash_pin, verify_pin


def _utcnow_iso() -> str:
    """Timezone-aware UTC timestamp in ISO-8601 (sortable, unambiguous)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AccountType(str, Enum):
    """Supported account products. Inheriting ``str`` makes JSON trivial."""

    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"

    @property
    def overdraft_limit(self) -> float:
        """CURRENT accounts may go overdrawn up to a small limit; SAVINGS may not."""
        return 1_000.0 if self is AccountType.CURRENT else 0.0

    @property
    def annual_interest_rate(self) -> float:
        """Simple illustrative interest rates per product."""
        return 0.04 if self is AccountType.SAVINGS else 0.005


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    INTEREST = "INTEREST"


@dataclass(frozen=True)
class Transaction:
    """An immutable record of a single ledger movement.

    ``frozen=True`` makes instances read-only, which is correct for an
    audit log: once written, a transaction must never be mutated.
    """

    type: TransactionType
    amount: float
    balance_after: float
    timestamp: str = field(default_factory=_utcnow_iso)
    note: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["type"] = self.type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            type=TransactionType(data["type"]),
            amount=data["amount"],
            balance_after=data["balance_after"],
            timestamp=data["timestamp"],
            note=data.get("note", ""),
            id=data.get("id", uuid.uuid4().hex[:12]),
        )


@dataclass
class Account:
    """A customer bank account.

    Invariants enforced by this class:
      * balance only changes via ``deposit`` / ``withdraw`` / ``apply_interest``
      * withdrawals respect the available balance + product overdraft limit
      * inactive accounts reject all money movements
      * the PIN is stored only as a salted hash, never in plaintext
    """

    account_number: str
    holder_name: str
    account_type: AccountType
    _pin_hash: str
    balance: float = 0.0
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: str = field(default_factory=_utcnow_iso)
    transactions: List[Transaction] = field(default_factory=list)

    # ----- factory ----------------------------------------------------- #
    @classmethod
    def open(
        cls,
        account_number: str,
        holder_name: str,
        account_type: AccountType,
        pin: str,
        opening_balance: float = 0.0,
    ) -> "Account":
        """Open a brand-new account, hashing the PIN and recording the
        opening deposit (if any) as the first transaction."""
        if opening_balance < 0:
            raise InvalidAmountError(opening_balance)

        account = cls(
            account_number=account_number,
            holder_name=holder_name.strip(),
            account_type=account_type,
            _pin_hash=hash_pin(pin),
            balance=0.0,
        )
        if opening_balance > 0:
            account.deposit(opening_balance, note="Opening deposit")
        return account

    # ----- authentication --------------------------------------------- #
    def verify_pin(self, pin: str) -> bool:
        return verify_pin(pin, self._pin_hash)

    def change_pin(self, new_pin: str) -> None:
        self._pin_hash = hash_pin(new_pin)

    # ----- guards ------------------------------------------------------ #
    def _ensure_active(self) -> None:
        if self.status is not AccountStatus.ACTIVE:
            raise AccountInactiveError(self.account_number)

    @staticmethod
    def _validate_amount(amount: float) -> float:
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidAmountError(amount)
        amount = round(float(amount), 2)
        if amount <= 0:
            raise InvalidAmountError(amount)
        return amount

    @property
    def available_balance(self) -> float:
        """Balance plus any overdraft head-room available for spending."""
        return self.balance + self.account_type.overdraft_limit

    # ----- money movement --------------------------------------------- #
    def deposit(
        self, amount: float, *, note: str = "", _type: TransactionType = TransactionType.DEPOSIT
    ) -> Transaction:
        self._ensure_active()
        amount = self._validate_amount(amount)
        self.balance = round(self.balance + amount, 2)
        return self._record(_type, amount, note)

    def withdraw(
        self, amount: float, *, note: str = "", _type: TransactionType = TransactionType.WITHDRAWAL
    ) -> Transaction:
        self._ensure_active()
        amount = self._validate_amount(amount)
        if amount > self.available_balance:
            raise InsufficientFundsError(self.balance, amount)
        self.balance = round(self.balance - amount, 2)
        return self._record(_type, amount, note)

    def apply_interest(self) -> Transaction | None:
        """Credit one period of simple interest (illustrative)."""
        self._ensure_active()
        rate = self.account_type.annual_interest_rate
        interest = round(self.balance * rate, 2)
        if interest <= 0:
            return None
        self.balance = round(self.balance + interest, 2)
        return self._record(
            TransactionType.INTEREST, interest, f"Interest @ {rate:.2%} p.a."
        )

    def _record(self, ttype: TransactionType, amount: float, note: str) -> Transaction:
        txn = Transaction(
            type=ttype, amount=amount, balance_after=self.balance, note=note
        )
        self.transactions.append(txn)
        return txn

    # ----- serialization ---------------------------------------------- #
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_number": self.account_number,
            "holder_name": self.holder_name,
            "account_type": self.account_type.value,
            "pin_hash": self._pin_hash,
            "balance": self.balance,
            "status": self.status.value,
            "created_at": self.created_at,
            "transactions": [t.to_dict() for t in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        return cls(
            account_number=data["account_number"],
            holder_name=data["holder_name"],
            account_type=AccountType(data["account_type"]),
            _pin_hash=data["pin_hash"],
            balance=data["balance"],
            status=AccountStatus(data["status"]),
            created_at=data["created_at"],
            transactions=[Transaction.from_dict(t) for t in data.get("transactions", [])],
        )

    def __str__(self) -> str:
        return (
            f"[{self.account_number}] {self.holder_name} "
            f"({self.account_type.value}) - Balance: {self.balance:,.2f} "
            f"[{self.status.value}]"
        )
