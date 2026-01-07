# 💊 Pharma-Procure Optimizer

> **Version 2.0** - Now with Dashboard Analytics & Enhanced UI

A modern, intelligent application for pharmaceutical procurement that helps you optimize inventory purchasing by comparing supplier offers, analyzing pricing trends, and managing product matching with a beautiful, professional interface.

## ✨ Features

### 📊 Dashboard Analytics (NEW in v2.0)
- **Real-time Metrics**: Track master products, active suppliers, price offers, and cart status
- **Interactive Charts**: Visualize supplier pricing, expiry risk distribution, and cost trends
- **Data Insights**: Make informed purchasing decisions with comprehensive analytics

### 🎨 Modern UI/UX (NEW in v2.0)
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

### 1. View Dashboard (NEW)
- Launch the app to see the Dashboard tab
- Review key metrics: total products, suppliers, offers, and unmatched items
- Analyze charts for supplier pricing trends and expiry risk distribution
- Monitor your cart status in real-time

### 2. Upload Master List
- Go to "Upload & Process" tab
- Drag and drop your Master List Excel file (`.xlsx`, `.xls`)
- Required columns: `Item Code`, `Product Name`, `Unit of Issue`
- System automatically processes and stores the data

### 3. Upload Supplier Offers
- In the same "Upload & Process" tab, upload supplier CSV files
- Required columns: `Supplier Name`, `Product Name`, `Price`, `Pack Size`
- Optional: `Bonus`, `Expiry Date`, `List Tag`
- System automatically matches products using fuzzy matching

### 4. Search Best Prices
- Go to "Best Buy & Cart" tab
- Enter product name in the search bar
- View results as beautiful deal cards showing:
  - Supplier name with colored badges
  - Normalized unit cost for fair comparison
  - Pack size, bonus, and expiry information
- Set quantity and add items to cart
- Review cart summary and total cost

### 5. Manual Linking (When Needed)
- Navigate to "Matching Workbench" tab
- Review unmatched supplier products
- Click "🔗 Link" button next to items
- Search and select corresponding master product
- Linked items will now appear in Best Buy search

## 🆕 What's New in v2.0

- ✅ **Interactive Dashboard** with real-time metrics and charts (using Plotly)
- ✅ **Modern UI Design** with custom CSS theme and professional styling
- ✅ **Deal Cards** for better visual product comparison
- ✅ **Empty States** with helpful icons and messages
- ✅ **Toast Notifications** for user feedback
- ✅ **Improved Cart Management** with detailed summaries
- ✅ **Enhanced Search** with better result organization

## Project Structure

```
purchase solution/
├── app.py              # Main Streamlit application with UI
├── setup_db.py         # Database models (SQLAlchemy)
├── logic.py            # Business logic (EUC, fuzzy matching)
├── simplify_names.py   # Product name simplification utilities
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── pharma.db           # SQLite database (auto-created)
├── USER_GUIDE.md       # Comprehensive user guide with screenshots
└── README.md           # This file
```

## Configuration

Edit `config.py` to customize:
- Risk assessment thresholds
- Fuzzy matching cutoffs
- Default values

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License - feel free to use this project for your pharmaceutical procurement needs.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Fuzzy matching powered by [RapidFuzz](https://github.com/maxbachmann/RapidFuzz)
- Charts created with [Plotly](https://plotly.com/)

---

**Version 2.0** | [View Changelog](USER_GUIDE.md) | [Report Issues](https://github.com/aknaseef/Pharma-Procure-Optimizer/issues)
