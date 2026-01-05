import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup_db import MasterProduct, SupplierOffer, ProductAlias, PriceHistory
from logic import calculate_euc, fuzzy_match, parse_pack_size
import time
import re
import logging

# Import name simplification utility
from simplify_names import simplify_product_name

# Import configuration
from config import (
    DATABASE_PATH, RISK_HIGH_DAYS, RISK_MEDIUM_DAYS,
    DEFAULT_CREDIT_DAYS, LOG_LEVEL, LOG_FILE, MAX_FILE_SIZE_MB
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Page Config
st.set_page_config(page_title="Pharma-Procure Optimizer", layout="wide")

# Database Connection (using config)
engine = create_engine(DATABASE_PATH)
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()

def find_index(columns, keywords):
    """
    Returns the index of the first column that matches any constant in keywords.
    Case insensitive partial match.
    """
    cols_lower = [c.lower() for c in columns]
    for i, col in enumerate(cols_lower):
        for kw in keywords:
            if kw in col:
                return i
    return 0

def validate_file_upload(uploaded_file, max_size_mb: int = MAX_FILE_SIZE_MB) -> tuple:
    """
    Validate uploaded file size.
    
    Returns:
        (is_valid: bool, error_message: str or None)
    """
    if uploaded_file is None:
        return False, "No file uploaded"
    
    # Check file size (Streamlit UploadedFile has .size attribute)
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        logger.warning(f"File too large: {file_size_mb:.2f}MB > {max_size_mb}MB limit")
        return False, f"File too large ({file_size_mb:.1f}MB). Maximum allowed: {max_size_mb}MB"
    
    return True, None

# Initialize Session State for Cart
if 'cart' not in st.session_state:
    st.session_state.cart = []

# Title
st.title("💊 Pharma-Procure Optimizer v2.0")

# Tabs
tab1, tab2, tab3 = st.tabs(["📂 Upload & Process", "️🔍 Matching Workbench", "🛒 Best Buy & Cart"])

# --- TAB 1: Upload & Process ---
with tab1:
    st.header("Upload Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Master List")
        master_file = st.file_uploader("Upload Master List (Excel)", type=["xlsx"])
        if master_file:
            # Validate file size
            is_valid, error_msg = validate_file_upload(master_file)
            if not is_valid:
                st.error(error_msg)
            else:
                # Read first to get columns
                try:
                    df_master_preview = pd.read_excel(master_file)
                    st.write("Preview:", df_master_preview.head(3))
                    
                    # Standardize cols for reliable matching
                    df_master_preview.columns = df_master_preview.columns.str.strip().str.lower()
                    cols = df_master_preview.columns.tolist()
                    
                    st.markdown("### Map Master List Columns")
                    idx_name = find_index(cols, ['product_name', 'product name', 'trade name', 'item name', 'description'])
                    idx_code = find_index(cols, ['code', 'item code', 'item_code', 'sku']) 
                    idx_dosage = find_index(cols, ['dosage', 'strength', 'uom'])
                    idx_pack = find_index(cols, ['pack', 'size'])
                    idx_cost = find_index(cols, ['cost', 'standard', 'price', 'rate', 'retail'])

                    col_name = st.selectbox("Product Name", cols, index=idx_name, key='m_name')
                    col_code = st.selectbox("Item Code", cols, index=idx_code, key='m_code')
                    col_dosage = st.selectbox("Dosage", ["None"] + cols, index=idx_dosage + 1 if idx_dosage > 0 or (idx_dosage==0 and 'dosage' in cols[0]) else 0, key='m_dose')
                    col_pack = st.selectbox("Pack Size", ["None"] + cols, index=idx_pack + 1 if idx_pack > 0 or (idx_pack==0 and 'pack' in cols[0]) else 0, key='m_pack')
                    col_cost = st.selectbox("Standard Cost", ["None"] + cols, index=idx_cost + 1 if idx_cost > 0 or (idx_cost==0 and 'cost' in cols[0]) else 0, key='m_cost')

                    if st.button("Process Master List"):
                        # Reload fresh or use preview
                        df_master = df_master_preview
                        
                        # Drop rows where Name is missing
                        df_master = df_master.dropna(subset=[col_name])
                        
                        session = get_db_session()
                        count = 0
                        for index, row in df_master.iterrows():
                            p_name = str(row[col_name])
                            item_code = str(row[col_code])
                            
                            # Robust Cost Cleaning
                            std_cost = 0.0
                            if col_cost != "None":
                                try:
                                    val = row[col_cost]
                                    if pd.notnull(val):
                                        v_str = str(val).upper().replace('AED', '').replace(',', '').strip()
                                        match_c = re.search(r"(\d+(\.\d+)?)", v_str)
                                        if match_c:
                                            std_cost = float(match_c.group(1))
                                except Exception as e:
                                    logger.warning(f"Failed to parse cost value: {e}")
                                    std_cost = 0.0

                            pack_s = str(row[col_pack]) if col_pack != "None" else "1"
                            dose_s = str(row[col_dosage]) if col_dosage != "None" else ""
                            
                            # --- AGGRESSIVE CLEANING ---
                            is_header = False
                            if p_name.lower() in [c.lower() for c in cols]:
                                is_header = True
                            if str(row[col_code]).lower() in [c.lower() for c in cols]:
                                is_header = True
                            
                            if is_header:
                                continue

                            if re.search(r"page\s+\d+", p_name.lower()) or "ministry of health" in p_name.lower():
                                continue
                                
                            if p_name.replace('.','').isdigit() and len(p_name) < 5:
                                continue
                                
                            if len(p_name) < 2:
                                continue

                            exists = session.query(MasterProduct).filter_by(item_code=item_code).first()
                            if not exists:
                                simplified = simplify_product_name(p_name)
                                mp = MasterProduct(
                                    item_code=item_code,
                                    product_name=p_name,
                                    simplified_name=simplified,
                                    dosage=dose_s,
                                    pack_size=pack_s,
                                    standard_cost=std_cost
                                )
                                session.add(mp)
                                count += 1
                        session.commit()
                        session.close()
                        st.success(f"Successfully added {count} new products to Master List.")
                except Exception as e:
                    st.error(f"Error reading file: {e}")

    with col2:
        st.subheader("2. Supplier Offers")
        supplier_file = st.file_uploader("Upload Supplier Sheet (Excel/CSV)", type=["xlsx", "csv"])
        
        c_sup, c_tag = st.columns(2)
        supplier_name = c_sup.text_input("Supplier Name")
        list_tag = c_tag.text_input("List Tag (e.g., General, Fridge)", value="General")
        
        if supplier_file and supplier_name and list_tag:
            if supplier_file.name.endswith('.csv'):
                df_supplier = pd.read_csv(supplier_file)
            else:
                df_supplier = pd.read_excel(supplier_file)
            
            st.write("Preview:", df_supplier.head(3))
            
            st.markdown("### Map Columns")
            cols = df_supplier.columns.tolist()
            
            # Smart Detection
            idx_item = find_index(cols, ['name', 'item', 'description', 'product', 'drug'])
            idx_price = find_index(cols, ['price', 'rate', 'cost', 'public', 'net', 'aed'])
            idx_pack = find_index(cols, ['pack', 'size', 'uom', 'format']) # Added reasonable defaults for pack
            idx_bonus = find_index(cols, ['bonus', 'offer', 'free', 'scheme', 'deal'])
            idx_expiry = find_index(cols, ['expiry', 'exp', 'valid', 'date'])
            idx_credit = find_index(cols, ['credit', 'term', 'payment'])

            col_item = st.selectbox("Item Name Column", cols, index=idx_item)
            col_price = st.selectbox("Price Column", cols, index=idx_price)
            col_pack = st.selectbox("Pack Size Column", ["None"] + cols, index=idx_pack + 1 if idx_pack > 0 or (idx_pack==0 and 'pack' in cols[0].lower()) else 0)
            col_bonus = st.selectbox("Bonus Column", ["None"] + cols, index=idx_bonus + 1 if idx_bonus > 0 or (idx_bonus==0 and 'bonus' in cols[0].lower()) else 0)
            col_expiry = st.selectbox("Expiry Column", ["None"] + cols, index=idx_expiry + 1 if idx_expiry > 0 or (idx_expiry==0 and 'exp' in cols[0].lower()) else 0)
            col_credit = st.selectbox("Credit/Terms Column", ["None"] + cols, index=idx_credit + 1 if idx_credit > 0 or (idx_credit==0 and 'credit' in cols[0].lower()) else 0)
            
            # Manual Credit Period (applies to all products if no column selected)
            st.markdown("---")
            manual_credit_days = st.number_input(
                "Default Credit Period (days) - applies to all products if no column selected",
                min_value=0,
                max_value=365,
                value=30,
                help="Enter the credit period in days. This will be used for all products if 'Credit/Terms Column' is set to 'None'."
            )
            
            if st.button("Process & Archive Old Data"):
                session = get_db_session()
                
                # 1. Archive & Delete Old Data for this Supplier + Tag
                old_offers = session.query(SupplierOffer).filter_by(supplier_name=supplier_name, list_tag=list_tag).all()
                archived_count = 0
                for old in old_offers:
                    hist = PriceHistory(
                        supplier_name=old.supplier_name,
                        list_tag=old.list_tag,
                        raw_product_name=old.raw_product_name,
                        price=old.price,
                        supplier_pack_size=old.supplier_pack_size,
                        normalized_cost=old.normalized_cost,
                        bonus_string=old.bonus_string,
                        expiry_date=old.expiry_date
                    )
                    session.add(hist)
                    session.delete(old)
                    archived_count += 1
                
                # 2. Process New Data
                processed_count = 0
                progress_bar = st.progress(0)
                
                for index, row in df_supplier.iterrows():
                    raw_name = str(row[col_item])
                    
                    # Robust Price Cleaning
                    try:
                        price_val = row[col_price]
                        if pd.isnull(price_val):
                            price = 0.0
                        else:
                            # Simple clean: remove currency and spaces
                            p_str = str(price_val).upper().replace('AED', '').replace('RS', '').replace('$', '').strip()
                            price = float(p_str)
                    except ValueError:
                        # Fallback: extract first number found (e.g. if user mapped "10+2" as price, take 10)
                        match_price = re.search(r"(\d+(\.\d+)?)", str(row[col_price]))
                        price = float(match_price.group(1)) if match_price else 0.0
                    
                    # Pack Size Logic
                    pack_val = 1
                    if col_pack != "None":
                         pack_val = parse_pack_size(row[col_pack])
                    
                    bonus = str(row[col_bonus]) if col_bonus != "None" and pd.notnull(row[col_bonus]) else None
                    expiry = None
                    if col_expiry != "None" and pd.notnull(row[col_expiry]):
                        try:
                            dt_val = pd.to_datetime(row[col_expiry], errors='coerce')
                            if pd.notnull(dt_val):
                                expiry = dt_val.date()
                        except Exception as e:
                            logger.warning(f"Failed to parse expiry date: {e}")
                            expiry = None
                    
                    credit_days = manual_credit_days  # Use manual default
                    if col_credit != "None" and pd.notnull(row[col_credit]):
                        # Try to parse string "30 days" -> 30
                        c_str = str(row[col_credit])
                        match_c = re.search(r"(\d+)", c_str)
                        if match_c:
                            credit_days = int(match_c.group(1))

                    # Fuzzy match (with price to help disambiguate pack sizes)
                    match_result = fuzzy_match(raw_name, session, price)
                    matched_id = match_result['master_id'] if match_result else None
                    
                    # Calc Metrics
                    euc, _, norm_cost = calculate_euc(price, pack_val, bonus)
                    
                    # Create Offer
                    offer = SupplierOffer(
                        supplier_name=supplier_name,
                        list_tag=list_tag,
                        raw_product_name=raw_name,
                        price=price,
                        supplier_pack_size=pack_val,
                        normalized_cost=norm_cost,
                        bonus_string=bonus,
                        expiry_date=expiry,
                        credit_period_days=credit_days,
                        matched_master_id=matched_id
                    )
                    session.add(offer)
                    processed_count += 1
                    
                    if index % 10 == 0:
                        progress_bar.progress(min(index / len(df_supplier), 1.0))
                
                session.commit()
                session.close()
                progress_bar.progress(1.0)
                st.success(f"Archived {archived_count} old records. Processed {processed_count} new offers.")
                
                # Clear form fields for next upload
                st.info("💡 Form cleared for next upload. Please enter new Supplier Name for the next file.")
                st.rerun()

# --- TAB 2: Matching Workbench ---
with tab2:
    st.header("Resolve Uncertain Matches")
    session = get_db_session()
    # Simple Review query
    offers = session.query(SupplierOffer).all()
    
    data = []
    for o in offers:
        match_name = o.master_product.product_name if o.master_product else "NO MATCH"
        data.append({
            "ID": o.id,
            "Supplier": o.supplier_name,
            "Product": o.raw_product_name,
            "Matched": match_name,
            "Norm. Cost": o.normalized_cost
        })
    
    if data:
        st.dataframe(pd.DataFrame(data))
        
        st.markdown("### Link Alias")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            offer_id = st.number_input("Offer ID to Link", min_value=1, step=1)
        with c2:
            search = st.text_input("Find Master Product")
            target_id = None
            if search:
                res = session.query(MasterProduct).filter(MasterProduct.product_name.ilike(f"%{search}%")).limit(5).all()
                if res:
                    sel = st.selectbox("Select Master", [f"{r.product_name} ({r.id})" for r in res])
                    target_id = int(sel.split('(')[-1].replace(')', ''))
        with c3:
            st.write("")
            st.write("")
            if st.button("Link Alias"):
                if offer_id and target_id:
                    o = session.get(SupplierOffer, offer_id)
                    if o:
                        o.matched_master_id = target_id
                    # Also link all future same names?
                    # Create Alias
                    pa = ProductAlias(alias_name=o.raw_product_name, master_product_id=target_id)
                    session.add(pa)
                    session.commit()
                    st.success("Linked!")
    session.close()

# --- TAB 3: Best Buy Search & Cart ---
with tab3:
    st.header("Best Buy Search")
    
    col_search, col_cart_btn = st.columns([3, 1])
    with col_search:
        query = st.text_input("Search Product (Generic or Brand)")
    with col_cart_btn:
        st.metric("Cart Items", len(st.session_state.cart))
        if st.checkbox("Show Cart Details"):
            st.write("### Your Purchase Order")
            if st.session_state.cart:
                cart_df = pd.DataFrame(st.session_state.cart)
                st.dataframe(cart_df)
                
                # CSV Export
                csv = cart_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download PO (CSV)",
                    csv,
                    "purchase_order.csv",
                    "text/csv",
                    key='download-csv'
                )
                
                if st.button("Clear Cart"):
                    st.session_state.cart = []
                    st.rerun()
            else:
                st.info("Cart is empty.")
        
    if query:
        session = get_db_session()
        masters = session.query(MasterProduct).filter(MasterProduct.product_name.ilike(f"%{query}%")).all()
        master_ids = [m.id for m in masters]
        
        if master_ids:
            results = session.query(SupplierOffer).filter(SupplierOffer.matched_master_id.in_(master_ids)).all()
            
            # Prepare data for display
            res_data = []
            for r in results:
                # Re-calc for display
                euc, _, _ = calculate_euc(r.price, r.supplier_pack_size, r.bonus_string)
                
                # Risk Logic
                risk = "Safe"
                if r.expiry_date:
                    days = (r.expiry_date - pd.Timestamp.now().date()).days
                    if days < RISK_HIGH_DAYS: risk = "High Risk"
                    elif days < RISK_MEDIUM_DAYS: risk = "Medium Risk"
                
                res_data.append({
                    "RefID": r.id,
                    "Supplier": r.supplier_name,
                    "Tag": r.list_tag,
                    "Product": r.raw_product_name,
                    "Pack Size": r.supplier_pack_size,
                    "Price (Pack)": r.price,
                    "Bonus": r.bonus_string,
                    "Norm. Unit Cost": r.normalized_cost, # Crucial
                    "Highlight": f"{r.normalized_cost:.4f}", # Sort key
                    "Expiry": r.expiry_date,
                    "Credit Days": r.credit_period_days or 30,  # Default to 30 if not set
                    "Risk": risk
                })
            
            if res_data:
                df_res = pd.DataFrame(res_data)
                df_res = df_res.sort_values(by="Norm. Unit Cost", ascending=True)
                
                st.write(f"Found {len(df_res)} offers. Sorted by Lowest Unit Cost.")
                
                # Risk Legend
                with st.expander("ℹ️ Risk Level Explanation & Smart Buying Tips", expanded=False):
                    st.markdown("""
                    **Risk Levels (based on Expiry Date):**
                    - 🟢 **Safe**: >12 months until expiry
                    - 🟠 **Medium Risk**: 6-12 months until expiry
                    - 🔴 **High Risk**: <6 months until expiry
                    - ⚪ **Unknown**: No expiry date provided
                    
                    ---
                    
                    **💡 Smart Buying Decision Guide:**
                    
                    | Price | Risk | Credit | Verdict |
                    |-------|------|--------|---------|
                    | ⬇️ Low | 🟢 Safe | Any | ✅ **Best Deal** - Buy confidently |
                    | ⬇️ Low | 🟠 Medium | Long (60+ days) | ✅ **Good** - Time to sell before payment |
                    | ⬇️ Low | 🔴 High | Long (60+ days) | ⚠️ **Risky** - Only if you can sell fast |
                    | ⬇️ Low | 🔴 High | Short (<30 days) | ❌ **Avoid** - Payment due before you can sell |
                    | ⬆️ High | 🟢 Safe | Any | ⚠️ **Compare** - Look for better prices |
                    
                    **Key Tips:**
                    - Always compare Unit Cost (not Pack Price) across suppliers
                    - Credit Period > Shelf Life Risk = Safer deal
                    - High Risk + Low Price = Only buy if turnover is fast
                    """)
                
                # Header
                h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2, 2, 1, 1, 1, 1, 1, 1])
                h1.write("**Supplier**")
                h2.write("**Product**")
                h3.write("**Price/Pack**")
                h4.write("**Unit Cost**")
                h5.write("**Expiry**")
                h6.write("**Credit Days**")
                h7.write("**Risk**")
                h8.write("**Order Qty**")
                
                for idx, row in df_res.iterrows():
                    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2, 2, 1, 1, 1, 1, 1, 1])
                    c1.write(f"{row['Supplier']} ({row['Tag']})")
                    c2.write(f"{row['Product']} (Size: {row['Pack Size']})")
                    c3.write(f"{row['Price (Pack)']}")
                    c4.write(f"**{row['Norm. Unit Cost']:.4f}**")
                    
                    # Expiry Date with color coding
                    if row['Expiry']:
                        exp_date = row['Expiry']
                        days_left = (exp_date - pd.Timestamp.now().date()).days
                        if days_left < 180:
                            c5.markdown(f":red[{exp_date}]")
                        elif days_left < 365:
                            c5.markdown(f":orange[{exp_date}]")
                        else:
                            c5.write(str(exp_date))
                    else:
                        c5.write("-")
                    
                    # Credit Period
                    c6.write(f"{row['Credit Days']} days")
                    
                    color = "green"
                    if "High" in row['Risk']: color = "red"
                    elif "Medium" in row['Risk']: color = "orange"
                    c7.markdown(f":{color}[{row['Risk']}]")
                    
                    # Cart Action
                    key = f"qty_{row['RefID']}"
                    qty = c8.number_input("Qty", min_value=0, step=1, key=key, label_visibility="collapsed")
                    
                    if qty > 0:
                        # Add to cart logic (Basic: if qty > 0 and not in cart or update)
                        # We need a button to "Update Cart" or just add immediately?
                        # Immediate add is tricky with reruns.
                        # Let's add an "Add" button per row or global "Add Selected".
                        pass

                if st.button("Add Entered Quantities to Cart"):
                    added = 0
                    for idx, row in df_res.iterrows():
                        k = f"qty_{row['RefID']}"
                        q = st.session_state.get(k, 0)
                        if q > 0:
                            # Add to session cart
                            item = {
                                "Supplier": row['Supplier'],
                                "Product": row['Product'],
                                "Quantity": q,
                                "Unit Cost": row['Norm. Unit Cost'],
                                "Total": q * row['Price (Pack)'] # Assuming Qty is Packs
                            }
                            st.session_state.cart.append(item)
                            added += 1
                    if added > 0:
                        st.success(f"Added {added} items to cart!")
                        # st.rerun() 
            else:
                st.info("No supplier offers found.")
                
            # Show unmatched products in separate section
            st.markdown("---")
            unmatched = session.query(SupplierOffer).filter(SupplierOffer.matched_master_id.is_(None)).all()
            
            if unmatched:
                with st.expander(f"⚠️ Unmatched Products ({len(unmatched)}) - Requires Manual Linking"):
                    st.warning(f"These {len(unmatched)} products were not automatically matched to the Master List. You must manually link them in the 'Matching Workbench' tab before they can be properly searched.")
                    
                    unmatched_data = []
                    for u in unmatched:
                        unmatched_data.append({
                            "Supplier": u.supplier_name,
                            "Tag": u.list_tag,
                            "Product": u.raw_product_name,
                            "Price": u.price,
                            "Pack Size": u.supplier_pack_size,
                            "Bonus": u.bonus_string,
                            "Expiry": u.expiry_date
                        })
                    
        else:
            st.info("No matched products found in Master List.")
        
        # ALWAYS search unmatched products for the query (regardless of master match)
        st.markdown("---")
        unmatched = session.query(SupplierOffer).filter(
            SupplierOffer.matched_master_id.is_(None),
            SupplierOffer.raw_product_name.ilike(f"%{query}%")
        ).all()
        
        if unmatched:
            with st.expander(f"⚠️ Unmatched Products Matching '{query}' ({len(unmatched)})", expanded=True):
                st.warning("These products match your search but are not linked to the Master List. Link them in 'Matching Workbench' to compare prices.")
                
                unmatched_data = []
                for u in unmatched:
                    unmatched_data.append({
                        "Supplier": u.supplier_name,
                        "Tag": u.list_tag,
                        "Product": u.raw_product_name,
                        "Price": u.price,
                        "Pack Size": u.supplier_pack_size,
                        "Bonus": u.bonus_string,
                        "Expiry": u.expiry_date
                    })
                
                df_unmatched = pd.DataFrame(unmatched_data)
                st.dataframe(df_unmatched, use_container_width=True)
                
                st.info("💡 Tip: Go to 'Matching Workbench' tab to manually link these.")
        
        session.close()
    else:
        # Show ALL unmatched products when no search query
        session = get_db_session()
        unmatched_all = session.query(SupplierOffer).filter(SupplierOffer.matched_master_id.is_(None)).all()
        
        if unmatched_all:
            st.info(f"Enter a product name above to search, or review {len(unmatched_all)} unmatched products below.")
            
            with st.expander(f"⚠️ All Unmatched Products ({len(unmatched_all)})"):
                st.warning("These products need manual linking in the 'Matching Workbench' tab.")
                
                unmatched_data = []
                for u in unmatched_all:
                    unmatched_data.append({
                        "Supplier": u.supplier_name,
                        "Tag": u.list_tag,
                        "Product": u.raw_product_name,
                        "Price": u.price,
                        "Pack Size": u.supplier_pack_size,
                        "Bonus": u.bonus_string,
                        "Expiry": u.expiry_date
                    })
                
                df_unmatched = pd.DataFrame(unmatched_data)
                st.dataframe(df_unmatched, use_container_width=True)

    
    session.close()
