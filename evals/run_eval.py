"""Check the reviewer against the author-assigned labels in evals/labels.json.

    python evals/run_eval.py

Reports rank agreement, error in points, band agreement, whether copies and
leaked secrets were caught, and how much of the cohort was routed to a human.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from reviewer.review import load_rubric, review_cohort  # noqa: E402
from reviewer.scoring import band_for  # noqa: E402


def main() -> int:
    rubric = load_rubric()
    labels = json.loads((ROOT / "evals" / "labels.json").read_text())
    results = {r["name"]: r for r in review_cohort(ROOT / "data" / "samples", rubric)}
    names = sorted(labels["scores"])

    human = [labels["scores"][n] for n in names]
    auto = [results[n]["score"] for n in names]
    rho, _ = spearmanr(human, auto)
    errors = [abs(h - a) for h, a in zip(human, auto)]
    mae = sum(errors) / len(errors)

    order = [b for _, b in rubric["bands"]][::-1]  # lowest to highest
    exact = within_one = 0
    rows = []
    for n, h, a in zip(names, human, auto):
        hb, ab = band_for(h, rubric["bands"]), results[n]["band"]
        exact += hb == ab
        within_one += abs(order.index(hb) - order.index(ab)) <= 1
        rows.append((n, h, a, hb, ab, results[n]["needs_human_review"]))

    flagged_pairs = set()
    for n, r in results.items():
        for f in r["flags"]:
            if f["kind"] == "similarity":
                for other in names:
                    if other != n and f"'{other}'" in f["detail"]:
                        flagged_pairs.add(frozenset((n, other)))
    expected_pairs = {frozenset(p) for p in labels["duplicate_pairs"]}
    caught = expected_pairs & flagged_pairs
    false_pairs = flagged_pairs - expected_pairs

    secret_hits = {n for n, r in results.items() if any(f["kind"] == "secrets" for f in r["flags"])}
    expected_secret = set(labels["secret_samples"])

    routed = [n for n in names if results[n]["needs_human_review"]]
    summary = {
        "samples": len(names),
        "spearman_rho": round(float(rho), 3),
        "mean_abs_error_points": round(mae, 1),
        "band_exact": f"{exact}/{len(names)}",
        "band_within_one": f"{within_one}/{len(names)}",
        "duplicate_pairs_caught": f"{len(caught)}/{len(expected_pairs)}",
        "duplicate_false_positive_pairs": len(false_pairs),
        "secrets_caught": f"{len(secret_hits & expected_secret)}/{len(expected_secret)}",
        "secret_false_positives": len(secret_hits - expected_secret),
        "routed_to_human": f"{len(routed)}/{len(names)}",
    }

    print(f"{'sample':<30}{'label':>6}{'tool':>7}  {'label band':<12}{'tool band':<12}review")
    for n, h, a, hb, ab, rv in rows:
        mark = "" if hb == ab else "  <- band differs"
        print(f"{n:<30}{h:>6}{a:>7.1f}  {hb:<12}{ab:<12}{'yes' if rv else 'no '}{mark}")
    print()
    for k, v in summary.items():
        print(f"{k:<32}{v}")

    out = {"summary": summary, "rows": [dict(zip(("sample", "label", "tool", "label_band", "tool_band", "routed"), r)) for r in rows]}
    (ROOT / "evals" / "results.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
