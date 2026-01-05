#!/usr/bin/env python3
"""Test price-based disambiguation"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from logic import fuzzy_match

engine = create_engine('sqlite:///pharma.db')
Session = sessionmaker(bind=engine)
session = Session()

# Test case: Panadol Advance with different prices
test_cases = [
    ("Panadol Advance", None, "No price"),
    ("Panadol Advance", 10.0, "10 AED (should match 24-pack)"),
    ("Panadol Advance", 18.0, "18 AED (should match 48-pack)"),
    ("Panadol Advance", 35.0, "35 AED (should match 96-pack)"),
]

print("=" * 80)
print("PRICE-BASED DISAMBIGUATION TEST")
print("=" * 80)

for name, price, description in test_cases:
    result = fuzzy_match(name, session, price)
    
    print(f"\nTest: {description}")
    print(f"  Input: '{name}' @ {price} AED" if price else f"  Input: '{name}' (no price)")
    
    if result:
        print(f"  ✓ Matched: {result['match_name']}")
        print(f"    Score: {result['score']}, Confidence: {result['confidence']}")
    else:
        print(f"  ✗ NO MATCH")

session.close()
print("\n" + "=" * 80)
