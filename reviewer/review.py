"""Pipeline: analyze -> score -> integrity checks -> routing -> feedback."""
from __future__ import annotations

import json
from pathlib import Path

from . import similarity
from .analyzer import Signals, analyze
from .feedback import build_feedback
from .scoring import band_for, overall, score_criteria

DEFAULT_RUBRIC = Path(__file__).resolve().parent.parent / "data" / "rubric.json"


def load_rubric(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or DEFAULT_RUBRIC).read_text())


def fingerprint(sig: Signals) -> dict:
    raw, struct = similarity.code_views(sig.py_texts)
    return {"raw": raw, "struct": struct, "readme": similarity.readme_words(sig.readme_text)}


def _flags(sig: Signals, matches: list[dict]) -> list[dict]:
    flags = []
    if sig.secrets:
        flags.append({"kind": "secrets", "severity": "high",
                      "detail": "Possible credentials committed: " + "; ".join(sig.secrets[:3])})
    if sig.committed_env_file and not sig.secrets:
        flags.append({"kind": "env_file", "severity": "medium", "detail": "A .env file is committed"})
    for m in matches[:3]:
        flags.append({
            "kind": "similarity",
            "severity": "high",
            "detail": (f"High overlap with '{m['other']}' ({m['reason']}; code {m['raw']}, "
                       f"structure {m['struct']}, README {m['readme']}). Needs a human look, not a verdict."),
        })
    if sig.commits is not None and len(sig.commits) == 1 and sig.py.total_lines >= 150:
        flags.append({"kind": "bulk_commit", "severity": "medium",
                      "detail": "All work arrived in a single commit"})
    if sig.placeholders:
        flags.append({"kind": "placeholder", "severity": "medium",
                      "detail": f"Placeholder text found in {sig.placeholders} file(s)"})
    return flags


def _routing(score: float, criteria, flags, sig: Signals, rubric: dict) -> tuple[bool, list[str]]:
    reasons = []
    for f in flags:
        if f["severity"] == "high":
            reasons.append(f["detail"])
    margin = rubric["borderline_margin"]
    for threshold, name in rubric["bands"]:
        if threshold and abs(score - threshold) <= margin:
            reasons.append(f"Score {score} is within {margin} points of the {name} cutoff ({threshold})")
            break
    # Only the quality signals can contradict each other. A zero on task fit or git
    # history means something is missing, which the score already reflects.
    quality = [c.score for c in criteria if c.key in ("documentation", "code_quality", "testing") and c.available]
    if quality and max(quality) - min(quality) >= rubric["conflict_gap"]:
        reasons.append("Docs, code and tests disagree strongly (one is excellent while another is nearly empty)")
    if sig.py.total_lines < 20 and sig.readme_words < 50:
        reasons.append("Very little content to evaluate; the upload may be incomplete")
    return bool(reasons), reasons


def result_from_signals(sig: Signals, rubric: dict, matches: list[dict] | None = None) -> dict:
    criteria = score_criteria(sig, rubric)
    score = overall(criteria)
    flags = _flags(sig, matches or [])
    needs_review, reasons = _routing(score, criteria, flags, sig, rubric)
    notes = []
    if any(not c.available for c in criteria):
        notes.append("Git history was not available, so the score uses the remaining criteria only.")
    result = {
        "name": sig.name,
        "score": score,
        "band": band_for(score, rubric["bands"]),
        "criteria": [
            {"key": c.key, "label": c.label, "weight": c.weight, "score": c.score,
             "available": c.available, "good": c.good, "gaps": c.gaps}
            for c in criteria
        ],
        "flags": flags,
        "needs_human_review": needs_review,
        "review_reasons": reasons,
        "notes": notes,
        "stats": {
            "files": sig.file_count,
            "python_lines": sig.py.total_lines,
            "functions": sig.py.functions,
            "test_functions": sig.test_funcs,
            "readme_words": sig.readme_words,
            "commits": None if sig.commits is None else len(sig.commits),
        },
    }
    result["feedback"] = build_feedback(result)
    return result


def review_submission(root: str | Path, rubric: dict | None = None, corpus_dir: str | Path | None = None) -> dict:
    """Review one submission folder, optionally comparing it to a folder of others."""
    rubric = rubric or load_rubric()
    root = Path(root).resolve()
    sig = analyze(root, rubric["long_function_lines"])
    matches: list[dict] = []
    if corpus_dir:
        corpus = {}
        for child in sorted(Path(corpus_dir).iterdir()):
            if child.is_dir() and child.resolve() != root:
                other = analyze(child, rubric["long_function_lines"])
                corpus[other.name] = fingerprint(other)
        matches = similarity.compare(fingerprint(sig), corpus, rubric["similarity"])
    return result_from_signals(sig, rubric, matches)


def review_cohort(cohort_dir: str | Path, rubric: dict | None = None) -> list[dict]:
    """Review every subfolder of a directory, comparing each against the rest."""
    rubric = rubric or load_rubric()
    sigs = {}
    prints = {}
    for child in sorted(Path(cohort_dir).iterdir()):
        if child.is_dir():
            s = analyze(child, rubric["long_function_lines"])
            sigs[s.name] = s
            prints[s.name] = fingerprint(s)
    results = []
    for name, sig in sigs.items():
        others = {k: v for k, v in prints.items() if k != name}
        matches = similarity.compare(prints[name], others, rubric["similarity"])
        results.append(result_from_signals(sig, rubric, matches))
    return results
