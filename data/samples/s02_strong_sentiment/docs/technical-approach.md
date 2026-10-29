# Technical Approach

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
