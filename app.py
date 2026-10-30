"""Streamlit demo: first-pass review of task submissions.

    streamlit run app.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from reviewer.feedback import polish_with_llm
from reviewer.fetch import FetchError, prepare
from reviewer.review import load_rubric, review_cohort, review_submission

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "data" / "samples"

st.set_page_config(page_title="Cynbit Review Assist", layout="wide")
st.title("Cynbit Review Assist")
st.caption(
    "First-pass triage of BitElevate task submissions. It scores against a rubric, shows the evidence "
    "for every score, and routes unclear cases to a person. Submitted code is read, never run."
)

rubric = load_rubric()


@st.cache_data(show_spinner=False)
def cached_cohort() -> list[dict]:
    return review_cohort(SAMPLES, rubric)


def show_result(r: dict, key: str) -> None:
    left, right = st.columns([1, 2])
    with left:
        st.metric("Score", f"{r['score']} / 100")
        st.write(f"**Band:** {r['band']}")
        if r["needs_human_review"]:
            st.warning("Needs human review")
            for reason in r["review_reasons"]:
                st.write(f"- {reason}")
        else:
            st.success("Clear enough for a quick skim")
        for note in r["notes"]:
            st.info(note)
    with right:
        for c in r["criteria"]:
            if not c["available"]:
                st.write(f"**{c['label']}**: not available")
                continue
            st.write(f"**{c['label']}** ({c['weight']:g}%)")
            st.progress(min(max(c["score"], 0.0), 1.0))
            with st.expander("Evidence"):
                for g in c["good"]:
                    st.write(f"+ {g}")
                for g in c["gaps"]:
                    st.write(f"- {g}")
    if r["flags"]:
        st.subheader("Flags")
        for f in r["flags"]:
            (st.error if f["severity"] == "high" else st.warning)(f["detail"])
    st.subheader("Draft feedback for the student")
    fb = r["feedback"]
    st.write(fb["summary"])
    cols = st.columns(2)
    with cols[0]:
        st.write("**Strengths**")
        for s in fb["strengths"] or ["Nothing stands out yet."]:
            st.write(f"+ {s}")
    with cols[1]:
        st.write("**To improve**")
        for s in fb["improvements"] or ["No major gaps found."]:
            st.write(f"- {s}")
    if st.button("Reword with an LLM (needs an API key)", key=f"llm_{key}"):
        text = polish_with_llm(r)
        st.write(text if text else "No API key set, or the call failed. The template feedback above still stands.")


mode = st.sidebar.radio("Mode", ["Sample cohort", "Review one submission"])
st.sidebar.caption("The sample cohort is synthetic: built to cover strong, partial, copied and broken work.")

if mode == "Sample cohort":
    results = sorted(cached_cohort(), key=lambda r: (not r["needs_human_review"], -r["score"]))
    st.subheader("Review queue")
    st.dataframe(
        [
            {
                "Submission": r["name"],
                "Score": r["score"],
                "Band": r["band"],
                "Human review": "yes" if r["needs_human_review"] else "no",
                "Flags": len(r["flags"]),
            }
            for r in results
        ],
        width="stretch",
        hide_index=True,
    )
    choice = st.selectbox("Open a submission", [r["name"] for r in results])
    show_result(next(r for r in results if r["name"] == choice), choice)
else:
    st.subheader("Review one submission")
    url = st.text_input("Public GitHub URL", placeholder="https://github.com/owner/repo")
    upload = st.file_uploader("...or upload a .zip", type=["zip"])
    compare = st.checkbox("Compare against the sample cohort for overlap", value=True)
    if st.button("Review") and (url or upload):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                if upload:
                    zip_path = Path(tmp) / "upload.zip"
                    zip_path.write_bytes(upload.getvalue())
                    folder = prepare(str(zip_path), Path(tmp) / "x")
                else:
                    folder = prepare(url, Path(tmp))
                result = review_submission(folder, rubric, SAMPLES if compare else None)
            show_result(result, "single")
        except FetchError as exc:
            st.error(str(exc))
