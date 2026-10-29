"""A minimal bank account with an audit trail."""
from __future__ import annotations

from dataclasses import dataclass, field


class InsufficientFunds(Exception):
    """Raised when a withdrawal exceeds the balance."""


@dataclass
class Account:
    """Holds a balance and the list of operations applied to it."""

    owner: str
    balance: float = 0.0
    history: list[tuple[str, float]] = field(default_factory=list)

    def deposit(self, amount: float) -> None:
        """Add money; amount must be positive."""
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount
        self.history.append(("deposit", amount))

    def withdraw(self, amount: float) -> None:
        """Remove money or raise InsufficientFunds."""
        if amount > self.balance:
            raise InsufficientFunds(f"balance {self.balance} < {amount}")
        self.balance -= amount
        self.history.append(("withdraw", amount))
