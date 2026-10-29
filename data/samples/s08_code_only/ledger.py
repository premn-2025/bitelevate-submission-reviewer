"""Aggregate several accounts."""
from __future__ import annotations

from account import Account


def total_balance(accounts: list[Account]) -> float:
    """Sum of all balances."""
    return sum(a.balance for a in accounts)


def richest(accounts: list[Account]) -> Account | None:
    """Account with the highest balance, or None if the list is empty."""
    return max(accounts, key=lambda a: a.balance, default=None)


def transfer(src: Account, dst: Account, amount: float) -> None:
    """Move money between two accounts."""
    src.withdraw(amount)
    dst.deposit(amount)
