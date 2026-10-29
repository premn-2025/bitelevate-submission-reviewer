"""Summarize what cleaning changed."""
from __future__ import annotations


def summary(before: int, after: int) -> str:
    """One line describing rows removed."""
    removed = before - after
    pct = 100 * removed / before if before else 0.0
    return f"{before} rows in, {after} out ({removed} removed, {pct:.1f}%)"


def numeric_columns(rows: list[dict[str, str]]) -> list[str]:
    """Columns where every non-blank value parses as a number."""
    from cleaner import parse_number

    if not rows:
        return []
    cols = []
    for col in rows[0]:
        values = [r[col] for r in rows if r[col]]
        if values and all(parse_number(v) is not None for v in values):
            cols.append(col)
    return cols
