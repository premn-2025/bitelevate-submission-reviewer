# Review Sentiment Triage

## Overview
Customer reviews pile up and negative ones are found late. This project labels each review as positive, neutral or negative with a transparent word-list method, so unhappy customers can be contacted first. It is meant as a baseline that a heavier model has to beat.

## Installation
```
pip install -r requirements.txt
```

## Usage
```
python run.py reviews.txt
```
The file holds one review per line and the output is the count for each label.

## Approach
Text is lower-cased and tokenised with a regular expression. A positive and a negative word list give a polarity score and a negator word flips the sign of the next word. A lexicon was chosen because it is fast, explainable and needs no training data.

## Results
On 40 hand-labelled reviews the baseline reached about 0.72 accuracy, with most errors on sarcasm. The test suite has six cases for tokenising, negation and counting.

## Limitations
The method cannot handle sarcasm, mixed opinions or other languages. Next steps are a small fine-tuned classifier and a comparison against this baseline.

## Running the tests
```
pytest -q
```
