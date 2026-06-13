"""
Unit tests for NeoBank.

These tests use the in-memory repository so they are fast and leave no
files behind. They cover the happy paths AND the important edge cases
(overdrafts, wrong PIN, transfer rollback, inactive accounts) - which is
exactly what reviewers look for to gauge engineering maturity.

Run with either:
    python -m pytest -q          (if pytest is installed)
    python -m unittest -v        (standard library, no dependencies)
"""

import unittest

from banksystem.exceptions import (
    AccountInactiveError,
    AccountNotFoundError,
    AuthenticationError,
    InsufficientFundsError,
    InvalidAmountError,
)
from banksystem.models import Account, AccountStatus, AccountType
from banksystem.repository import InMemoryAccountRepository
from banksystem.security import hash_pin, verify_pin
from banksystem.services import BankService


class SecurityTests(unittest.TestCase):
    def test_hash_is_not_plaintext_and_verifies(self):
        h = hash_pin("1234")
        self.assertNotIn("1234", h)
        self.assertTrue(verify_pin("1234", h))
        self.assertFalse(verify_pin("0000", h))

    def test_two_hashes_differ_due_to_salt(self):
        self.assertNotEqual(hash_pin("1234"), hash_pin("1234"))


class AccountModelTests(unittest.TestCase):
    def setUp(self):
        self.acc = Account.open("AC000001", "Brijesh", AccountType.SAVINGS, "1234", 100.0)

    def test_opening_deposit_recorded(self):
        self.assertEqual(self.acc.balance, 100.0)
        self.assertEqual(len(self.acc.transactions), 1)

    def test_deposit_and_withdraw(self):
        self.acc.deposit(50)
        self.assertEqual(self.acc.balance, 150.0)
        self.acc.withdraw(30)
        self.assertEqual(self.acc.balance, 120.0)

    def test_negative_amount_rejected(self):
        with self.assertRaises(InvalidAmountError):
            self.acc.deposit(-5)
        with self.assertRaises(InvalidAmountError):
            self.acc.withdraw(0)

    def test_savings_cannot_overdraw(self):
        with self.assertRaises(InsufficientFundsError):
            self.acc.withdraw(1000)

    def test_current_account_allows_overdraft(self):
        current = Account.open("AC000002", "Ravi", AccountType.CURRENT, "1234", 100.0)
        current.withdraw(900)  # within 100 + 1000 overdraft
        self.assertEqual(current.balance, -800.0)
        with self.assertRaises(InsufficientFundsError):
            current.withdraw(500)

    def test_inactive_account_blocks_operations(self):
        self.acc.status = AccountStatus.CLOSED
        with self.assertRaises(AccountInactiveError):
            self.acc.deposit(10)

    def test_interest_applied(self):
        txn = self.acc.apply_interest()
        self.assertIsNotNone(txn)
        self.assertAlmostEqual(self.acc.balance, 104.0)  # 100 * 4%

    def test_serialization_roundtrip(self):
        data = self.acc.to_dict()
        restored = Account.from_dict(data)
        self.assertEqual(restored.balance, self.acc.balance)
        self.assertEqual(restored.holder_name, self.acc.holder_name)
        self.assertTrue(restored.verify_pin("1234"))


class BankServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = BankService(InMemoryAccountRepository())
        self.a = self.service.open_account("Brijesh", AccountType.SAVINGS, "1234", 500)
        self.b = self.service.open_account("Ketan", AccountType.CURRENT, "4321", 200)

    def test_open_generates_unique_numbers(self):
        self.assertNotEqual(self.a.account_number, self.b.account_number)

    def test_wrong_pin_raises(self):
        with self.assertRaises(AuthenticationError):
            self.service.withdraw(self.a.account_number, "0000", 10)

    def test_unknown_account_raises(self):
        with self.assertRaises(AccountNotFoundError):
            self.service.get_balance("AC999999", "1234")

    def test_successful_transfer(self):
        self.service.transfer(self.a.account_number, "1234", self.b.account_number, 100)
        self.assertEqual(self.service.get_balance(self.a.account_number, "1234"), 400)
        self.assertEqual(self.service.get_balance(self.b.account_number, "4321"), 300)

    def test_transfer_rollback_on_failure(self):
        # Freeze target so the credit leg fails; debit must be rolled back.
        self.service.set_status(self.b.account_number, "4321", AccountStatus.FROZEN)
        with self.assertRaises(AccountInactiveError):
            self.service.transfer(self.a.account_number, "1234", self.b.account_number, 100)
        # Source balance unchanged because of rollback.
        self.assertEqual(self.service.get_balance(self.a.account_number, "1234"), 500)

    def test_self_transfer_blocked(self):
        with self.assertRaises(InvalidAmountError):
            self.service.transfer(self.a.account_number, "1234", self.a.account_number, 10)

    def test_statement_returns_recent_first(self):
        self.service.deposit(self.a.account_number, "1234", 10)
        self.service.withdraw(self.a.account_number, "1234", 5)
        stmt = self.service.get_statement(self.a.account_number, "1234", limit=5)
        self.assertEqual(stmt[0].type.value, "WITHDRAWAL")

    def test_batch_interest(self):
        count = self.service.apply_interest_to_all()
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
