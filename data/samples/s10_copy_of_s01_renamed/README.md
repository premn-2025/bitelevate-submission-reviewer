# Inquiry Rating Tool

## Overview
A small tool that rates incoming inquiries between zero and one hundred so the team can reply to the most promising ones first. It looks at the money available, the services asked about and the time the client has.

## Installation
```
pip install -r requirements.txt
```

## Usage
```
python app.py "Acme Ltd" 250000 8 need crm automation
```

## Approach
Three small functions each return points and the sum is capped at one hundred.

## Results
Unit tests pass for each function.

## Limitations
The word list is short.

## Running the tests
```
pytest -q
```
