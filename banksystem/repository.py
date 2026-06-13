"""
Persistence layer implementing the Repository pattern.

The rest of the application talks to an ``AccountRepository`` *interface*
and never touches the storage format directly. This decoupling means we
could swap the JSON backend for SQLite or Postgres tomorrow without
changing a single line of business logic - a hallmark of maintainable
design.

Two implementations are provided:
    * ``JsonAccountRepository``  - durable, file-backed (default)
    * ``InMemoryAccountRepository`` - fast, ephemeral (used by tests)

The JSON writer is *atomic*: it writes to a temporary file and then
``os.replace``-s it into place, so a crash mid-write can never corrupt
the live data file.
"""

from __future__ import annotations

import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from .models import Account


class AccountRepository(ABC):
    """Abstract contract every storage backend must satisfy."""

    @abstractmethod
    def add(self, account: Account) -> None: ...

    @abstractmethod
    def get(self, account_number: str) -> Optional[Account]: ...

    @abstractmethod
    def exists(self, account_number: str) -> bool: ...

    @abstractmethod
    def update(self, account: Account) -> None: ...

    @abstractmethod
    def delete(self, account_number: str) -> None: ...

    @abstractmethod
    def list_all(self) -> List[Account]: ...

    @abstractmethod
    def next_account_number(self) -> str: ...


class InMemoryAccountRepository(AccountRepository):
    """Keeps everything in a dict. Great for unit tests and demos."""

    def __init__(self) -> None:
        self._store: Dict[str, Account] = {}
        self._counter = 1000

    def add(self, account: Account) -> None:
        self._store[account.account_number] = account

    def get(self, account_number: str) -> Optional[Account]:
        return self._store.get(account_number)

    def exists(self, account_number: str) -> bool:
        return account_number in self._store

    def update(self, account: Account) -> None:
        self._store[account.account_number] = account

    def delete(self, account_number: str) -> None:
        self._store.pop(account_number, None)

    def list_all(self) -> List[Account]:
        return list(self._store.values())

    def next_account_number(self) -> str:
        self._counter += 1
        return f"AC{self._counter:06d}"


class JsonAccountRepository(AccountRepository):
    """File-backed repository persisting accounts to a single JSON document."""

    def __init__(self, path: str | os.PathLike[str] = "data/bank_data.json") -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._store: Dict[str, Account] = {}
        self._counter = 1000
        self._load()

    # ----- internal I/O ------------------------------------------------ #
    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Corrupt/unreadable file: start clean rather than crash.
            return
        self._counter = raw.get("counter", 1000)
        for acc_data in raw.get("accounts", []):
            account = Account.from_dict(acc_data)
            self._store[account.account_number] = account

    def _flush(self) -> None:
        payload = {
            "counter": self._counter,
            "accounts": [a.to_dict() for a in self._store.values()],
        }
        # Atomic write: temp file in the same dir, then os.replace().
        directory = self._path.parent
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self._path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    # ----- repository interface --------------------------------------- #
    def add(self, account: Account) -> None:
        self._store[account.account_number] = account
        self._flush()

    def get(self, account_number: str) -> Optional[Account]:
        return self._store.get(account_number)

    def exists(self, account_number: str) -> bool:
        return account_number in self._store

    def update(self, account: Account) -> None:
        self._store[account.account_number] = account
        self._flush()

    def delete(self, account_number: str) -> None:
        if account_number in self._store:
            del self._store[account_number]
            self._flush()

    def list_all(self) -> List[Account]:
        return list(self._store.values())

    def next_account_number(self) -> str:
        self._counter += 1
        self._flush()
        return f"AC{self._counter:06d}"
