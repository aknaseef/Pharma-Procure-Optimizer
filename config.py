"""
Configuration settings for Pharma-Procure Optimizer.
Edit these values to customize the application behavior.
"""

# =============================================================================
# DATABASE SETTINGS
# =============================================================================
DATABASE_PATH = "sqlite:///pharma.db"

# =============================================================================
# RISK ASSESSMENT THRESHOLDS (in days)
# =============================================================================
RISK_HIGH_DAYS = 180      # Less than 6 months = High Risk
RISK_MEDIUM_DAYS = 365    # Less than 12 months = Medium Risk

# =============================================================================
# FUZZY MATCHING SETTINGS
# =============================================================================
# Higher scores = stricter matching = fewer false positives
# Note: Pharmaceutical products require high precision due to safety concerns
MATCH_CUTOFF_TOKEN_SORT = 85    # token_sort_ratio minimum score (was 70)
MATCH_CUTOFF_TOKEN_SET = 85     # token_set_ratio minimum score (was 75)
MATCH_CUTOFF_PARTIAL = 90       # partial_ratio minimum score (was 85)
MATCH_SCORE_TOLERANCE = 3       # Points within top score for disambiguation (was 5)

# Confidence levels
CONFIDENCE_HIGH_SCORE = 95      # Increased from 90 for higher confidence
CONFIDENCE_MEDIUM_SCORE = 85    # Increased from 75

# Pharmaceutical Formulation Stopwords
# These common terms should be excluded from matching to prevent false positives
# Example: "Lantus Syrup" and "ACTIFED Syrup" shouldn't match just because both have "Syrup"
PHARMA_STOPWORDS = [
    # Dosage forms
    'tablet', 'tablets', 'tab', 'tabs',
    'capsule', 'capsules', 'cap', 'caps',
    'syrup', 'syrups', 'suspension', 'suspensions',
    'injection', 'injections', 'inj',
    'solution', 'solutions', 'sol',
    'cream', 'creams',
    'ointment', 'ointments',
    'gel', 'gels',
    'lotion', 'lotions',
    'drops', 'drop',
    'spray', 'sprays',
    'powder', 'powders',
    'granules', 'granule',
    'sachet', 'sachets',
    'vial', 'vials',
    'ampoule', 'ampoules', 'ampule', 'ampules',
    'inhaler', 'inhalers',
    'suppository', 'suppositories', 'supp',
    'patch', 'patches',
    'film', 'films',
    
    # Common packaging terms
    'bottle', 'bottles', 'btl',
    'box', 'boxes',
    'blister', 'blisters',
    'strip', 'strips',
    'tube', 'tubes',
    'pack', 'packs',
    'jar', 'jars',
    
    # Common descriptors (low value for matching)
    'mg', 'ml', 'gm', 'mcg', 'iu',
    'per', 'each', 'unit', 'units',
]

# =============================================================================
# DEFAULT VALUES
# =============================================================================
DEFAULT_CREDIT_DAYS = 30
DEFAULT_PACK_SIZE = 1

# =============================================================================
# FILE UPLOAD LIMITS
# =============================================================================
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = ["xlsx", "csv"]

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL = "INFO"
LOG_FILE = "pharma_procure.log"
