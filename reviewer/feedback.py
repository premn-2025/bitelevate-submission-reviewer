"""Student-facing feedback, built only from the evidence the rubric produced.

The default writer is a plain template, so the tool works with no API key.
`polish_with_llm` is optional: it rewords the same findings into a friendlier
paragraph. It sends the findings, never the student's code.
"""
from __future__ import annotations

import json
import os

SYSTEM_PROMPT = (
    "You write short feedback for students on a technical task submission. "
    "You are given structured findings produced by an automated checker. "
    "Use only those findings. Do not invent problems, praise, or scores. "
    "Be specific, kind, and concrete about what to fix first. "
    "Write at most 140 words in plain prose, no headings. "
    "Say once that this is a draft for the human reviewer to confirm."
)


def build_feedback(result: dict) -> dict:
    crits = [c for c in result["criteria"] if c["available"]]
    strong = sorted(crits, key=lambda c: -c["score"])
    weak = sorted(crits, key=lambda c: -(c["weight"] * (1 - c["score"])))

    strengths = []
    for c in strong:
        if c["score"] >= 0.6:
            strengths.extend(f"{c['label']}: {g}" for g in c["good"][:2])
        if len(strengths) >= 4:
            break

    improvements = []
    for c in weak:
        if c["score"] >= 0.85:
            continue
        for gap in c["gaps"][:2]:
            improvements.append(f"{c['label']}: {gap}")
        if len(improvements) >= 6:
            break

    best = strong[0]["label"] if strong else "n/a"
    gap_area = weak[0]["label"] if weak and weak[0]["score"] < 0.85 else None
    summary = f"{result['band']} ({result['score']}/100). Strongest area: {best}."
    if gap_area:
        summary += f" Biggest opportunity: {gap_area}."
    return {"summary": summary, "strengths": strengths[:4], "improvements": improvements[:6]}


def polish_with_llm(result: dict, client=None, model: str | None = None) -> str | None:
    """Return a reworded paragraph, or None if no API key / any failure."""
    if client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return None
        try:
            import anthropic  # optional dependency
            client = anthropic.Anthropic(api_key=key)
        except Exception:
            return None
    payload = {
        "band": result["band"],
        "score": result["score"],
        "strengths": result["feedback"]["strengths"],
        "improvements": result["feedback"]["improvements"],
        "flags": [f["detail"] for f in result["flags"]],
    }
    try:
        resp = client.messages.create(
            model=model or os.environ.get("CYNBIT_LLM_MODEL", "claude-sonnet-5-5"),
            max_tokens=400,
            temperature=0.2,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip() or None
    except Exception:
        return None
