"""Command line entry point.

  python -m reviewer.cli path/to/submission
  python -m reviewer.cli https://github.com/owner/repo --corpus data/samples
  python -m reviewer.cli data/samples --cohort
"""
from __future__ import annotations

import argparse
import json
import sys

from .feedback import polish_with_llm
from .fetch import FetchError, prepare
from .review import load_rubric, review_cohort, review_submission


def render(result: dict) -> str:
    lines = [
        f"{result['name']}: {result['band']} ({result['score']}/100)"
        + ("   [NEEDS HUMAN REVIEW]" if result["needs_human_review"] else ""),
    ]
    for c in result["criteria"]:
        shown = "n/a" if not c["available"] else f"{round(c['score'] * 100):>3}%"
        lines.append(f"  {c['label']:<34} {shown:>5}  (weight {c['weight']:g})")
    for f in result["flags"]:
        lines.append(f"  ! [{f['severity']}] {f['detail']}")
    if result["review_reasons"]:
        lines.append("  Review reasons:")
        lines.extend(f"    - {r}" for r in result["review_reasons"])
    fb = result["feedback"]
    lines.append(f"  Summary: {fb['summary']}")
    if fb["strengths"]:
        lines.append("  Strengths:")
        lines.extend(f"    + {s}" for s in fb["strengths"])
    if fb["improvements"]:
        lines.append("  To improve:")
        lines.extend(f"    - {s}" for s in fb["improvements"])
    lines.extend(f"  Note: {n}" for n in result["notes"])
    if result.get("llm_feedback"):
        lines.append("  Drafted feedback (LLM):")
        lines.append("    " + result["llm_feedback"].replace("\n", "\n    "))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="First-pass review of a task submission")
    ap.add_argument("source", help="folder, .zip, or public GitHub URL (with --cohort: a folder of submissions)")
    ap.add_argument("--corpus", help="folder of other submissions to compare against for overlap")
    ap.add_argument("--rubric", help="path to a rubric JSON (default: data/rubric.json)")
    ap.add_argument("--cohort", action="store_true", help="review every subfolder of SOURCE")
    ap.add_argument("--llm", action="store_true", help="also draft friendlier feedback (needs ANTHROPIC_API_KEY or LLM_API_KEY)")
    ap.add_argument("--json", dest="json_out", help="write full results to this JSON file")
    args = ap.parse_args(argv)

    rubric = load_rubric(args.rubric)
    try:
        if args.cohort:
            results = review_cohort(args.source, rubric)
        else:
            results = [review_submission(prepare(args.source), rubric, args.corpus)]
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.llm:
        for r in results:
            r["llm_feedback"] = polish_with_llm(r)
            if r["llm_feedback"] is None:
                r["notes"].append("LLM feedback skipped (no API key or the call failed).")
    results.sort(key=lambda r: (not r["needs_human_review"], -r["score"]))
    print("\n\n".join(render(r) for r in results))
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(results, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
