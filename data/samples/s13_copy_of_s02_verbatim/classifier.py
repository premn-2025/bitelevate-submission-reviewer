"""Lexicon-based sentiment scoring for short customer reviews."""
from __future__ import annotations

import re
from collections import Counter

POSITIVE = {"great", "fast", "helpful", "love", "excellent", "smooth"}
NEGATIVE = {"slow", "broken", "rude", "bad", "terrible", "refund"}
NEGATORS = {"not", "never", "no"}


def tokenize(text: str) -> list[str]:
    """Lowercase and split text into word tokens."""
    return re.findall(r"[a-z']+", text.lower())


def polarity(tokens: list[str]) -> int:
    """Count positive minus negative words, flipping after a negator."""
    total = 0
    for i, tok in enumerate(tokens):
        sign = -1 if i > 0 and tokens[i - 1] in NEGATORS else 1
        if tok in POSITIVE:
            total += sign
        elif tok in NEGATIVE:
            total -= sign
    return total


def label(text: str) -> str:
    """Return positive, negative or neutral."""
    score = polarity(tokenize(text))
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def summarize(reviews: list[str]) -> Counter:
    """Count labels across a batch of reviews."""
    return Counter(label(r) for r in reviews)
