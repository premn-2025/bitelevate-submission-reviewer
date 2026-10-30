# Cynbit Review Assist

A first-pass reviewer for BitElevate-style task submissions. It scores a repository against a rubric, shows the evidence behind every score, flags committed secrets and copied work, and sends unclear cases to a person. It reads submissions; it never runs them.

Built for the Cynbit Technologies AI/ML Engineer Intern assessment ("Identify an AI Opportunity for Cynbit").

**Live demo:** https://bitelevate.streamlit.app/ (sample cohort, no sign-in needed; free tier, so it may take a few seconds to wake up)

## Deliverables

| Deliverable | Where |
|---|---|
| AI Opportunity Report | [docs/opportunity-report.md](docs/opportunity-report.md) |
| Proof of concept | this repository (`reviewer/`, `app.py`) |
| Technical Approach Report | [docs/technical-approach.md](docs/technical-approach.md) |
| Live demo | https://bitelevate.streamlit.app/ |

## Quick start

```
pip install -r requirements.txt
python -m pytest -q                              # 22 tests
python -m reviewer.cli data/samples --cohort     # review the sample cohort
python -m reviewer.cli path/to/submission        # review one folder
python -m reviewer.cli https://github.com/owner/repo --corpus data/samples
streamlit run app.py                             # review queue in the browser
python evals/run_eval.py                         # compare against labels
```

No API key is needed. With a key, `--llm` (or the button in the app) rewords the feedback; it sends only the structured findings, never the code. It uses Anthropic if `ANTHROPIC_API_KEY` is set and the `anthropic` package is installed. Otherwise it uses `LLM_API_KEY` (or `OPENAI_API_KEY`) with any OpenAI-compatible API, such as OpenAI, Gemini, Groq, OpenRouter or a local Ollama; set `LLM_BASE_URL` and `LLM_MODEL` for providers other than OpenAI.

## What it checks

Six criteria, weights in `data/rubric.json`: documentation (20), code quality (25), testing (15), structure and reproducibility (15), git history (10), and whether the required deliverables exist (15). Separately it looks for committed secrets, overlap with other submissions (including copies with renamed variables), single-commit uploads and placeholder text.

## Layout

```
reviewer/    analyzer, scoring, similarity, review pipeline, feedback, fetch, cli
app.py       Streamlit review queue
data/        rubric.json, synthetic sample cohort and the script that builds it
evals/       labels and the evaluation script
tests/       pytest suite
docs/        the two written reports
```

## Results so far

On 13 synthetic submissions, with labels I wrote myself: rank agreement 0.935, mean error 8.5 points, band within one step 13 of 13, both copied pairs caught, the committed secret caught, no false alarms. 12 of 13 were routed to a person, because the set is built from edge cases.

Please read the caveats in the [technical approach](docs/technical-approach.md#6-evaluation) before relying on these numbers. The samples are synthetic, I wrote both the samples and the labels, and I adjusted the tool after seeing results. This shows the idea works on cases I designed, not that it works on real student submissions.

## Limits

Code metrics only understand Python and notebooks. Nothing here checks that submitted code runs. Thresholds and weights are hand-set and have not been validated on real data. Overlap flags mean "a person should look", not "copied".
