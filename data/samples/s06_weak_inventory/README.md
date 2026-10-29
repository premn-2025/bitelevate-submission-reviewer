# Inventory Checker

## Overview
Reads an inventory CSV and prints total value, low stock items and the most stocked item. Written quickly to see what the data looks like before building anything bigger.

## Installation
```
pip install -r requirements.txt
```

## Usage
```
python main.py inventory.csv
```

## Approach
One pass over the file, collecting totals and flags as it goes.

## Limitations
No tests yet. Error handling is minimal.
