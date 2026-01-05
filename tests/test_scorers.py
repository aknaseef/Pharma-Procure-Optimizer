#!/usr/bin/env python3
"""Test individual scorers"""

from rapidfuzz import fuzz

supplier = "Panadol Advance 500mg"
master = "PANADOL ADVANCE 500MG TABLET"

print(f"Supplier: '{supplier}'")
print(f"Master: '{master}'")
print()
print(f"token_sort_ratio: {fuzz.token_sort_ratio(supplier, master)}")
print(f"partial_ratio: {fuzz.partial_ratio(supplier, master)}")
print(f"WRatio: {fuzz.WRatio(supplier, master)}")
print(f"ratio: {fuzz.ratio(supplier, master)}")
print(f"token_set_ratio: {fuzz.token_set_ratio(supplier, master)}")
