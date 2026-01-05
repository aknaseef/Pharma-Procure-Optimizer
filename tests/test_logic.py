"""
Automated tests for Pharma-Procure Optimizer
Run with: pytest tests/ -v
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import parse_pack_size, calculate_euc, fuzzy_match
from config import (
    MATCH_CUTOFF_TOKEN_SORT, MATCH_CUTOFF_TOKEN_SET, 
    CONFIDENCE_HIGH_SCORE, CONFIDENCE_MEDIUM_SCORE
)


class TestParsePackSize:
    """Tests for pack size parsing function"""
    
    def test_simple_number(self):
        assert parse_pack_size("24") == 24
        assert parse_pack_size("100") == 100
    
    def test_with_suffix(self):
        assert parse_pack_size("24s") == 24
        assert parse_pack_size("100ml") == 100
        assert parse_pack_size("50tabs") == 50
    
    def test_multiplication(self):
        assert parse_pack_size("10x10") == 100
        assert parse_pack_size("5*20") == 100
        assert parse_pack_size("3 x 10") == 30
    
    def test_none_or_empty(self):
        assert parse_pack_size(None) == 1
        assert parse_pack_size("") == 1
    
    def test_no_number(self):
        assert parse_pack_size("bottle") == 1


class TestCalculateEUC:
    """Tests for Effective Unit Cost calculation"""
    
    def test_basic_calculation(self):
        euc, margin, norm_cost = calculate_euc(100.0, 10)
        assert norm_cost == 10.0  # 100 / 10
    
    def test_with_bonus_plus(self):
        # 10+2 deal: buy 10, get 12 total
        euc, margin, norm_cost = calculate_euc(100.0, 10, "10+2")
        # Effective price = 100 * (10/12) = 83.33
        # Norm cost = 83.33 / 10 = 8.33
        assert norm_cost == pytest.approx(8.333, rel=0.01)
    
    def test_with_bonus_percent(self):
        # Bonus 10% means get 110 for price of 100
        euc, margin, norm_cost = calculate_euc(100.0, 10, "Bonus 10%")
        # Effective price = 100 * (100/110) = 90.91
        assert norm_cost == pytest.approx(9.09, rel=0.01)
    
    def test_no_bonus(self):
        euc, margin, norm_cost = calculate_euc(50.0, 25, None)
        assert norm_cost == 2.0


class TestConfigConstants:
    """Tests to verify config constants are reasonable"""
    
    def test_cutoffs_are_reasonable(self):
        assert 50 <= MATCH_CUTOFF_TOKEN_SORT <= 100
        assert 50 <= MATCH_CUTOFF_TOKEN_SET <= 100
    
    def test_confidence_thresholds(self):
        assert CONFIDENCE_MEDIUM_SCORE < CONFIDENCE_HIGH_SCORE
        assert CONFIDENCE_HIGH_SCORE <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
