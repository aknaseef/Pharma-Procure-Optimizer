#!/usr/bin/env python3
"""Test specific problem cases"""

from rapidfuzz import fuzz

# Problem cases from user
test_cases = [
    ("Panadol Blue Tabs (24s)", "CHILDREN'S PANADOL 5-12 YEARS SYRUP"),
    ("Vit C Effervescent", "CALCIUM C 1000 SANDOZ ORANGE TABLET"),
    ("Prime Calamine Lotion", "ACNE-AID (TINIFED) TOPICAL LOTION"),
    ("Betadine Sol 500ml", "DEPAKINE 500MG TABLET"),
]

print("Testing why these matched incorrectly:")
print("=" * 80)

for supplier, wrong_match in test_cases:
    supplier_norm = supplier.upper()
    print(f"\nSupplier: '{supplier}'")
    print(f"Wrong Match: '{wrong_match}'")
    print(f"  token_sort_ratio: {fuzz.token_sort_ratio(supplier_norm, wrong_match)}")
    print(f"  partial_ratio: {fuzz.partial_ratio(supplier_norm, wrong_match)}")
    print(f"  WRatio: {fuzz.WRatio(supplier_norm, wrong_match)}")
