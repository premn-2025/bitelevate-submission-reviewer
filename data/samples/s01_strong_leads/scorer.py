"""Score inbound sales leads from structured inquiry fields."""
from __future__ import annotations

from dataclasses import dataclass

BUDGET_TIERS = ((500_000, 30), (100_000, 20), (20_000, 10))
SERVICE_KEYWORDS = {"automation": 15, "agent": 15, "crm": 10, "cloud": 8, "migration": 8}


@dataclass
class Lead:
    """A single inbound inquiry."""

    company: str
    budget_inr: int
    message: str
    timeline_weeks: int


def budget_points(budget_inr: int) -> int:
    """Map a budget to points using fixed tiers."""
    for floor, points in BUDGET_TIERS:
        if budget_inr >= floor:
            return points
    return 0


def keyword_points(message: str) -> int:
    """Add points for each service keyword mentioned."""
    text = message.lower()
    return sum(p for word, p in SERVICE_KEYWORDS.items() if word in text)


def urgency_points(timeline_weeks: int) -> int:
    """Shorter timelines score higher."""
    if timeline_weeks <= 4:
        return 15
    if timeline_weeks <= 12:
        return 8
    return 2


def score_lead(lead: Lead) -> int:
    """Combine all signals into a 0-100 score."""
    total = (
        budget_points(lead.budget_inr)
        + keyword_points(lead.message)
        + urgency_points(lead.timeline_weeks)
    )
    return min(total, 100)


def band(score: int) -> str:
    """Name the score band."""
    if score >= 50:
        return "hot"
    if score >= 25:
        return "warm"
    return "cold"
