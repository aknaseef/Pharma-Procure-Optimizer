# Pharma Procure Optimizer - User Guide

Welcome to **Pharma Procure Optimizer**, your intelligent solution for pharmaceutical inventory procurement. This guide will walk you through all features of the application to help you find the best deals across multiple suppliers and optimize your purchasing decisions.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Uploading Data](#uploading-data)
4. [Matching Workbench](#matching-workbench)
5. [Best Buy & Cart](#best-buy--cart)
6. [FAQ](#faq)

---

## Getting Started

### Prerequisites

- Python 3.8 or higher installed
- Required Python packages (install using `pip install -r requirements.txt`)

### Running the Application

1. Open a terminal in the project directory
2. Run the application:
   ```bash
   python3 -m streamlit run app.py
   ```
3. The application will open in your default browser at `http://localhost:8501`

---

## Dashboard Overview

The **Dashboard** provides a comprehensive overview of your procurement data with real-time metrics and visualizations.

![Dashboard Overview](/Users/naseef/.gemini/antigravity/brain/7774a7e2-5f68-480d-9c29-43c1355bde7f/dashboard_overview_1767803488095.png)

### Key Metrics

The dashboard displays five essential metrics at the top:

- **📦 Master Products**: Total number of products in your master list
- **🎯 Active Suppliers**: Number of suppliers currently providing offers
- **💰 Price Offers**: Total supplier offers available for comparison
- **⚠️ Unmatched**: Products that need manual linking
- **🛒 Cart Items**: Current items in your shopping cart

### Charts and Insights

- **Weighted Avg Unit Cost by Supplier**: Compare average unit costs across suppliers
- **Expiry Risk Distribution**: Visualize products by their expiry timelines
- Additional interactive charts for data analysis

---

## Uploading Data

The **Upload & Process** tab allows you to import your master product list and supplier price sheets.

![Upload Tab](/Users/naseef/.gemini/antigravity/brain/7774a7e2-5f68-480d-9c29-43c1355bde7f/upload_tab_interface_1767803536364.png)

### Master Product List

1. **Prepare your Excel file** with the following columns:
   - `Item Code`: Unique identifier for each product
   - `Product Name`: Name of the product
   - `Unit of Issue`: Standard unit (e.g., BOX, VIAL, TABLET)

2. **Upload the file**:
   - Drag and drop your Excel file into the "Master Product List" section
   - Or click "Browse files" to select your file
   - Supported formats: `.xlsx`, `.xls`

3. **Verify**: The system will display a preview of the uploaded data

### Supplier Price Sheet

1. **Prepare your CSV file** with these columns:
   - `Supplier Name`: Name of the supplier
   - `List Tag`: Category or batch identifier
   - `Product Name`: Product description
   - `Price`: Offer price
   - `Pack Size`: Number of units per pack
   - `Bonus`: Any bonus quantities (optional)
   - `Expiry Date`: Expiration date (optional)

2. **Upload the file**:
   - Drag and drop into the "Supplier Price Sheet" section
   - Or click "Browse files"
   - Supported format: `.csv`

3. **Automatic Matching**: The system will automatically match supplier products to your master list using intelligent fuzzy matching

> [!TIP]
> Upload multiple supplier sheets one at a time to compare prices from different vendors!

---

## Matching Workbench

The **Matching Workbench** is where you manually link supplier products that couldn't be automatically matched to your master list.

![Matching Workbench](/Users/naseef/.gemini/antigravity/brain/7774a7e2-5f68-480d-9c29-43c1355bde7f/matching_workbench_tab_1767803639495.png)

### How to Use the Matching Workbench

1. **Review Unmatched Products**: The table shows all supplier offers that weren't automatically linked
   - Supplier name and product details are displayed
   - Each row has a "Link" button with a confidence indicator (✅ high, 🟡 medium, ⚠️ low)

2. **Link Products**:
   - Click the "🔗 Link" button next to a product
   - A dialog will appear with two options:
     - **Find Master Product**: Search and select from existing master list items
     - **Manual Linking**: Enter the Offer ID and Master Product directly

3. **Search Master Products**:
   - Type product name in the search box
   - Select the matching master product from the dropdown
   - Click "Link Selected" to create the connection

4. **Verify Links**: Linked products will appear in the "Best Buy & Cart" search results

> [!IMPORTANT]
> Linking products is crucial for accurate price comparisons. Products must be linked before they appear in search results.

---

## Best Buy & Cart

The **Best Buy & Cart** tab is your main interface for searching products, comparing prices, and building your purchase order.

![Best Buy & Cart](/Users/naseef/.gemini/antigravity/brain/7774a7e2-5f68-480d-9c29-43c1355bde7f/best_buy_cart_tab_1767803689140.png)

### Searching for Products

1. **Enter Product Name**: Type the product name in the search bar
2. **View Results**: The system displays all matched offers sorted by best price
3. **Compare Deals**: Each result shows:
   - Supplier name
   - Product details
   - Price per pack
   - Pack size
   - Normalized unit cost (for fair comparison)
   - Bonus quantities
   - Expiry date

### Deal Cards

Each product offer is displayed in a card format with:
- 🏷️ **Supplier badge** at the top
- 📦 **Product name** and details
- 💰 **Price information** with unit cost
- 📦 **Pack size** and bonus
- 📅 **Expiry date** (if available)
- 🔢 **Quantity input** field
- Color-coded tags for key information

### Adding Items to Cart

1. **Set Quantity**: Enter the desired quantity in the number input field
2. **Add to Cart**: Click the "🛒 Add Selected to Cart" button
3. **Confirmation**: A toast notification confirms items were added

### Managing Your Cart

- **View Cart Details**: Check the "Show Cart Details" checkbox to expand the cart
- **Cart Summary**: Shows all items with:
  - Supplier
  - Product name
  - Quantity
  - Unit cost
  - Total cost
- **Total Amount**: Displayed at the bottom of the cart
- **Clear Cart**: Use the "🗑️ Clear Cart" button to start over

> [!TIP]
> The normalized unit cost helps you compare products with different pack sizes fairly!

---

## FAQ

### How does automatic matching work?

The system uses advanced fuzzy matching algorithms (via `rapidfuzz`) to compare supplier product names with your master list. It considers:
- Text similarity
- Common pharmaceutical naming patterns
- Unit of issue compatibility
- Confidence scoring

### What if a product isn't automatically matched?

No problem! Go to the **Matching Workbench** tab to manually link unmatched products to your master list.

### Can I upload multiple supplier sheets?

Yes! Upload supplier sheets one at a time. The system will process and merge all offers, allowing you to compare prices across all suppliers.

### How is the "Best Buy" determined?

Products are sorted by **normalized unit cost** (price per single unit) to ensure fair comparison across different pack sizes. The lowest unit cost appears first.

### What happens to my data between sessions?

All data is stored in a local SQLite database (`pharma.db`). Your master list, supplier offers, and manual links persist between sessions.

### Can I export my cart?

Currently, the cart is displayed in a table format. You can copy the data manually. Future versions may include direct export functionality.

### What file formats are supported?

- **Master List**: Excel files (`.xlsx`, `.xls`)
- **Supplier Sheets**: CSV files (`.csv`)

### How do I reset the database?

Delete the `pharma.db` file from the project directory and restart the application. This will create a fresh database.

> [!WARNING]
> Deleting the database will remove all uploaded data, manual links, and cart items permanently!

### Is my data secure?

Yes! All data is stored locally on your machine. The application does not send any data to external servers.

---

## Support

For issues, questions, or feature requests:
- Open an issue on the [GitHub repository](https://github.com/aknaseef/Pharma-Procure-Optimizer)
- Check the README.md for technical documentation

---

**Happy Procuring! 💊💰**
