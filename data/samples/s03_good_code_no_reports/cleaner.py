"""Small helpers for tidying messy CSV exports."""
from __future__ import annotations

import csv
from pathlib import Path


def normalize_header(name: str) -> str:
    """Turn 'Total Amount (INR)' into 'total_amount_inr'."""
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in name)
    return "_".join(cleaned.split())


def parse_number(value: str) -> float | None:
    """Parse numbers like '1,200.50' or '(45)' (negative); None if not numeric."""
    text = value.strip().replace(",", "")
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV into dictionaries with normalized headers."""
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [{normalize_header(k): (v or "").strip() for k, v in row.items()} for row in reader]


def drop_empty(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Remove rows where every field is blank."""
    return [r for r in rows if any(r.values())]


def dedupe(rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    """Keep the first row for each value of `key`."""
    seen: set[str] = set()
    kept = []
    for row in rows:
        if row.get(key) in seen:
            continue
        seen.add(row.get(key, ""))
        kept.append(row)
    return kept
