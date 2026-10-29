# Technical Approach

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
