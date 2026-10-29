# Technical Approach

How the BitElevate submission reviewer is built, why, how well it works so far, and how I would take it further.

## 1. Scope

Input: a submission as a folder, a zip file or a public GitHub URL.
Output: a score out of 100 with evidence for each rubric criterion, flags for secrets and overlap, a decision on whether a person must review it, and draft feedback for the student.

The tool reads files. It never executes, installs or imports submitted code.

## 2. Architecture

```
folder / zip / GitHub URL
        |
   fetch.py            safe extract or shallow clone (URL allowlist, zip-slip check)
        |
   analyzer.py         static signals: README, AST of Python/notebooks, tests, layout, git log
        |
   scoring.py          six rubric criteria, each with "good" and "gap" evidence
        |
   similarity.py       compare with other submissions (raw tokens and name-masked tokens)
        |
   review.py           integrity flags, human-review routing, overall score and band
        |
   feedback.py         template feedback (default) -> optional LLM rewording
        |
   cli.py / app.py     command line and Streamlit review queue
```

`data/rubric.json` holds the weights, band cutoffs, routing thresholds and the list of required deliverables, so Cynbit can change these without touching code. The individual checks inside each criterion, and their thresholds, are still set in `scoring.py`.

## 3. Data pipeline

1. **Collect.** Walk the folder, skip `.git` and dependency folders, cap the file count and file size. Remember junk folders (venv, node_modules, `__pycache__`) unless the project's own `.gitignore` excludes them.
2. **Extract signals.**
   - README: word count, headings, which headings have real content beneath them, code blocks, mention of tests.
   - Python and notebook code cells, through `ast`: parse errors, functions, docstrings, type hints, function length, bare `except`, test functions and assertions.
   - Layout: dependency file, `.gitignore`, entrypoint, `.env` handling.
   - Git: commit subjects from `git log`, or a `_commits.txt` fixture for the samples.
   - Secrets: three regular expressions for key-like strings.
3. **Score.** Each criterion is a list of weighted checks. Every check records either a "good" or a "gap" sentence, which is the evidence shown to the reviewer.
4. **Compare.** Python is tokenised twice: as written, and with names, strings and numbers masked. TF-IDF over token n-grams and cosine similarity give a raw and a structural score against every other submission. README wording is also compared, using word trigrams, but only among READMEs of 40 or more words.
5. **Route.** A submission goes to a person if it has a high-severity flag, sits within 4 points of a band cutoff, shows docs, code and tests that strongly disagree, or has almost no content.
6. **Write feedback.** Strengths and improvements come straight from the evidence. Strengths are ordered by criterion score, improvements by weight times shortfall.

## 4. Method choices and alternatives

| Decision | Chosen | Alternatives | Why |
|---|---|---|---|
| Scoring | Transparent rules over static signals | LLM as judge; a model trained on past grades | No labelled history exists yet, rules can be audited line by line, and a score needs to be explainable to a student. An LLM judge is the planned second stage for things rules cannot see, such as whether the approach makes sense |
| Overlap | TF-IDF on token n-grams, raw and name-masked | Embeddings; winnowing or MOSS-style fingerprints | Cheap, deterministic, and the masked view survives renaming. Embeddings would add false matches between unrelated but similar-looking code |
| Task fit | Keyword match on headings, file names and text | LLM reading of the reports | Shallow on purpose. It proves a deliverable exists, not that it is good |
| Feedback | Template first, LLM optional | LLM only | The tool works with no API key and no data leaving the machine |
| Execution | None | Run tests in a sandbox | Running untrusted code needs real isolation; out of scope for a first version |

## 5. LLM step and prompt design

The optional step (`feedback.polish_with_llm`) rewords the template feedback into one friendly paragraph.

- **Input.** Only the structured findings: band, score, strengths, improvements and flag text. No source code or README text is sent, and neither is the submission's own name. Overlap flags do name the other submission's folder, which could be a student's name.
- **System prompt.** Use only the given findings, invent nothing, no scores of its own, at most 140 words, say once that this is a draft for the human reviewer.
- **Settings.** Low temperature (0.2), short output cap.
- **Failure behaviour.** No API key, a missing package or any error returns `None`, and the template feedback is used.
- **Testing.** A unit test passes a fake client and checks that a function definition from the sample is not in the payload and that the system prompt contains the "Do not invent" instruction. I have not run it against a live model in this build, so wording quality is untested.

If the LLM step grew into judging, I would add a fixed output schema, a held-out set of human-graded examples, and a check that every claim in the output maps to a given finding.

## 6. Evaluation

**Setup.** `python evals/run_eval.py` scores 13 synthetic submissions and compares them with scores I wrote in `evals/labels.json` before the first run. The set covers strong work, partial work, README-only work, an empty upload, a padded README, a committed secret and two copies (one with renamed identifiers, one verbatim).

**Results (final run).**

| Measure | Value |
|---|---|
| Rank agreement with labels (Spearman) | 0.935 |
| Mean absolute error | 8.5 points |
| Band exactly right | 7 of 13 |
| Band within one step | 13 of 13 |
| Copied pairs caught | 2 of 2, no false pairs |
| Committed secret caught | 1 of 1, no false alarms |
| Routed to a human | 12 of 13 |

**Where it disagrees with the labels.** The weak inventory script scored 40.3 against my 25, the padded README 42.2 against 25, and the code-only submission 33.9 against 40. The two copies and the secret sample scored lower than my labels because my labels judged intent and ignored what those samples lack: all three are missing the reports, the verbatim copy and the secret sample have no tests, and the renamed copy has tests but a thinner README and git history; I did not change the labels afterwards, so these gaps stay in the table.

**Honest caveats.**

- The samples are synthetic and I wrote both the samples and the labels. This checks the tool against my intent, not against independent reviewers. It cannot show how the tool behaves on real student work.
- 13 samples is far too few for any reliable statistic.
- The set is built from edge cases, so the 12 of 13 routing rate says nothing about a real cohort. With a 4-point margin around three band cutoffs, roughly a third of a real cohort could be routed on borderline grounds alone. That margin is the lever that sets the review queue's size.
- I changed the tool after seeing results, so the final numbers are not an independent test. The changes were:
  1. The first run of the eval was polluted by `__pycache__` folders that pytest had created inside the samples, which the structure check counted as committed junk. I fixed the check so a folder the project's own `.gitignore` excludes is not penalised, and re-ran.
  2. The padded README scored too high because a heading earned credit even with nothing under it. Sections now count only with real content. It still scored 42.2 against a label of 25, so the defence is only partial.
  3. The renamed copy had a structure similarity of 1.0 but a raw similarity of 0.48 and slipped under a rule that required both views to be high. Unrelated pairs never exceeded 0.18 on structure. I made the structure view enough on its own. A shared starter template would push unrelated submissions up, so this threshold needs real data.
  4. Most routing reasons were "criteria disagree", triggered by zeros for missing deliverables. Only docs, code and tests can now contradict each other.

  The commit history was reorganised into logical steps after development, so the commit order does not match the order in which I found these issues.

## 7. Safety and privacy

- Submitted code is never run or imported. Notebook `!` and `%` lines are neutralised before parsing.
- Zip files are checked for unsafe paths and size before extraction. GitHub URLs must match `https://github.com/owner/repo`, and the clone is shallow with a timeout.
- Secrets are reported as a flag with a file name, never echoed back in full.
- A person makes the final decision on every submission. The tool states why it is unsure.
- Overlap is worded as "needs a human look", never as an accusation.

## 8. Known limitations

- Code metrics understand Python and notebooks only. JavaScript, TypeScript and other languages score zero on code quality and also miss the entrypoint, multi-module, proof-of-concept and overlap checks, which would be unfair until fixed.
- No check that the code runs or the tests pass.
- Docstring and function-length checks are proxies for quality, not quality itself.
- Keyword checks for deliverables can be gamed by stuffing words in a README.
- Thresholds and weights are set by hand and unvalidated on real data.
- Sub-check thresholds (README length, docstring share, test count, function length and the rest) are hard-coded in `scoring.py`, not in the rubric file.
- The routing margin is broad: 4 points either side of three cutoffs covers a 24-point slice of the scale.
- When a submission has no `.git` folder, a `_commits.txt` file is trusted as its history, so a student could fake one.
- `git log` runs on a `.git` folder that came from the student's zip. It does not run their code, but it is git working on an untrusted repository.
- Overlap flags include the other submission's folder name, which reaches the reviewer and, if the LLM step is on, the LLM.

## 9. Execution plan

| Phase | Work | Exit check |
|---|---|---|
| 0, weeks 1-2 | Collect 50 to 100 past submissions with reviewer grades (with consent), replace my rubric with Cynbit's, fix label noise | Rubric agreed with the people who grade |
| 1, weeks 3-4 | Add JavaScript and TypeScript support; calibrate weights and routing margin against the graded set | Spearman at or above 0.8 and band within one step at least 90 percent on a held-out part of the set |
| 2, weeks 5-6 | Shadow mode: the tool runs beside human reviewers and nothing is shown to students | Reviewer minutes per submission and disagreement cases recorded |
| 3, weeks 7-8 | Add sandboxed test execution and an LLM judge for rubric items that need reading, each checked against graded examples | Judge agrees with reviewers at least as well as reviewers agree with each other |
| 4, after that | Draft feedback shown to students after a reviewer approves it; portal integration | Student and reviewer satisfaction, appeal rate |

Stop conditions: if agreement stays low after calibration, or the overlap flag keeps firing on shared templates, narrow the tool to a checklist and keep the person as the grader.

## 10. Running it

```
pip install -r requirements.txt
python -m pytest -q
python evals/run_eval.py
streamlit run app.py
python -m reviewer.cli data/samples --cohort
```
