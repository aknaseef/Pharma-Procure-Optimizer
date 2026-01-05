import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup_db import MasterProduct

def simplify_product_name(raw_name):
    """
    Simplifies detailed MOH product names to core components for better matching.
    
    Examples:
    "0.2% CIPROFLOXACIN in 0.9% W/V SODIUM CHLORIDE INJECTION USP Infusion/Solution for, 100ml Plastic Bag"
    -> "CIPROFLOXACIN SODIUM CHLORIDE"
    
    "PARACETAMOL 500MG TABLETS BP, 24's Blister Pack"
    -> "PARACETAMOL 500MG TABLETS"
    """
    if not raw_name:
        return ""
    
    name = raw_name.upper().strip()
    
    # Remove common noise patterns
    noise_patterns = [
        r'\bBP\b',
        r'\bUSP\b',
        r'\bB\.P\.\b',
        r'\bU\.S\.P\.\b',
        r'INFUSION/SOLUTION FOR',
        r'INFUSION FOR',
        r'SOLUTION FOR',
        r'INJECTION FOR',
        r',.*$',  # Remove everything after comma (packaging details)
        r'\d+ML PLASTIC BAG',
        r'\d+ML PLASTIC BOTTLE',
        r'\d+ML GLASS VIAL',
        r'\d+ML GLASS BOTTLE',
        r'PLASTIC BAG',
        r'PLASTIC BOTTLE',
        r'GLASS VIAL',
        r'GLASS BOTTLE',
        r'BLISTER PACK',
        r'STRIP',
        r'\d+\'S\b',
        r'\d+S\b',
    ]
    
    for pattern in noise_patterns:
        name = re.sub(pattern, ' ', name, flags=re.IGNORECASE)
    
    # Remove "in X%" patterns (concentrations in solutions)
    name = re.sub(r'\bIN\s+\d+\.?\d*%\s+W/V\b', ' ', name)
    name = re.sub(r'\bW/V\b', ' ', name)
    
    # Clean up extra spaces
    name = ' '.join(name.split())
    
    # Extract first meaningful part (before "INJECTION", "INFUSION", "TABLET")
    # But keep the dosage form if it's the main descriptor
    match = re.match(r'^(.*?)\s+(INJECTION|INFUSION|TABLET|CAPSULE|SYRUP|SUSPENSION)', name)
    if match:
        core = match.group(1) + ' ' + match.group(2)
        name = core
    
    return name.strip()

if __name__ == "__main__":
    # Connect to database
    engine = create_engine('sqlite:///pharma.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products
    products = session.query(MasterProduct).all()
    
    print(f"Processing {len(products)} products...")
    
    count = 0
    for product in products:
        simplified = simplify_product_name(product.product_name)
        product.simplified_name = simplified
        count += 1
        
        if count <= 10:  # Show first 10 examples
            print(f"\nOriginal: {product.product_name[:80]}...")
            print(f"Simplified: {simplified}")
    
    session.commit()
    session.close()
    
    print(f"\n✓ Successfully simplified {count} product names!")
