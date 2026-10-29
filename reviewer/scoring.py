"""Turn static signals into rubric scores, each with evidence."""
from __future__ import annotations

from dataclasses import dataclass, field

from .analyzer import GENERIC_MESSAGES, Signals


@dataclass
class Criterion:
    key: str
    label: str
    weight: float
    score: float = 0.0            # 0..1
    available: bool = True
    good: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    def add(self, points: float, earned: float, ok: bool, good: str, gap: str) -> None:
        """Add one check: `points` is the share of the criterion, `earned` in 0..1."""
        self.score += points * max(0.0, min(1.0, earned))
        (self.good if ok else self.gaps).append(good if ok else gap)


def _documentation(s: Signals, c: Criterion) -> Criterion:
    has = bool(s.readme_text)
    c.add(0.15, 1.0 if has else 0.0, has, "README present", "No README found")
    if not has:
        return c
    c.add(0.20, s.readme_words / 250, s.readme_words >= 150,
          f"README has substance ({s.readme_words} words)",
          f"README is short ({s.readme_words} words); aim for at least 150")
    c.add(0.15, 1.0 if "setup" in s.readme_sections else 0.0, "setup" in s.readme_sections,
          "Setup instructions have their own section", "No setup/installation section")
    c.add(0.10, 1.0 if "usage" in s.readme_sections else 0.0, "usage" in s.readme_sections,
          "Usage/run instructions present", "No usage or 'how to run' section")
    c.add(0.05, 1.0 if "overview" in s.readme_sections else 0.0, "overview" in s.readme_sections,
          "Overview explains what the project does", "No overview of the problem or project")
    depth = sum(1 for k in ("approach", "results", "limits") if k in s.readme_sections)
    c.add(0.15, depth / 3, depth >= 2,
          f"Covers approach/results/limitations ({depth} of 3)",
          f"Only {depth} of approach/results/limitations covered in the README")
    c.add(0.05, 1.0 if s.readme_code_blocks else 0.0, s.readme_code_blocks > 0,
          "Includes runnable command examples", "No code blocks showing how to run it")
    per_heading = s.readme_words / max(len(s.readme_headings), 1)
    c.add(0.15, per_heading / 25, per_heading >= 20,
          "Sections have real content, not just headings",
          f"Sections look thin ({per_heading:.0f} words per heading); headings alone don't document anything")
    return c


def _code_quality(s: Signals, c: Criterion, long_limit: int) -> Criterion:
    p = s.py
    if p.files == 0:
        c.gaps.append("No Python code found")
        return c
    ok_parse = 1 - p.parse_errors / max(p.files + p.parse_errors, 1)
    c.add(0.20, ok_parse, p.parse_errors == 0, "All Python files parse cleanly",
          f"{p.parse_errors} Python file(s) have syntax errors")
    if p.definitions:
        c.add(0.25, p.documented / p.definitions, p.documented / p.definitions >= 0.6,
              f"{p.documented} of {p.definitions} functions/classes have docstrings",
              f"Only {p.documented} of {p.definitions} functions/classes have docstrings")
    else:
        c.gaps.append("No functions or classes defined; everything is script-level code")
    if p.functions:
        c.add(0.25, 1 - p.long_functions / p.functions, p.long_functions == 0,
              f"No function longer than {long_limit} lines",
              f"{p.long_functions} function(s) exceed {long_limit} lines (longest {p.max_func_len})")
        c.add(0.10, p.typed_funcs / p.functions, p.typed_funcs / p.functions >= 0.5,
              "Type hints used on most functions", "Few functions have type hints")
    c.add(0.10, 1.0 if p.bare_excepts == 0 else max(0.0, 1 - p.bare_excepts / 3), p.bare_excepts == 0,
          "No bare except clauses", f"{p.bare_excepts} bare 'except:' clause(s) swallow every error")
    c.add(0.10, p.total_lines / 150, p.total_lines >= 80,
          f"Meaningful amount of code ({p.total_lines} lines)",
          f"Very little code ({p.total_lines} lines)")
    return c


def _testing(s: Signals, c: Criterion) -> Criterion:
    c.add(0.30, 1.0 if s.test_files else 0.0, s.test_files > 0,
          f"{s.test_files} test file(s)", "No test files found")
    if s.test_files:
        c.add(0.40, s.test_funcs / 8, s.test_funcs >= 5,
              f"{s.test_funcs} test functions", f"Only {s.test_funcs} test function(s); aim for 5 or more")
        per_test = s.asserts / max(s.test_funcs, 1)
        c.add(0.20, per_test, per_test >= 1,
              f"Tests contain assertions ({s.asserts})", "Tests contain few or no assertions")
    c.add(0.10, 1.0 if s.readme_mentions_tests else 0.0, s.readme_mentions_tests,
          "README explains how to run the tests", "README does not say how to run tests")
    return c


def _structure(s: Signals, c: Criterion) -> Criterion:
    c.add(0.25, 1.0 if s.has_dep_file else 0.0, s.has_dep_file,
          "Dependencies declared", "No requirements.txt / pyproject / package.json")
    c.add(0.15, 1.0 if s.has_gitignore else 0.0, s.has_gitignore, ".gitignore present", "No .gitignore")
    c.add(0.20, 1.0 if s.has_entrypoint else 0.0, s.has_entrypoint,
          "Clear entrypoint (app/main/notebook)", "No obvious entrypoint to run the project")
    c.add(0.15, 1.0 if s.py.files >= 2 else 0.0, s.py.files >= 2,
          "Code split across more than one module", "All code is in a single file or missing")
    env_ok = (not s.uses_env_vars) or s.has_env_example
    c.add(0.10, 1.0 if env_ok else 0.0, env_ok,
          "Configuration handled cleanly" if s.uses_env_vars else "No hidden environment requirements",
          "Reads environment variables but ships no .env.example")
    clean = not s.junk_dirs and not s.committed_env_file
    why = []
    if s.junk_dirs:
        why.append("committed " + ", ".join(s.junk_dirs))
    if s.committed_env_file:
        why.append("committed .env")
    c.add(0.15, 1.0 if clean else 0.0, clean, "No virtualenv or .env committed",
          "Repository is not clean: " + "; ".join(why))
    return c


def _git(s: Signals, c: Criterion) -> Criterion:
    if s.commits is None:
        c.available = False
        c.gaps.append("Git history not available in this submission")
        return c
    n = len(s.commits)
    c.add(0.40, n / 8, n >= 6, f"{n} commits", f"Only {n} commit(s); history shows little incremental work")
    meaningful = [m for m in s.commits if len(m.split()) >= 3 and m.lower().strip(".!") not in GENERIC_MESSAGES]
    share = len(meaningful) / n if n else 0.0
    c.add(0.35, share, share >= 0.7, "Commit messages describe the change",
          "Many commit messages are generic ('update', 'fix') or too short")
    c.add(0.15, 1.0 if n >= 2 else 0.0, n >= 2, "Work spread over multiple commits",
          "Everything arrived in a single commit")
    uniq = len(set(s.commits)) / n if n else 0.0
    c.add(0.10, uniq, uniq >= 0.8, "Commit messages are distinct", "Many repeated commit messages")
    return c


def _task_fit(s: Signals, c: Criterion, items: dict) -> Criterion:
    heading_blob = " ".join(s.md_headings + s.file_names).lower()
    per = 1 / max(len(items), 1)
    for item in items.values():
        where = item["where"]
        if where == "structure":
            hit = s.has_entrypoint and s.has_dep_file and s.py.total_lines >= 50
        elif where == "headings_or_filenames":
            hit = any(p in heading_blob for p in item["patterns"])
        else:
            hit = any(p in s.text_blob for p in item["patterns"])
        c.add(per, 1.0 if hit else 0.0, hit, f"Delivers: {item['label']}", f"Missing: {item['label']}")
    return c


def score_criteria(s: Signals, rubric: dict) -> list[Criterion]:
    out = []
    long_limit = rubric.get("long_function_lines", 40)
    for key, meta in rubric["criteria"].items():
        c = Criterion(key=key, label=meta["label"], weight=float(meta["weight"]))
        if key == "documentation":
            _documentation(s, c)
        elif key == "code_quality":
            _code_quality(s, c, long_limit)
        elif key == "testing":
            _testing(s, c)
        elif key == "structure":
            _structure(s, c)
        elif key == "git_hygiene":
            _git(s, c)
        elif key == "task_fit":
            _task_fit(s, c, rubric["required_items"])
        c.score = round(min(c.score, 1.0), 3)
        out.append(c)
    return out


def overall(criteria: list[Criterion]) -> float:
    live = [c for c in criteria if c.available]
    total = sum(c.weight for c in live)
    if not total:
        return 0.0
    return round(100 * sum(c.weight * c.score for c in live) / total, 1)


def band_for(score: float, bands: list) -> str:
    for threshold, name in bands:
        if score >= threshold:
            return name
    return bands[-1][1]
