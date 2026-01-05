#!/usr/bin/env python3
"""Quick test script to debug fuzzy matching"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup_db import MasterProduct
from logic import fuzzy_match

engine = create_engine('sqlite:///pharma.db')
Session = sessionmaker(bind=engine)
session = Session()

# Test cases from supplier sheet
test_names = [
    "Panadol Advance 500mg",
    "Augmentin 625mg",
    "Omez 20mg",
    "Panadol Blue Tabs (24s)",
    "Augmentin 625 Tab",
    "Vit C Effervescent",
]

print("=" * 80)
print("FUZZY MATCHING DEBUG TEST")
print("=" * 80)

for supplier_name in test_names:
    result = fuzzy_match(supplier_name, session)
    
    print(f"\nSupplier: '{supplier_name}'")
    if result:
        print(f"  ✓ MATCHED: {result['match_name']}")
        print(f"    Score: {result['score']}, Confidence: {result['confidence']}")
    else:
        print(f"  ✗ NO MATCH")
        
        # Try to find manually
        all_masters = session.query(MasterProduct).all()
        potential = [m for m in all_masters if supplier_name.upper().split()[0] in (m.simplified_name or "").upper()]
        if potential:
            print(f"    Potential matches found:")
            for p in potential[:3]:
                print(f"      - {p.simplified_name}")

session.close()
print("\n" + "=" * 80)
