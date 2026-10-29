"""Score inbound sales leads from structured inquiry fields."""
from __future__ import annotations

from dataclasses import dataclass

MONEY_TIERS = ((500_000, 30), (100_000, 20), (20_000, 10))
TOPIC_WORDS = {"automation": 15, "agent": 15, "crm": 10, "cloud": 8, "migration": 8}


@dataclass
class Inquiry:
    """A single inbound inquiry."""

    client: str
    budget: int
    note: str
    weeks: int


def money_points(budget: int) -> int:
    """Map a budget to points using fixed tiers."""
    for limit, points in MONEY_TIERS:
        if budget >= limit:
            return points
    return 0


def topic_points(note: str) -> int:
    """Add points for each service keyword mentioned."""
    text = note.lower()
    return sum(p for word, p in TOPIC_WORDS.items() if word in text)


def time_points(weeks: int) -> int:
    """Shorter timelines score higher."""
    if weeks <= 4:
        return 15
    if weeks <= 12:
        return 8
    return 2


def rate_inquiry(inquiry: Inquiry) -> int:
    """Combine all signals into a 0-100 score."""
    points = (
        money_points(inquiry.budget)
        + topic_points(inquiry.note)
        + time_points(inquiry.weeks)
    )
    return min(points, 100)


def tier(score: int) -> str:
    """Name the score tier."""
    if score >= 50:
        return "hot"
    if score >= 25:
        return "warm"
    return "cold"
