import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from reviewer import review_submission, load_rubric, similarity  # noqa: E402
from reviewer.analyzer import analyze  # noqa: E402
from reviewer.feedback import polish_with_llm  # noqa: E402
from reviewer.fetch import FetchError, prepare  # noqa: E402
from reviewer.review import review_cohort  # noqa: E402

SAMPLES = ROOT / "data" / "samples"
RUBRIC = load_rubric()


def by_name(results):
    return {r["name"]: r for r in results}


@pytest.fixture(scope="module")
def cohort():
    return by_name(review_cohort(SAMPLES, RUBRIC))


def test_strong_beats_weak(cohort):
    assert cohort["s01_strong_leads"]["score"] > cohort["s06_weak_inventory"]["score"] + 40


def test_ranking_order_matches_intent(cohort):
    s = {k: v["score"] for k, v in cohort.items()}
    assert s["s01_strong_leads"] > s["s03_good_code_no_reports"] > s["s04_medium_wordfreq"] > s["s09_empty"]


def test_readme_only_does_not_score_well(cohort):
    assert cohort["s07_readme_only"]["band"] == "Needs work"
    code = next(c for c in cohort["s07_readme_only"]["criteria"] if c["key"] == "code_quality")
    assert code["score"] == 0


def test_padded_readme_gets_less_documentation_credit(cohort):
    padded = next(c for c in cohort["s12_padded_readme"]["criteria"] if c["key"] == "documentation")
    real = next(c for c in cohort["s04_medium_wordfreq"]["criteria"] if c["key"] == "documentation")
    assert padded["score"] < real["score"]


def test_renamed_copy_is_flagged_on_both_sides(cohort):
    a = [f["detail"] for f in cohort["s01_strong_leads"]["flags"]]
    b = [f["detail"] for f in cohort["s10_copy_of_s01_renamed"]["flags"]]
    assert any("s10_copy_of_s01_renamed" in d for d in a)
    assert any("s01_strong_leads" in d for d in b)


def test_unrelated_submissions_are_not_flagged(cohort):
    for name in ("s03_good_code_no_reports", "s04_medium_wordfreq", "s05_medium_regression", "s06_weak_inventory"):
        assert not [f for f in cohort[name]["flags"] if f["kind"] == "similarity"], name


def test_secret_is_flagged_and_routed(cohort):
    r = cohort["s11_committed_secret"]
    assert any(f["kind"] == "secrets" for f in r["flags"])
    assert r["needs_human_review"]


def test_every_score_is_in_range_and_has_feedback(cohort):
    for r in cohort.values():
        assert 0 <= r["score"] <= 100
        assert r["feedback"]["summary"]


def test_single_review_with_corpus_matches_cohort_flag():
    r = review_submission(SAMPLES / "s10_copy_of_s01_renamed", RUBRIC, corpus_dir=SAMPLES)
    assert any(f["kind"] == "similarity" for f in r["flags"])


def test_git_unavailable_reweights_instead_of_zeroing(tmp_path):
    (tmp_path / "README.md").write_text("# T\n\n## Overview\nThis explains the project in plain words here.\n")
    (tmp_path / "a.py").write_text('"""m"""\n\n\ndef f() -> int:\n    """d"""\n    return 1\n')
    r = review_submission(tmp_path, RUBRIC)
    git = next(c for c in r["criteria"] if c["key"] == "git_hygiene")
    assert git["available"] is False
    assert r["notes"]


def test_syntax_error_is_counted_not_crashing(tmp_path):
    (tmp_path / "broken.py").write_text("def f(:\n    pass\n")
    sig = analyze(tmp_path)
    assert sig.py.parse_errors == 1


def test_notebook_code_cells_are_analysed(tmp_path):
    nb = {"cells": [{"cell_type": "code", "source": ["!pip install x\n", "def f():\n", "    return 1\n"]}]}
    (tmp_path / "demo.ipynb").write_text(json.dumps(nb))
    sig = analyze(tmp_path)
    assert sig.py.functions == 1 and sig.has_entrypoint


def test_zip_with_unsafe_path_is_rejected(tmp_path):
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("../evil.txt", "x")
    with pytest.raises(FetchError):
        prepare(str(bad), tmp_path / "out")


def test_non_github_url_is_rejected():
    with pytest.raises(FetchError):
        prepare("https://example.com/owner/repo")


def test_zip_wrapper_folder_is_unwrapped(tmp_path):
    z = tmp_path / "s.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("proj/README.md", "# hi")
    out = prepare(str(z), tmp_path / "out")
    assert (out / "README.md").exists()


class FakeClient:
    class messages:
        last = None

        @classmethod
        def create(cls, **kwargs):
            cls.last = kwargs

            class Block:
                type = "text"
                text = "Friendly draft."

            class Resp:
                content = [Block()]

            return Resp()


def test_llm_polish_sends_findings_not_code(cohort):
    r = cohort["s01_strong_leads"]
    out = polish_with_llm(r, client=FakeClient)
    assert out == "Friendly draft."
    sent = FakeClient.messages.last["messages"][0]["content"]
    assert "def score_lead" not in sent
    assert "Do not invent" in FakeClient.messages.last["system"]


def test_llm_polish_returns_none_without_key(cohort, monkeypatch):
    for var in ("ANTHROPIC_API_KEY", "LLM_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    assert polish_with_llm(cohort["s01_strong_leads"]) is None


def test_llm_polish_works_with_any_openai_compatible_key(cohort, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example/v1/")
    monkeypatch.setenv("LLM_MODEL", "some-model")
    seen = {}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout):
        seen["url"], seen["auth"], seen["body"] = req.full_url, req.get_header("Authorization"), json.loads(req.data)
        return Resp(json.dumps({"choices": [{"message": {"content": "Friendly draft."}}]}).encode())

    monkeypatch.setattr("reviewer.feedback.urllib.request.urlopen", fake_urlopen)
    assert polish_with_llm(cohort["s01_strong_leads"]) == "Friendly draft."
    assert seen["url"] == "https://llm.example/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    assert seen["body"]["model"] == "some-model"
    assert "Do not invent" in seen["body"]["messages"][0]["content"]
    assert "def score_lead" not in seen["body"]["messages"][1]["content"]


def test_gitignored_junk_folder_is_not_penalised(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "a.py").write_text("x = 1\n")
    assert analyze(tmp_path).junk_dirs == ["__pycache__"]
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    assert analyze(tmp_path).junk_dirs == []


def test_missing_deliverables_alone_do_not_force_human_review(cohort):
    assert not cohort["s03_good_code_no_reports"]["needs_human_review"]


def test_short_readme_in_corpus_does_not_switch_off_readme_overlap():
    readme = " ".join(f"word{i}" for i in range(50))

    def entry(prefix, text):
        tokens = [f"{prefix}{i}" for i in range(80)]
        return {"raw": tokens, "struct": tokens, "readme": text}

    corpus = {"copy": entry("b", readme), "short": entry("c", "just five words here ok")}
    matches = similarity.compare(entry("a", readme), corpus, RUBRIC["similarity"])
    assert [m["other"] for m in matches] == ["copy"]
    assert matches[0]["reason"] == "README wording overlap"


def test_tests_folder_is_matched_as_a_path_segment(tmp_path):
    (tmp_path / "contests").mkdir()
    (tmp_path / "contests" / "solver.py").write_text("def solve():\n    return 1\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "helpers.py").write_text("def test_solve():\n    assert True\n")
    sig = analyze(tmp_path)
    assert sig.test_files == 1
    assert sig.py.functions == 1
