# 💊 Pharma-Procure Optimizer

A local application for pharmacists to optimize inventory purchasing by comparing supplier offers, calculating effective unit costs, and managing product matching.

## Features

- **Master Product Management**: Upload MOH master list with intelligent column mapping
- **Supplier Offer Processing**: Import supplier sheets with automatic fuzzy matching
- **Smart Matching**: Hybrid fuzzy matching algorithm with price-based pack size disambiguation
- **Best Buy Search**: Find lowest unit cost offers across all suppliers
- **Risk Assessment**: Expiry-based risk levels with purchasing recommendations
- **Shopping Cart**: Build and export purchase orders

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

## Usage

### 1. Upload Master List
- Go to "Upload & Process" tab
- Upload your MOH Master List (Excel)
- Map columns (Product Name, Item Code, Cost, etc.)
- Click "Process Master List"

### 2. Upload Supplier Offers
- Upload supplier price sheets
- Enter Supplier Name and List Tag
- Set default Credit Period
- Click "Process & Archive Old Data"

### 3. Search Best Prices
- Go to "Best Buy & Cart" tab
- Search by product name
- Compare unit costs across suppliers
- Check expiry dates and risk levels
- Add items to cart

### 4. Manual Linking
- Use "Matching Workbench" for products that didn't auto-match
- Create aliases for future auto-matching

## Project Structure

```
purchase solution/
├── app.py              # Main Streamlit application
├── setup_db.py         # Database models
├── logic.py            # Business logic (EUC, fuzzy matching)
├── simplify_names.py   # Product name simplification
├── config.py           # Configuration settings
├── requirements.txt    # Dependencies
├── pharma.db           # SQLite database (auto-created)
└── README.md           # This file
```

## Configuration

Edit `config.py` to customize:
- Risk assessment thresholds
- Fuzzy matching cutoffs
- Default values

## License

Internal use only.
