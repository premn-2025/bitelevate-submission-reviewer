# Price Watchlist

## Overview
Fetches the latest price for a list of symbols from a market data API and prints them as a table.

## Installation
```
pip install -r requirements.txt
```

## Usage
```
python fetcher.py
```

## Approach
One request per symbol with a timeout, results gathered in a dictionary.
