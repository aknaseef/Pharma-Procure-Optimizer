import re
from typing import Optional, Dict, Any
from rapidfuzz import process, fuzz
from sqlalchemy.orm import Session
from setup_db import ProductAlias, MasterProduct
from config import (
    MATCH_CUTOFF_TOKEN_SORT, MATCH_CUTOFF_TOKEN_SET, MATCH_CUTOFF_PARTIAL,
    MATCH_SCORE_TOLERANCE, CONFIDENCE_HIGH_SCORE, CONFIDENCE_MEDIUM_SCORE,
    DEFAULT_PACK_SIZE
)

def parse_pack_size(pack_input):
    """
    Tries to infer integer pack size from string or number.
    e.g. "24s" -> 24, "100ml" -> 1 (treat as 1 unit of product?), 
    "10x10" -> 100.
    Default to 1.
    """
    if not pack_input:
        return 1
    
    s = str(pack_input).lower()
    
    # Check "10x10"
    match_x = re.match(r"(\d+)\s*[x\*]\s*(\d+)", s)
    if match_x:
        return int(match_x.group(1)) * int(match_x.group(2))
    
    # Check digits
    match_digits = re.search(r"(\d+)", s)
    if match_digits:
        return int(match_digits.group(1))
    
    return 1

def calculate_euc(price: float, pack_size: int = 1, bonus_string: str = None):
    """
    Calculates Effective Unit Cost (EUC).
    Returns (EUC_Total_Deal, Margin, Normalized_Unit_Cost)
    
    Note: 'price' is typically the price for the 'pack_size'.
    """
    # 1. Logic for Bonus
    # "10+2" means Buy 10 @ Price, Get 12 total.
    # Usually Price input is for the 'Buy' quantity or Unit Price?
    # Industry standard in this context often: Price is for 1 Pack.
    # Deal 10+2: Buy 10 Packs, Get 12 Packs.
    # Total Cost = 10 * Price. Total Qty = 12 * pack_size.
    # This function's signature is for a single line item.
    # Let's assume 'price' is "Unit Price of 1 Pack".
    
    effective_pack_price = price
    
    if bonus_string:
        match_plus = re.match(r"(\d+)[\+/](\d+)", bonus_string)
        if match_plus:
            buy_qty = int(match_plus.group(1))
            free_qty = int(match_plus.group(2))
            if buy_qty > 0:
                total_qty = buy_qty + free_qty
                # Factor: I pay for 'buy_qty', I get 'total_qty'.
                # Effective Price per pack = Price * (Buy / Total)
                effective_pack_price = price * (buy_qty / total_qty)

        match_perc = re.match(r"Bonus\s*(\d+)%", bonus_string, re.IGNORECASE)
        if match_perc:
            percent = float(match_perc.group(1))
            # Buy 100, get 100 + P
            effective_pack_price = price * (100 / (100 + percent))

    euc = effective_pack_price
    margin = 0.0 # Calculate based on Selling Price if we had it, else 0
    
    # Normalized Cost (Cost Per Tablet/Unit)
    normalized_cost = euc / max(1, pack_size)
    
    return round(euc, 4), round(margin, 2), round(normalized_cost, 4)


def fuzzy_match(raw_name: str, db_session: Session, supplier_price: float = None):
    """
    Fuzzy match supplier product name to master product.
    If supplier_price is provided, uses it to disambiguate between similar products.
    
    Args:
        raw_name: Supplier product name
        db_session: Database session
        supplier_price: Optional supplier price to help disambiguate pack sizes
    
    Returns:
        Dict with match_name, master_id, score, confidence or None
    """
    # First check for exact alias match
    alias = db_session.query(ProductAlias).filter(ProductAlias.alias_name == raw_name).first()
    if alias:
        return {
            "match_name": alias.master_product.product_name,
            "master_id": alias.master_product.id,
            "score": 100,
            "confidence": "High (Alias)"
        }

    # Normalize to uppercase for better matching (case-insensitive)
    raw_name_normalized = raw_name.upper().strip()
    
    # Use simplified_name for fuzzy matching, but also get standard_cost for price matching
    masters = db_session.query(
        MasterProduct.id, 
        MasterProduct.simplified_name, 
        MasterProduct.product_name,
        MasterProduct.standard_cost
    ).all()
    
    # Build dict with simplified_name as the searchable text (uppercase)
    master_dict = {m.id: (m.simplified_name or m.product_name).upper() for m in masters}
    master_full_names = {m.id: m.product_name for m in masters}
    master_prices = {m.id: m.standard_cost for m in masters}
    
    if not master_dict:
        return None

    # Try multiple matching strategies with STRICT cutoffs to avoid false positives
    scorers = [
        (fuzz.token_sort_ratio, MATCH_CUTOFF_TOKEN_SORT),
        (fuzz.token_set_ratio, MATCH_CUTOFF_TOKEN_SET),
        (fuzz.partial_ratio, MATCH_CUTOFF_PARTIAL),
    ]
    
    # Get top candidates from each scorer
    all_candidates = []
    
    for scorer, cutoff in scorers:
        matches = process.extract(
            raw_name_normalized,
            master_dict,
            scorer=scorer,
            score_cutoff=cutoff,
            limit=10  # Get top 10 from each
        )
        
        for match_name, score, master_id in matches:
            all_candidates.append((master_id, score, scorer.__name__))
    
    if not all_candidates:
        return None
    
    # Sort by score descending
    all_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # If we have supplier price, use it to disambiguate top matches
    if supplier_price and supplier_price > 0:
        # Get top score
        top_score = all_candidates[0][1]
        
        # Get all matches within tolerance of top score
        close_matches = [c for c in all_candidates if c[1] >= top_score - MATCH_SCORE_TOLERANCE]
        
        if len(close_matches) > 1:
            # Multiple similar matches - use price to pick best
            best_match_id = None
            best_price_diff = float('inf')
            
            for master_id, score, _ in close_matches:
                master_price = master_prices.get(master_id, 0) or 0
                price_diff = abs(supplier_price - master_price)
                
                if price_diff < best_price_diff:
                    best_price_diff = price_diff
                    best_match_id = master_id
            
            # Use price-selected match
            final_match = best_match_id
            final_score = next(c[1] for c in close_matches if c[0] == best_match_id)
        else:
            # Only one good match
            final_match = close_matches[0][0]
            final_score = close_matches[0][1]
    else:
        # No price info - just use best name match
        final_match = all_candidates[0][0]
        final_score = all_candidates[0][1]
    
    confidence = "Low"
    if final_score >= CONFIDENCE_HIGH_SCORE:
        confidence = "High"
    elif final_score >= CONFIDENCE_MEDIUM_SCORE:
        confidence = "Medium"
        
    return {
        "match_name": master_full_names[final_match],
        "master_id": final_match,
        "score": round(final_score, 2),
        "confidence": confidence
    }


