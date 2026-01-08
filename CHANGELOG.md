# CHANGELOG

All notable changes to the Pharma-Procure Optimizer project will be documented in this file.

## [2.1.0] - 2026-01-08

### 🎯 Major Features Added

#### PDF to Excel Converter
- **New Feature**: Convert PDF supplier price lists directly to Excel within the app
- Automatic table extraction from multi-page PDFs
- Smart column detection and mapping interface
- Handles repeated headers across pages (like MOH price lists)
- One-click download of converted Excel files
- Integrated into Upload & Process tab

#### Public Selling Price Validation
- **Regulatory Compliance**: Track official public selling prices separately from net rates
- Database schema enhancement with `public_selling_price` column
- Automatic price validation during product matching
- Price mismatch detection and warnings
- Tolerance of 0.01 AED for rounding differences
- New "Price Mismatch" filter in Matching Workbench
- Enhanced display columns: Net Rate, Public Price, Master Price, Price Match Status

#### Improved Product Matching (Critical Fix)
- **Stricter Matching Thresholds**: Increased from 70-75% to 85-90% similarity
- **Pharmaceutical Stopword Filtering**: Added 50+ common terms excluded from matching
  - Dosage forms: tablet, syrup, injection, capsule, cream, ointment, gel, lotion, etc.
  - Packaging terms: bottle, box, blister, tube, jar, etc.
  - Prevents false matches like "Lantus Syrup" ↔ "ACTIFED Syrup"
- **Enhanced Confidence Levels**: High confidence now requires 95% similarity (was 90%)

### 🔧 Technical Improvements

#### Database
- Added `public_selling_price` column to `supplier_offers` table
- Created migration script for seamless schema updates
- Backward compatible with existing data

#### Matching Logic (`logic.py`)
- New `remove_pharma_stopwords()` function
- Updated `fuzzy_match()` to accept and validate public prices
- New `_validate_price()` helper for price comparison
- Returns comprehensive match results including price validation

#### Configuration (`config.py`)
- New `PHARMA_STOPWORDS` list with 50+ pharmaceutical terms
- Increased `MATCH_CUTOFF_TOKEN_SORT` from 70 to 85
- Increased `MATCH_CUTOFF_TOKEN_SET` from 75 to 85
- Increased `MATCH_CUTOFF_PARTIAL` from 85 to 90
- Increased `CONFIDENCE_HIGH_SCORE` from 90 to 95
- Increased `CONFIDENCE_MEDIUM_SCORE` from 75 to 85

#### PDF Converter Module (`pdf_converter.py`)
- Comprehensive table extraction from PDFs
- Smart header detection and removal
- Table merging across multiple pages
- Enhanced column suggestions (distinguishes public price from net rate)
- Robust error handling

### 🎨 UI/UX Enhancements

#### Upload & Process Tab
- New PDF converter section with collapsible interface
- Enhanced column mapping with Public Selling Price field
- Renamed "Price" to "Net Rate (Supplier Price)" for clarity
- Added "Public Selling Price (PP AED)" optional field
- Price mismatch summary after uploads
- Improved validation messages

#### Matching Workbench
- New "Price Mismatch" filter option
- Enhanced table columns showing price breakdown
- Visual price match indicators (✅/❌/—)
- Better filtering for price compliance review

#### PDF Converter UI
- Clean, expandable interface matching app theme
- Live preview of extracted data
- Auto-suggestions for column mapping
- Support for both public price and net rate columns
- Download button for converted files
- Helpful guidance and error messages

### 📝 Documentation Updates
- Updated README.md with new features and screenshots
- Enhanced USER_GUIDE.md with:
  - PDF converter usage instructions
  - Price validation workflow
  - Stopword filtering explanation
  - Flow diagrams and screenshots
- Added comprehensive code comments

### 🐛 Bug Fixes
- Fixed false positive matches based on formulation type only
- Resolved font visibility issues in dark theme
- Improved price extraction from various formats
- Better handling of NULL price values

### 🔒 Breaking Changes
- None - All changes are backward compatible
- Existing data preserved during schema updates

### 📊 Performance
- No significant performance impact
- Stopword filtering adds <1ms per match
- Price validation is instant

---

## [2.0.0] - Previous Release
- Initial release with core matching functionality
- Dashboard with key metrics
- Basic supplier upload and matching
- Best buy analysis
- Cart functionality

---

## Notes
For detailed migration instructions and feature usage, see [USER_GUIDE.md](USER_GUIDE.md).
