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
MATCH_CUTOFF_TOKEN_SORT = 70    # token_sort_ratio minimum score
MATCH_CUTOFF_TOKEN_SET = 75     # token_set_ratio minimum score
MATCH_CUTOFF_PARTIAL = 85       # partial_ratio minimum score
MATCH_SCORE_TOLERANCE = 5       # Points within top score for disambiguation

# Confidence levels
CONFIDENCE_HIGH_SCORE = 90
CONFIDENCE_MEDIUM_SCORE = 75

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
