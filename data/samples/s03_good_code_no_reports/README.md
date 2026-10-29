# CSV Cleaner

## Overview
Helpers for tidying messy exports: normalising headers, parsing numbers written with commas or brackets, removing blank rows and dropping duplicates.

## Installation
```
pip install -r requirements.txt
```

## Usage
```
from cleaner import read_rows, drop_empty, dedupe
```
See report.py for a one-line summary of what changed.

## Running the tests
```
pytest -q
```
