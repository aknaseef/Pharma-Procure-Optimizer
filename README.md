# 💊 Pharma-Procure Optimizer

> **Version 2.1** - PDF Converter, Price Validation & Improved Matching

A modern, intelligent application for pharmaceutical procurement that helps you optimize inventory purchasing by comparing supplier offers, analyzing pricing trends, and managing product matching with a beautiful, professional interface.

## ✨ Features

### 🆕 NEW in v2.1
- **📄 PDF to Excel Converter**: Convert PDF supplier price lists directly within the app
  - Automatic table extraction from multi-page PDFs
  - Smart column detection and mapping
  - One-click download of converted Excel files
  
- **💵 Public Selling Price Validation**: Ensure regulatory compliance
  - Track official public prices separately from net rates
  - Automatic price validation during matching
  - Price mismatch detection and filtering
  
- **🎯 Enhanced Product Matching**: Prevent false positives
  - Stricter matching thresholds (85-90% similarity required)
  - Pharmaceutical stopword filtering (50+ terms)
  - No more matches based solely on "Tablet", "Syrup", etc.

### 📊 Dashboard Analytics (v2.0)
- **Real-time Metrics**: Track master products, active suppliers, price offers, and cart status
- **Interactive Charts**: Visualize supplier pricing, expiry risk distribution, and cost trends
- **Data Insights**: Make informed purchasing decisions with comprehensive analytics

### 🎨 Modern UI/UX (v2.0)
- **Professional Design**: Custom theme with teal accents and dark backgrounds
- **Deal Cards**: Beautiful card-based product displays with hover effects
- **Empty States**: Helpful guidance when no data is available
- **Toast Notifications**: Non-intrusive feedback for user actions

### 🔧 Core Functionality
- **Master Product Management**: Upload and manage your product inventory list
- **Supplier Offer Processing**: Import multiple supplier sheets with automatic fuzzy matching
- **Smart Matching**: Hybrid fuzzy matching algorithm with price-based pack size disambiguation
- **Best Buy Search**: Find lowest unit cost offers across all suppliers with normalized pricing
- **Risk Assessment**: Expiry-based risk levels with purchasing recommendations
- **Shopping Cart**: Build purchase orders with detailed cost breakdowns

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone or download the project:
```bash
cd "purchase solution"
```

2. Create virtual environment (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python3 setup_db.py
```

5. Run the application:
```bash
python3 -m streamlit run app.py
```

6. Open browser at `http://localhost:8501`

## 📖 Documentation

For detailed instructions with screenshots, see the **[User Guide](USER_GUIDE.md)**.

## Usage

### 1. View Dashboard
- Launch the app to see the Dashboard tab
- Review key metrics: total products, suppliers, offers, and unmatched items
- Analyze charts for supplier pricing trends and expiry risk distribution
- Monitor your cart status in real-time

### 2. Upload Master List
- Go to "Upload & Process" tab
- Drag and drop your Master List Excel file (`.xlsx`, `.xls`)
- Required columns: `Item Code`, `Product Name`, `Standard Cost` (public selling price)
- System automatically processes and stores the data

### 3. Convert PDF Supplier Lists (NEW)
- In "Upload & Process" tab, scroll to "📄 Convert PDF Supplier List to Excel"
- Upload PDF supplier price list
- Review auto-detected columns
- Map to required fields:
  - Product Name (required)
  - Public Selling Price (optional)
  - Net Rate (required)
  - Pack Size, Bonus, etc. (optional)
- Download converted Excel file
- Upload the Excel file as a regular supplier list

### 4. Upload Supplier Offers
- In "Upload & Process" tab, upload supplier Excel/CSV files
- Map columns:
  - **Product Name** (required)
  - **Public Selling Price** (PP AED) - regulated price
  - **Net Rate** (Supplier Price) - what you pay
  - Pack Size, Bonus, Expiry Date (optional)
- System automatically matches products and validates prices
- Review price mismatch warnings if any

### 5. Search Best Prices
- Go to "Best Buy & Cart" tab
- Enter product name in the search bar
- View results as beautiful deal cards showing:
  - Supplier name with colored badges
  - Normalized unit cost for fair comparison
  - Pack size, bonus, and expiry information
- Set quantity and add items to cart
- Review cart summary and total cost

### 6. Review Price Compliance (NEW)
- Navigate to "Matching Workbench" tab
- Use "Price Mismatch" filter to see products with incorrect public prices
- Review Net Rate, Public Price, and Master Price columns
- Check Price ✓ column for validation status (✅/❌)

### 7. Manual Linking (When Needed)
- Navigate to "Matching Workbench" tab
- Review unmatched supplier products
- Click "🔗 Link" button next to items
- Search and select corresponding master product
- Linked items will now appear in Best Buy search

## 🆕 What's New in v2.1

- ✅ **PDF to Excel Converter** - Convert supplier PDFs directly in the app
- ✅ **Public Selling Price Validation** - Track and validate regulated prices
- ✅ **Enhanced Matching Algorithm** - Stricter thresholds (85-90% similarity)
- ✅ **Stopword Filtering** - Ignore 50+ pharmaceutical formulation terms
- ✅ **Price Mismatch Detection** - Filter and review pricing compliance issues
- ✅ **Improved Column Detection** - Smart suggestions for public vs net prices
- ✅ **Database Migration System** - Seamless schema updates

## Project Structure

```
purchase solution/
├── app.py                    # Main Streamlit application with UI
├── setup_db.py               # Database models (SQLAlchemy)
├── logic.py                  # Business logic (EUC, fuzzy matching, stopwords)
├── pdf_converter.py          # PDF to Excel conversion utilities (NEW)
├── config.py                 # Configuration settings and stopwords list
├── migrate_add_public_price.py  # Database migration script (NEW)
├── requirements.txt          # Python dependencies
├── pharma.db                 # SQLite database (auto-created)
├── CHANGELOG.md              # Version history (NEW)
├── USER_GUIDE.md             # Comprehensive user guide with screenshots
└── README.md                 # This file
```

## Configuration

Edit `config.py` to customize:
- Risk assessment thresholds
- Fuzzy matching cutoffs (Token Sort, Token Set, Partial Ratio)
- Confidence levels for matching
- Pharmaceutical stopwords list (formulation terms to ignore)
- Default values

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License - feel free to use this project for your pharmaceutical procurement needs.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Fuzzy matching powered by [RapidFuzz](https://github.com/maxbachmann/RapidFuzz)
- Charts created with [Plotly](https://plotly.com/)
- PDF processing with [pdfplumber](https://github.com/jsvine/pdfplumber)

---

**Version 2.1** | [View Changelog](CHANGELOG.md) | [User Guide](USER_GUIDE.md) | [Report Issues](https://github.com/aknaseef/Pharma-Procure-Optimizer/issues)
