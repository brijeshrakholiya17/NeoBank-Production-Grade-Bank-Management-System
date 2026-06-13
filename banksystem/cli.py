"""
Interactive command-line interface for NeoBank.

The CLI is intentionally thin: it handles input/output and delegates ALL
logic to ``BankService``. PIN entry uses ``getpass`` so it is never echoed
to the screen - a small touch that signals security awareness.
"""

from __future__ import annotations

import getpass
import sys
from typing import Callable, Optional

from .exceptions import BankError
from .models import AccountStatus, AccountType
from .repository import JsonAccountRepository
from .services import BankService
from .utils import money, render_table

BANNER = r"""
   _   _            ____              _
  | \ | | ___  ___ | __ )  __ _ _ __ | | __
  |  \| |/ _ \/ _ \|  _ \ / _` | '_ \| |/ /
  | |\  |  __/ (_) | |_) | (_| | | | |   <
  |_| \_|\___|\___/|____/ \__,_|_| |_|_|\_\
        Production-Grade Banking System  v1.0
"""


class BankCLI:
    """Renders menus and routes user choices to the service layer."""

    def __init__(self, service: Optional[BankService] = None) -> None:
        self.service = service or BankService(JsonAccountRepository())

    # ----- low-level input helpers ------------------------------------ #
    @staticmethod
    def _prompt(label: str) -> str:
        return input(f"  {label}: ").strip()

    @staticmethod
    def _prompt_pin(label: str = "PIN") -> str:
        # getpass hides the typed characters (falls back gracefully if no TTY)
        try:
            return getpass.getpass(f"  {label}: ").strip()
        except Exception:
            return input(f"  {label}: ").strip()

    def _prompt_amount(self, label: str = "Amount") -> float:
        raw = self._prompt(label)
        try:
            return float(raw)
        except ValueError:
            raise BankError(f"'{raw}' is not a valid number.")

    @staticmethod
    def _info(msg: str) -> None:
        print(f"  \u2714 {msg}")

    @staticmethod
    def _error(msg: str) -> None:
        print(f"  \u2716 {msg}")

    # ----- menu actions ------------------------------------------------ #
    def open_account(self) -> None:
        print("\n  --- Open New Account ---")
        name = self._prompt("Account holder name")
        print("  Account type:  [1] Savings   [2] Current")
        choice = self._prompt("Choose 1 or 2")
        acc_type = AccountType.SAVINGS if choice == "1" else AccountType.CURRENT
        pin = self._prompt_pin("Set a 4-6 digit PIN")
        confirm = self._prompt_pin("Confirm PIN")
        if pin != confirm:
            raise BankError("PINs do not match.")
        opening = self._prompt_amount("Opening deposit (0 for none)")

        account = self.service.open_account(name, acc_type, pin, opening)
        self._info(f"Account created! Number: {account.account_number}")
        self._info(f"Welcome, {account.holder_name}. Keep your account number safe.")

    def deposit(self) -> None:
        print("\n  --- Deposit ---")
        acc = self._prompt("Account number")
        pin = self._prompt_pin()
        amount = self._prompt_amount()
        txn = self.service.deposit(acc, pin, amount, note="Cash deposit")
        self._info(f"Deposited {money(amount)}. New balance: {money(txn.balance_after)}")

    def withdraw(self) -> None:
        print("\n  --- Withdraw ---")
        acc = self._prompt("Account number")
        pin = self._prompt_pin()
        amount = self._prompt_amount()
        txn = self.service.withdraw(acc, pin, amount, note="Cash withdrawal")
        self._info(f"Withdrew {money(amount)}. New balance: {money(txn.balance_after)}")

    def transfer(self) -> None:
        print("\n  --- Transfer ---")
        src = self._prompt("Your account number")
        pin = self._prompt_pin()
        dst = self._prompt("Recipient account number")
        amount = self._prompt_amount()
        debit, _ = self.service.transfer(src, pin, dst, amount)
        self._info(f"Transferred {money(amount)} to {dst}.")
        self._info(f"Your new balance: {money(debit.balance_after)}")

    def balance(self) -> None:
        print("\n  --- Check Balance ---")
        acc = self._prompt("Account number")
        pin = self._prompt_pin()
        bal = self.service.get_balance(acc, pin)
        self._info(f"Available balance: {money(bal)}")

    def statement(self) -> None:
        print("\n  --- Mini Statement (last 10) ---")
        acc = self._prompt("Account number")
        pin = self._prompt_pin()
        txns = self.service.get_statement(acc, pin, limit=10)
        if not txns:
            self._info("No transactions yet.")
            return
        rows = [
            (t.timestamp.replace("T", " "), t.type.value, f"{t.amount:,.2f}",
             f"{t.balance_after:,.2f}", (t.note or "-")[:24])
            for t in txns
        ]
        print(render_table(
            ["Date (UTC)", "Type", "Amount", "Balance", "Note"], rows
        ))

    def close_account(self) -> None:
        print("\n  --- Close Account ---")
        acc = self._prompt("Account number")
        pin = self._prompt_pin()
        confirm = self._prompt("Type CLOSE to confirm")
        if confirm != "CLOSE":
            raise BankError("Closure cancelled.")
        self.service.close_account(acc, pin)
        self._info(f"Account {acc} has been closed.")

    def admin_list(self) -> None:
        print("\n  --- All Accounts (admin) ---")
        accounts = self.service.list_accounts()
        if not accounts:
            self._info("No accounts yet.")
            return
        rows = [
            (a.account_number, a.holder_name, a.account_type.value,
             f"{a.balance:,.2f}", a.status.value)
            for a in accounts
        ]
        print(render_table(
            ["Number", "Holder", "Type", "Balance", "Status"], rows
        ))
        total = sum(a.balance for a in accounts)
        self._info(f"Total deposits held: {money(total)} across {len(accounts)} accounts")

    def admin_interest(self) -> None:
        print("\n  --- Apply Interest (admin batch job) ---")
        count = self.service.apply_interest_to_all()
        self._info(f"Interest credited to {count} active account(s).")

    # ----- main loop --------------------------------------------------- #
    def run(self) -> None:
        print(BANNER)
        actions: dict[str, tuple[str, Callable[[], None]]] = {
            "1": ("Open new account", self.open_account),
            "2": ("Deposit", self.deposit),
            "3": ("Withdraw", self.withdraw),
            "4": ("Transfer", self.transfer),
            "5": ("Check balance", self.balance),
            "6": ("Mini statement", self.statement),
            "7": ("Close account", self.close_account),
            "8": ("[Admin] List all accounts", self.admin_list),
            "9": ("[Admin] Apply interest to all", self.admin_interest),
        }
        while True:
            print("\n" + "=" * 44)
            print("  MAIN MENU")
            print("=" * 44)
            for key, (label, _) in actions.items():
                print(f"   {key}. {label}")
            print("   0. Exit")
            choice = self._prompt("Select an option")

            if choice == "0":
                print("\n  Thank you for banking with NeoBank. Goodbye!\n")
                return
            action = actions.get(choice)
            if not action:
                self._error("Invalid option. Please choose from the menu.")
                continue
            try:
                action[1]()
            except BankError as exc:
                self._error(str(exc))
            except KeyboardInterrupt:
                print("\n  Operation cancelled.")
            except Exception as exc:  # last-resort guard so the app never crashes
                self._error(f"Unexpected error: {exc}")


def main() -> None:
    try:
        BankCLI().run()
    except KeyboardInterrupt:
        print("\n  Interrupted. Exiting.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
