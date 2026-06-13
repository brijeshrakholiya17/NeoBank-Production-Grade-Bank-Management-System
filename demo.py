#!/usr/bin/env python3
"""
Non-interactive demo / smoke test.

Runs a full scripted scenario against an in-memory bank so you (and anyone
viewing your GitHub) can see the whole system working end-to-end without
typing anything:

    python demo.py
"""

from banksystem.models import AccountType
from banksystem.repository import InMemoryAccountRepository
from banksystem.services import BankService
from banksystem.utils import money


def main() -> None:
    print("=" * 60)
    print("  NeoBank - Scripted Demo")
    print("=" * 60)

    bank = BankService(InMemoryAccountRepository())

    print("\n[1] Opening two accounts...")
    alice = bank.open_account("Alice Verma", AccountType.SAVINGS, "1234", 5000)
    bob = bank.open_account("Bob Singh", AccountType.CURRENT, "4321", 1000)
    print(f"    -> {alice}")
    print(f"    -> {bob}")

    print("\n[2] Alice deposits 2,500...")
    bank.deposit(alice.account_number, "1234", 2500)
    print(f"    -> Alice balance: {money(bank.get_balance(alice.account_number, '1234'))}")

    print("\n[3] Bob withdraws 1,500 (uses CURRENT overdraft)...")
    bank.withdraw(bob.account_number, "4321", 1500)
    print(f"    -> Bob balance: {money(bank.get_balance(bob.account_number, '4321'))}")

    print("\n[4] Alice transfers 3,000 to Bob...")
    bank.transfer(alice.account_number, "1234", bob.account_number, 3000)
    print(f"    -> Alice: {money(bank.get_balance(alice.account_number, '1234'))}")
    print(f"    -> Bob:   {money(bank.get_balance(bob.account_number, '4321'))}")

    print("\n[5] Trying an invalid withdrawal (should be blocked)...")
    try:
        bank.withdraw(alice.account_number, "1234", 999999)
    except Exception as exc:
        print(f"    -> Correctly blocked: {exc}")

    print("\n[6] Applying interest to all active accounts...")
    n = bank.apply_interest_to_all()
    print(f"    -> Interest credited to {n} accounts")
    print(f"    -> Alice: {money(bank.get_balance(alice.account_number, '1234'))}")

    print("\n[7] Alice's mini statement:")
    for t in bank.get_statement(alice.account_number, "1234", limit=10):
        print(f"    {t.timestamp}  {t.type.value:<12} {t.amount:>10,.2f}  "
              f"bal={t.balance_after:>10,.2f}")

    print("\nDemo complete. All systems nominal.\n")


if __name__ == "__main__":
    main()
