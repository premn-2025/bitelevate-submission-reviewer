"""Generate a small synthetic cohort of submissions under data/samples/.

These are NOT real student submissions. They are hand-built stand-ins that
cover the situations a reviewer meets: strong work, partial work, README-only
work, empty uploads, a committed secret, and two copied projects.
Run:  python data/make_samples.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

OUT = Path(__file__).resolve().parent / "samples"

# ---------------------------------------------------------------- code bases

LEAD_SCORER = r'''"""Score inbound sales leads from structured inquiry fields."""
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
'''

LEAD_APP = r'''"""Command line demo for the lead scorer."""
import sys

from scorer import Lead, band, score_lead


def main(argv: list[str]) -> None:
    """Score one lead given on the command line."""
    company, budget, weeks = argv[1], int(argv[2]), int(argv[3])
    lead = Lead(company, budget, " ".join(argv[4:]), weeks)
    value = score_lead(lead)
    print(f"{company}: {value} ({band(value)})")


if __name__ == "__main__":
    main(sys.argv)
'''

LEAD_TESTS = r'''from scorer import Lead, band, budget_points, keyword_points, score_lead, urgency_points


def test_budget_tiers():
    assert budget_points(600_000) == 30
    assert budget_points(150_000) == 20
    assert budget_points(25_000) == 10
    assert budget_points(1_000) == 0


def test_keywords_are_case_insensitive():
    assert keyword_points("Need CRM Automation") == 25


def test_no_keywords():
    assert keyword_points("hello there") == 0


def test_urgency_short_timeline():
    assert urgency_points(2) == 15


def test_urgency_long_timeline():
    assert urgency_points(30) == 2


def test_score_is_capped():
    lead = Lead("Acme", 900_000, "automation agent crm cloud migration", 1)
    assert score_lead(lead) == 100


def test_band_names():
    assert band(60) == "hot"
    assert band(30) == "warm"
    assert band(5) == "cold"


def test_end_to_end_cold_lead():
    lead = Lead("Tiny", 1_000, "just browsing", 40)
    assert band(score_lead(lead)) == "cold"
'''

SENTIMENT = r'''"""Lexicon-based sentiment scoring for short customer reviews."""
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
'''

SENTIMENT_RUN = r'''"""Run the sentiment summary over a text file with one review per line."""
import sys
from pathlib import Path

from classifier import summarize


def load(path: str) -> list[str]:
    """Read non-empty lines from a file."""
    return [l.strip() for l in Path(path).read_text().splitlines() if l.strip()]


def main() -> None:
    """Print label counts for the file given as the first argument."""
    counts = summarize(load(sys.argv[1]))
    for name in ("positive", "neutral", "negative"):
        print(f"{name:<9} {counts.get(name, 0)}")


if __name__ == "__main__":
    main()
'''

SENTIMENT_TESTS = r'''from classifier import label, polarity, summarize, tokenize


def test_tokenize_lowercases():
    assert tokenize("Great Service") == ["great", "service"]


def test_positive_label():
    assert label("fast and helpful") == "positive"


def test_negative_label():
    assert label("slow and rude") == "negative"


def test_negation_flips_sign():
    assert polarity(tokenize("not great")) == -1


def test_neutral_label():
    assert label("the box arrived") == "neutral"


def test_summarize_counts():
    counts = summarize(["love it", "terrible", "ok"])
    assert counts["positive"] == 1 and counts["negative"] == 1 and counts["neutral"] == 1
'''

CSV_CLEANER = r'''"""Small helpers for tidying messy CSV exports."""
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
'''

CSV_REPORT = r'''"""Summarize what cleaning changed."""
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
'''

CSV_TESTS = r'''from cleaner import dedupe, drop_empty, normalize_header, parse_number
from report import summary


def test_header_normalization():
    assert normalize_header("Total Amount (INR)") == "total_amount_inr"


def test_parse_plain_and_commas():
    assert parse_number("1,200.50") == 1200.5


def test_parse_parentheses_negative():
    assert parse_number("(45)") == -45


def test_parse_non_numeric():
    assert parse_number("abc") is None


def test_drop_empty_rows():
    assert drop_empty([{"a": ""}, {"a": "x"}]) == [{"a": "x"}]


def test_dedupe_keeps_first():
    rows = [{"id": "1", "v": "a"}, {"id": "1", "v": "b"}]
    assert dedupe(rows, "id") == [{"id": "1", "v": "a"}]


def test_summary_line():
    assert "2 removed" in summary(10, 8)
'''

WORDFREQ = r'''"""Count word frequencies in a text file."""
import argparse
import re
from collections import Counter


class WordCounter:
    """Keeps running word counts."""

    def __init__(self, stopwords=None):
        self.counts = Counter()
        self.stopwords = set(stopwords or [])

    def feed(self, text):
        words = re.findall(r"[a-zA-Z']+", text.lower())
        for w in words:
            if w not in self.stopwords:
                self.counts[w] += 1

    def top(self, n=10):
        """Most common n words."""
        return self.counts.most_common(n)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    wc = WordCounter(stopwords=["the", "a", "of", "and"])
    with open(args.path) as fh:
        for line in fh:
            wc.feed(line)
    for word, n in wc.top(args.top):
        print(word, n)


if __name__ == "__main__":
    main()
'''

WORDFREQ_TEST = r'''from main import WordCounter


def test_counts():
    wc = WordCounter()
    wc.feed("a b a")
    assert wc.counts["a"] == 2


def test_stopwords():
    wc = WordCounter(stopwords=["a"])
    wc.feed("a b")
    assert "a" not in wc.counts
'''

REGRESSION = r'''import random


def fit(xs, ys, lr=0.01, steps=2000):
    """Fit y = w*x + b with gradient descent."""
    w, b = 0.0, 0.0
    n = len(xs)
    for _ in range(steps):
        dw = sum((w * x + b - y) * x for x, y in zip(xs, ys)) * 2 / n
        db = sum((w * x + b - y) for x, y in zip(xs, ys)) * 2 / n
        w -= lr * dw
        b -= lr * db
    return w, b


def mse(xs, ys, w, b):
    return sum((w * x + b - y) ** 2 for x, y in zip(xs, ys)) / len(xs)


if __name__ == "__main__":
    random.seed(1)
    xs = [i / 10 for i in range(50)]
    ys = [3 * x + 2 + random.uniform(-0.3, 0.3) for x in xs]
    w, b = fit(xs, ys)
    print("w", round(w, 2), "b", round(b, 2), "mse", round(mse(xs, ys, w, b), 4))
'''

SLOPPY_INVENTORY = r'''import csv, sys
def main():
    f = sys.argv[1]
    data = []
    try:
        r = csv.reader(open(f))
        for row in r:
            data.append(row)
    except:
        print("error")
    total = 0
    low = []
    names = {}
    for i in range(1, len(data)):
        row = data[i]
        try:
            q = int(row[2])
            p = float(row[3])
        except:
            continue
        total = total + q * p
        if q < 5:
            low.append(row[1])
        if row[1] in names:
            names[row[1]] = names[row[1]] + q
        else:
            names[row[1]] = q
        if q == 0:
            print("out of stock", row[1])
        if p > 1000:
            print("expensive", row[1])
        if row[0] == "":
            print("missing id on line", i)
    print("total value", total)
    print("low stock", low)
    best = None
    for k in names:
        if best is None or names[k] > names[best]:
            best = k
    print("most stocked", best)
    for k in names:
        print(k, names[k])
    count = 0
    for k in names:
        count = count + 1
    print("items", count)
    avg = 0
    if count > 0:
        avg = total / count
    print("avg value per item", avg)
    for row in data[1:]:
        if len(row) < 4:
            print("short row", row)
    print("done")
main()
'''

ACCOUNT = r'''"""A minimal bank account with an audit trail."""
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
'''

LEDGER = r'''"""Aggregate several accounts."""
from __future__ import annotations

from account import Account


def total_balance(accounts: list[Account]) -> float:
    """Sum of all balances."""
    return sum(a.balance for a in accounts)


def richest(accounts: list[Account]) -> Account | None:
    """Account with the highest balance, or None if the list is empty."""
    return max(accounts, key=lambda a: a.balance, default=None)


def transfer(src: Account, dst: Account, amount: float) -> None:
    """Move money between two accounts."""
    src.withdraw(amount)
    dst.deposit(amount)
'''

FETCHER = r'''import requests

API_KEY = "sk-FAKEFAKEFAKEFAKEFAKE1234"
BASE = "https://api.example.com/v1"


def get_prices(symbol):
    """Fetch the latest price for a symbol."""
    r = requests.get(f"{BASE}/price/{symbol}", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10)
    r.raise_for_status()
    return r.json()["price"]


def watchlist(symbols):
    """Fetch prices for many symbols."""
    return {s: get_prices(s) for s in symbols}


if __name__ == "__main__":
    print(watchlist(["AAA", "BBB"]))
'''

STUB = r'''def run():
    pass


if __name__ == "__main__":
    run()
'''

# ------------------------------------------------------------------- docs

def readme(title, overview, setup=None, usage=None, approach=None, results=None, limits=None, tests=False):
    parts = [f"# {title}", "", "## Overview", overview, ""]
    if setup:
        parts += ["## Installation", setup, ""]
    if usage:
        parts += ["## Usage", usage, ""]
    if approach:
        parts += ["## Approach", approach, ""]
    if results:
        parts += ["## Results", results, ""]
    if limits:
        parts += ["## Limitations", limits, ""]
    if tests:
        parts += ["## Running the tests", "```\npytest -q\n```", ""]
    return "\n".join(parts)


LEADS_README = readme(
    "Lead Scorer",
    "Inbound inquiries arrive faster than a small sales team can read them. This tool gives every "
    "inquiry a 0-100 score from three signals the team already checks by hand: budget, the services "
    "mentioned, and how soon the client wants to start. It then sorts leads into hot, warm and cold "
    "so the first reply goes to the people most likely to become projects.",
    "```\npip install -r requirements.txt\n```\nThe scorer uses only the standard library; "
    "the requirements file is just pytest for the tests.",
    "```\npython app.py \"Acme Ltd\" 250000 8 need crm automation and an ai agent\n```\n"
    "The arguments are company, budget in rupees, timeline in weeks, then the free-text message.",
    "Each signal is a small pure function, so the rules can be read and changed without touching "
    "the rest. Budget uses fixed tiers, keywords add points per service, and urgency rewards "
    "short timelines. The total is capped at 100. Rules were preferred over a trained model because "
    "there is no labelled history of won and lost leads to learn from yet.",
    "On eight unit tests the bands behave as intended. On twenty hand-labelled example inquiries the "
    "hot band matched the team's own judgement in 17 cases. Tests live in tests/ and cover each "
    "function and the end-to-end path.",
    "The keyword list is short and English-only. Weights are guesses and should be recalibrated "
    "once real outcomes are available. Next steps are logging outcomes and fitting weights from them.",
    tests=True,
)

LEADS_OPPORTUNITY = """# AI Opportunity Report

## Opportunity summary
Cynbit sells AI agents and automation, so inbound lead triage is both a real internal bottleneck
and a live demo of what the company offers. Delay in the first reply is the main loss point.

## Options considered
1. Lead triage and scoring - low data needs, fast to pilot, directly measurable.
2. Proposal drafting assistant - higher value, needs past proposals as data.
3. Learner support assistant for BitElevate - good volume, harder to measure quality.

## Why triage first
It needs no training data to start, the output is easy for a human to check, and the success
metric (time to first reply for the best leads) is simple to track.
"""

LEADS_APPROACH = """# Technical Approach

## Architecture
Inquiry form -> parser -> three scoring functions -> band -> notification to the sales channel.

## Data pipeline
Inquiries are normalised into a Lead record. Budget and timeline are parsed to numbers; the free
text is lower-cased and matched against the service keyword list.

## Model choices
Rule-based scoring first, because there is no labelled history. A logistic regression on outcomes
is the planned second step once about 200 closed leads exist.

## Evaluation
Unit tests for each rule, plus agreement with manual labels on twenty example inquiries.

## Execution plan
Week 1: ship scoring behind a form. Week 2: collect outcomes. Week 4: fit weights and compare
against the rules. Milestone: hot-band precision above 70 percent.
"""

SENTIMENT_README = readme(
    "Review Sentiment Triage",
    "Customer reviews pile up and negative ones are found late. This project labels each review as "
    "positive, neutral or negative with a transparent word-list method, so unhappy customers can be "
    "contacted first. It is meant as a baseline that a heavier model has to beat.",
    "```\npip install -r requirements.txt\n```",
    "```\npython run.py reviews.txt\n```\nThe file holds one review per line and the output is the "
    "count for each label.",
    "Text is lower-cased and tokenised with a regular expression. A positive and a negative word list "
    "give a polarity score and a negator word flips the sign of the next word. A lexicon was chosen "
    "because it is fast, explainable and needs no training data.",
    "On 40 hand-labelled reviews the baseline reached about 0.72 accuracy, with most errors on sarcasm. "
    "The test suite has six cases for tokenising, negation and counting.",
    "The method cannot handle sarcasm, mixed opinions or other languages. Next steps are a small "
    "fine-tuned classifier and a comparison against this baseline.",
    tests=True,
)

SENTIMENT_APPROACH = """# Technical Approach

## Architecture
Reviews are read from a file, tokenised, scored by polarity and summarised.

## Data pipeline
Raw text, lowercase, regex tokens, polarity score, label, aggregate counts.

## Model choices
Lexicon baseline now; a distilled transformer fine-tuned on labelled reviews is the candidate upgrade.

## Evaluation
Accuracy on 40 labelled reviews and error analysis by category.

## Execution plan
Week 1: baseline and tests. Week 2: label 300 reviews. Week 3: fine-tune and compare. Milestone: beat
the baseline by at least ten accuracy points.
"""

SENTIMENT_OPPORTUNITY = """# AI Opportunity Report

## Opportunity summary
Review monitoring is a recurring need for Cynbit's reputation product work and for its clients.

## Options considered
Sentiment triage, review reply drafting, and topic clustering of complaints.

## Why sentiment triage
It is the smallest useful step, it can be evaluated with a few dozen labels, and it gives the team a
baseline to measure fancier models against.
"""

CSV_README = readme(
    "CSV Cleaner",
    "Helpers for tidying messy exports: normalising headers, parsing numbers written with commas or "
    "brackets, removing blank rows and dropping duplicates.",
    "```\npip install -r requirements.txt\n```",
    "```\nfrom cleaner import read_rows, drop_empty, dedupe\n```\nSee report.py for a one-line summary of what changed.",
    tests=True,
)

WORDFREQ_README = readme(
    "Word Frequency",
    "Counts the most common words in a text file. A small command line tool written as practice.",
    "```\npip install -r requirements.txt\n```",
    "```\npython main.py notes.txt --top 5\n```",
    approach="A Counter keeps the counts and a short stopword list is skipped.",
)

REGRESSION_README = readme(
    "Linear Fit",
    "Fits a straight line to noisy data using gradient descent written from scratch.",
    "Python 3 only, no packages.",
    "```\npython fit.py\n```",
    results="The fit recovers a slope near 3 and an intercept near 2 on the generated data.",
)

ACCOUNT_README = None  # code-only submission has no README on purpose

INVENTORY_README = readme(
    "Inventory Checker",
    "Reads an inventory CSV and prints total value, low stock items and the most stocked item. "
    "Written quickly to see what the data looks like before building anything bigger.",
    "```\npip install -r requirements.txt\n```",
    "```\npython main.py inventory.csv\n```",
    approach="One pass over the file, collecting totals and flags as it goes.",
    limits="No tests yet. Error handling is minimal.",
)

READMEONLY_README = readme(
    "Smart Business Intelligence Platform",
    "This platform uses advanced machine learning and artificial intelligence to transform business "
    "operations, delivering insights, automation and growth across every department. " * 4,
    "Install the dependencies and the environment, then configure the platform for your organisation "
    "according to the deployment guide. " * 3,
    "Launch the platform and open the dashboard to explore insights, forecasts and recommendations. " * 3,
    "The architecture combines a data lake, a feature store, deep learning models and a recommendation "
    "engine behind a scalable API gateway. " * 4,
    "The system achieves excellent accuracy and outstanding performance across benchmarks. " * 3,
    "Future work includes more models, more data and more integrations. " * 3,
)

FETCHER_README = readme(
    "Price Watchlist",
    "Fetches the latest price for a list of symbols from a market data API and prints them as a table.",
    "```\npip install -r requirements.txt\n```",
    "```\npython fetcher.py\n```",
    approach="One request per symbol with a timeout, results gathered in a dictionary.",
)

PADDED_README = """# Intelligent Platform

## Overview
AI platform.

## Installation
Install it.

## Usage
Run it.

## Approach
Machine learning pipeline.

## Results
Good evaluation metrics.

## Limitations
Some.

## Roadmap
Timeline and next steps.
"""

EMPTY_README = "# Project\n\nTODO: write this later.\n"

GITIGNORE = "__pycache__/\n*.pyc\n.venv/\n.env\n"

# ---------------------------------------------------------------- assembly

def write(base: Path, files: dict[str, str], commits: list[str] | None) -> None:
    for rel, text in files.items():
        if text is None:
            continue
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    if commits is not None:
        (base / "_commits.txt").write_text("\n".join(commits) + "\n")


def rename_copy(text: str) -> str:
    mapping = {
        "Lead": "Inquiry", "score_lead": "rate_inquiry", "budget_points": "money_points",
        "keyword_points": "topic_points", "urgency_points": "time_points", "band": "tier",
        "BUDGET_TIERS": "MONEY_TIERS", "SERVICE_KEYWORDS": "TOPIC_WORDS", "company": "client",
        "budget_inr": "budget", "timeline_weeks": "weeks", "message": "note", "total": "points",
        "floor": "limit", "value": "result", "lead": "inquiry",
    }
    for old, new in mapping.items():
        text = re.sub(rf"\b{old}\b", new, text)
    return text


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    strong_commits_a = [
        "Set up project layout and requirements", "Add budget tier scoring", "Add keyword scoring with tests",
        "Add urgency scoring", "Combine signals into capped score", "Add band names and command line demo",
        "Write unit tests for every rule", "Label twenty example inquiries for checking",
        "Write README with setup and usage", "Add opportunity report", "Add technical approach and plan",
        "Fix case-insensitive keyword matching",
    ]
    write(OUT / "s01_strong_leads", {
        "README.md": LEADS_README, "scorer.py": LEAD_SCORER, "app.py": LEAD_APP,
        "tests/test_scorer.py": LEAD_TESTS, "requirements.txt": "pytest\n", ".gitignore": GITIGNORE,
        "docs/opportunity-report.md": LEADS_OPPORTUNITY, "docs/technical-approach.md": LEADS_APPROACH,
    }, strong_commits_a)

    write(OUT / "s02_strong_sentiment", {
        "README.md": SENTIMENT_README, "classifier.py": SENTIMENT, "run.py": SENTIMENT_RUN,
        "tests/test_classifier.py": SENTIMENT_TESTS, "requirements.txt": "pytest\n", ".gitignore": GITIGNORE,
        "docs/opportunity-report.md": SENTIMENT_OPPORTUNITY, "docs/technical-approach.md": SENTIMENT_APPROACH,
    }, [
        "Initial layout", "Add tokenizer", "Add polarity scoring with negation", "Add label function",
        "Add summary counts", "Add run script for review files", "Add six unit tests",
        "Write README", "Write opportunity report", "Write technical approach and plan",
    ])

    write(OUT / "s03_good_code_no_reports", {
        "README.md": CSV_README, "cleaner.py": CSV_CLEANER, "report.py": CSV_REPORT,
        "tests/test_cleaner.py": CSV_TESTS, "requirements.txt": "pytest\n", ".gitignore": GITIGNORE,
    }, [
        "Start csv cleaner", "Add header normalisation", "Add number parsing", "Add dedupe and drop_empty",
        "Add summary report", "Add tests", "Add README",
    ])

    write(OUT / "s04_medium_wordfreq", {
        "README.md": WORDFREQ_README, "main.py": WORDFREQ, "tests/test_main.py": WORDFREQ_TEST,
        "requirements.txt": "pytest\n",
    }, ["first version", "add stopwords", "add tests", "update readme", "fix"])

    write(OUT / "s05_medium_regression", {
        "README.md": REGRESSION_README, "fit.py": REGRESSION,
    }, ["add gradient descent", "add mse and demo", "readme"])

    write(OUT / "s06_weak_inventory", {
        "README.md": INVENTORY_README, "main.py": SLOPPY_INVENTORY, "requirements.txt": "",
    }, ["update", "update", "final"])

    write(OUT / "s07_readme_only", {"README.md": READMEONLY_README}, ["add readme", "update readme"])

    write(OUT / "s08_code_only", {
        "account.py": ACCOUNT, "ledger.py": LEDGER, "main.py": "from ledger import total_balance\n",
    }, ["all code"])

    write(OUT / "s09_empty", {"README.md": EMPTY_README}, ["initial commit"])

    copy_a = rename_copy(LEAD_SCORER)
    copy_app = rename_copy(LEAD_APP).replace("from scorer import", "from scorer import")
    copy_tests = rename_copy(LEAD_TESTS)
    copy_readme = readme(
        "Inquiry Rating Tool",
        "A small tool that rates incoming inquiries between zero and one hundred so the team can reply "
        "to the most promising ones first. It looks at the money available, the services asked about "
        "and the time the client has.",
        "```\npip install -r requirements.txt\n```",
        "```\npython app.py \"Acme Ltd\" 250000 8 need crm automation\n```",
        "Three small functions each return points and the sum is capped at one hundred.",
        "Unit tests pass for each function.",
        "The word list is short.",
        tests=True,
    )
    write(OUT / "s10_copy_of_s01_renamed", {
        "README.md": copy_readme, "scorer.py": copy_a, "app.py": copy_app,
        "tests/test_scorer.py": copy_tests, "requirements.txt": "pytest\n", ".gitignore": GITIGNORE,
    }, ["add scoring", "add tests", "add readme", "tidy", "add app"])

    write(OUT / "s11_committed_secret", {
        "README.md": FETCHER_README, "fetcher.py": FETCHER, "requirements.txt": "requests\n",
        ".env": "API_KEY=sk-FAKEFAKEFAKEFAKEFAKE1234\n", ".gitignore": "__pycache__/\n*.pyc\n",
    }, ["add fetcher", "add watchlist function", "add readme", "add env file"])

    write(OUT / "s12_padded_readme", {
        "README.md": PADDED_README, "main.py": STUB, "requirements.txt": "numpy\n",
    }, ["add structure", "add readme", "update"])

    write(OUT / "s13_copy_of_s02_verbatim", {
        "README.md": readme(
            "Text Mood Checker",
            "Reads short pieces of text and says whether the mood is positive, negative or neutral.",
            "```\npip install -r requirements.txt\n```",
            "```\npython run.py reviews.txt\n```",
            "Word lists and a negation rule.",
        ),
        "classifier.py": SENTIMENT, "run.py": SENTIMENT_RUN, "requirements.txt": "pytest\n",
    }, ["upload", "add readme"])

    (OUT / "README.md").write_text(
        "# Sample cohort\n\nEvery folder here is synthetic, generated by ../make_samples.py. "
        "None is real student work, and any numbers inside their READMEs are made up fixtures.\n"
    )
    print(f"Wrote {len([p for p in OUT.iterdir() if p.is_dir()])} sample submissions to {OUT}")


if __name__ == "__main__":
    build()
