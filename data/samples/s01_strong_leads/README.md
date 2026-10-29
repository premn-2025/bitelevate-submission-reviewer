# Lead Scorer

## Overview
Inbound inquiries arrive faster than a small sales team can read them. This tool gives every inquiry a 0-100 score from three signals the team already checks by hand: budget, the services mentioned, and how soon the client wants to start. It then sorts leads into hot, warm and cold so the first reply goes to the people most likely to become projects.

## Installation
```
pip install -r requirements.txt
```
The scorer uses only the standard library; the requirements file is just pytest for the tests.

## Usage
```
python app.py "Acme Ltd" 250000 8 need crm automation and an ai agent
```
The arguments are company, budget in rupees, timeline in weeks, then the free-text message.

## Approach
Each signal is a small pure function, so the rules can be read and changed without touching the rest. Budget uses fixed tiers, keywords add points per service, and urgency rewards short timelines. The total is capped at 100. Rules were preferred over a trained model because there is no labelled history of won and lost leads to learn from yet.

## Results
On eight unit tests the bands behave as intended. On twenty hand-labelled example inquiries the hot band matched the team's own judgement in 17 cases. Tests live in tests/ and cover each function and the end-to-end path.

## Limitations
The keyword list is short and English-only. Weights are guesses and should be recalibrated once real outcomes are available. Next steps are logging outcomes and fitting weights from them.

## Running the tests
```
pytest -q
```
