import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from setup_db import MasterProduct, SupplierOffer, ProductAlias, PriceHistory
from logic import calculate_euc, fuzzy_match, parse_pack_size
import plotly.express as px
import plotly.graph_objects as go
import time
import re
import logging
from datetime import datetime, timedelta

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

# ============================================
# CUSTOM THEME & STYLING
# ============================================

CUSTOM_CSS = """
<style>
/* === Remove Default Streamlit Top Padding === */
.stApp > header {
    display: none !important;
}

.block-container {
    padding-top: 1rem !important;
}

#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* === Color Palette === */
:root {
    --primary: #0D9488;
    --primary-dark: #0F766E;
    --primary-light: #2DD4BF;
    --accent: #FBBF24;
    --danger: #F87171;
    --warning: #FB923C;
    --success: #4ADE80;
    --bg-dark: #111827;
    --bg-card: #1F2937;
    --text-primary: #FFFFFF;
    --text-secondary: #D1D5DB;
}

/* === Main App Styling === */
.stApp {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
}

/* === Global Text Visibility === */
.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
    color: #FFFFFF !important;
}

.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

.stMarkdown p, .stMarkdown span {
    color: #E5E7EB !important;
    font-size: 1rem !important;
}

/* Caption styling for better visibility */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #D1D5DB !important;
    font-size: 0.9rem !important;
}

/* Input labels */
.stTextInput label, .stSelectbox label, .stNumberInput label {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Metric values */
[data-testid="stMetricValue"] {
    color: #2DD4BF !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    color: #D1D5DB !important;
    font-weight: 600 !important;
}

/* Dataframe/Table text */
.stDataFrame {
    color: #FFFFFF !important;
}

/* Expander headers */
.streamlit-expanderHeader {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* === Styled Header === */
.main-header {
    background: linear-gradient(90deg, var(--primary) 0%, var(--primary-dark) 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 40px rgba(13, 148, 136, 0.3);
}

.main-header h1 {
    color: white !important;
    margin: 0 !important;
    font-weight: 700 !important;
}

.main-header p {
    color: rgba(255,255,255,0.8) !important;
    margin: 0.5rem 0 0 0 !important;
}

/* === Metric Cards === */
.metric-card {
    background: linear-gradient(145deg, #1F2937 0%, #374151 100%);
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 4px solid var(--primary);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(13, 148, 136, 0.2);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--primary-light);
    margin: 0;
}

.metric-label {
    color: #E5E7EB;
    font-size: 0.95rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
}

/* === Deal Cards === */
.deal-card {
    background: linear-gradient(145deg, #1F2937 0%, #374151 100%);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #374151;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.deal-card:hover {
    border-color: var(--primary);
    box-shadow: 0 8px 32px rgba(13, 148, 136, 0.2);
}

.deal-card.best-deal {
    border: 2px solid var(--accent);
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
}

.best-badge {
    position: absolute;
    top: 0;
    right: 0;
    background: linear-gradient(135deg, var(--accent) 0%, #D97706 100%);
    color: #111827;
    padding: 0.5rem 1rem;
    font-weight: 700;
    font-size: 0.75rem;
    border-radius: 0 12px 0 12px;
}

.risk-indicator {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 6px;
    border-radius: 12px 0 0 12px;
}

.risk-safe { background: var(--success); }
.risk-medium { background: var(--warning); }
.risk-high { background: var(--danger); }

/* === Upload Zones === */
.upload-zone {
    border: 2px dashed #4B5563;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    background: rgba(31, 41, 55, 0.5);
    transition: all 0.3s ease;
}

.upload-zone:hover {
    border-color: var(--primary);
    background: rgba(13, 148, 136, 0.1);
}

/* === File Uploader Text Visibility === */
[data-testid="stFileUploader"] {
    color: #FFFFFF !important;
}

[data-testid="stFileUploader"] section {
    background: rgba(31, 41, 55, 0.8) !important;
    border: 2px dashed #6B7280 !important;
    border-radius: 12px !important;
}

[data-testid="stFileUploader"] section > div {
    color: #FFFFFF !important;
}

[data-testid="stFileUploader"] small {
    color: #D1D5DB !important;
}

[data-testid="stFileUploader"] span {
    color: #FFFFFF !important;
}

[data-testid="stFileUploader"] p {
    color: #E5E7EB !important;
}

/* Target the drag and drop text specifically */
[data-testid="stFileUploaderDropzone"] {
    color: #FFFFFF !important;
}

[data-testid="stFileUploaderDropzone"] > div {
    color: #FFFFFF !important;
}

[data-testid="stFileUploaderDropzone"] span {
    color: #FFFFFF !important;
    font-weight: 500 !important;
}

[data-testid="stFileUploaderDropzone"] small, 
[data-testid="stFileUploaderDropzone"] p {
    color: #D1D5DB !important;
}

/* Streamlit uploader button */
[data-testid="stFileUploader"] button {
    background: var(--primary) !important;
    color: #FFFFFF !important;
}

/* === Tabs Styling === */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    background: #1F2937;
    border-radius: 8px 8px 0 0;
    padding: 0.75rem 1.5rem;
    color: var(--text-secondary);
    border: 1px solid #374151;
    border-bottom: none;
}

.stTabs [aria-selected="true"] {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
}

/* === Buttons === */
.stButton > button {
    background: linear-gradient(90deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.4);
}

/* === Download Button Fix === */
[data-testid="stDownloadButton"] button,
[data-testid="stDownloadButton"] > button,
.stDownloadButton > button {
    background: linear-gradient(90deg, #0D9488 0%, #0F766E 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
}

[data-testid="stDownloadButton"] button *,
[data-testid="stDownloadButton"] button span,
[data-testid="stDownloadButton"] button p,
[data-testid="stDownloadButton"] button div {
    color: #FFFFFF !important;
}

[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(90deg, #14B8A6 0%, #0D9488 100%) !important;
}

/* Warning text visibility fix */
.stWarning, [data-testid="stWarning"], [data-testid="stAlert"] {
    background-color: #FEF3C7 !important;
    border: 1px solid #F59E0B !important;
    border-radius: 8px !important;
}

.stWarning p, [data-testid="stWarning"] p,
.stWarning span, [data-testid="stWarning"] span,
[data-testid="stAlert"] p, [data-testid="stAlert"] span,
[data-testid="stAlert"] div {
    color: #78350F !important;
    font-weight: 500 !important;
}

/* Alert icon visibility */
.stWarning svg, [data-testid="stWarning"] svg,
[data-testid="stAlert"] svg {
    fill: #D97706 !important;
}

/* === DataFrames === */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}

/* === Expander Styling === */
.streamlit-expanderHeader {
    background: #1F2937;
    border-radius: 8px;
}

/* === Cart Badge === */
.cart-badge {
    background: var(--accent);
    color: #111827;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.875rem;
}

/* === Progress Steps === */
.progress-step {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: #1F2937;
    border-radius: 8px;
    margin-bottom: 0.5rem;
}

.step-number {
    width: 28px;
    height: 28px;
    background: var(--primary);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    color: white;
}

.step-complete { background: var(--success); }
.step-active { background: var(--accent); animation: pulse 2s infinite; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* === Empty State === */
.empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-secondary);
}

.empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
}

/* === Savings Badge === */
.savings-badge {
    background: linear-gradient(135deg, var(--success) 0%, #16A34A 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>
"""

# Page Config
st.set_page_config(
    page_title="Pharma-Procure Optimizer",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject Custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Database Connection (using config)
engine = create_engine(DATABASE_PATH)
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()

# ============================================
# HELPER FUNCTIONS
# ============================================

def find_index(columns, keywords):
    """Returns index of first column matching any keyword (case-insensitive partial match)."""
    cols_lower = [c.lower() for c in columns]
    for i, col in enumerate(cols_lower):
        for kw in keywords:
            if kw in col:
                return i
    return 0

def validate_file_upload(uploaded_file, max_size_mb: int = MAX_FILE_SIZE_MB) -> tuple:
    """Validate uploaded file size."""
    if uploaded_file is None:
        return False, "No file uploaded"
    
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        logger.warning(f"File too large: {file_size_mb:.2f}MB > {max_size_mb}MB limit")
        return False, f"File too large ({file_size_mb:.1f}MB). Maximum allowed: {max_size_mb}MB"
    
    return True, None

def render_metric_card(value, label, icon="📊"):
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">{icon} {label}</p>
        <p class="metric-value">{value}</p>
    </div>
    """, unsafe_allow_html=True)

def render_deal_card(row, is_best=False, savings_pct=None):
    """Render a styled deal card using Streamlit native components for reliability."""
    risk = str(row.get('Risk', 'Safe'))
    
    # Card container with styling
    if is_best:
        st.markdown("""
        <div style="background: linear-gradient(145deg, #1F2937 0%, #374151 100%); 
                    border-radius: 16px; border: 2px solid #F59E0B; 
                    box-shadow: 0 0 20px rgba(245, 158, 11, 0.3); 
                    padding: 1.5rem; margin-bottom: 0.5rem; position: relative;">
            <div style="position: absolute; top: 0; right: 0; 
                        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
                        color: #111827; padding: 0.5rem 1rem; font-weight: 700; 
                        font-size: 0.75rem; border-radius: 0 12px 0 12px;">🏆 BEST DEAL</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(145deg, #1F2937 0%, #374151 100%); 
                    border-radius: 16px; border: 1px solid #374151; 
                    padding: 1.5rem; margin-bottom: 0.5rem;">
        </div>
        """, unsafe_allow_html=True)
    
    # Use native Streamlit for content (more reliable)
    product_name = str(row.get('Product', 'Unknown'))[:40]
    supplier = str(row.get('Supplier', 'Unknown'))
    tag = str(row.get('Tag', 'General'))
    
    st.markdown(f"**{product_name}**")
    st.caption(f"{supplier} • {tag}")
    
    # Metrics in columns
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Unit Cost", f"{row.get('Norm. Unit Cost', 0):.4f}")
    with m2:
        st.metric("Pack Price", f"{row.get('Price (Pack)', 0)}")
    
    m3, m4 = st.columns(2)
    with m3:
        st.caption(f"📦 Pack: {row.get('Pack Size', 1)}")
    with m4:
        st.caption(f"📆 Credit: {row.get('Credit Days', 30)}d")
    
    # Risk and savings badges
    if "High" in risk:
        st.markdown("🔴 **High Risk**")
    elif "Medium" in risk:
        st.markdown("🟠 **Medium Risk**")
    else:
        st.markdown("🟢 **Safe**")
    
    if savings_pct and savings_pct > 0:
        st.success(f"💰 Save {savings_pct:.0f}%")

def render_empty_state(icon, title, message):
    """Render an empty state with icon and message."""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <h3>{title}</h3>
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)

# Initialize Session State for Cart
if 'cart' not in st.session_state:
    st.session_state.cart = []

# ============================================
# HEADER
# ============================================

st.markdown("""
<div class="main-header">
    <h1>💊 Pharma-Procure Optimizer</h1>
    <p>Smart inventory purchasing • Compare suppliers • Maximize savings</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# TABS
# ============================================

tab0, tab1, tab2, tab3 = st.tabs([
    "📊 Dashboard",
    "📂 Upload & Process",
    "🔍 Matching Workbench",
    "🛒 Best Buy & Cart"
])

# ============================================
# TAB 0: DASHBOARD
# ============================================

with tab0:
    st.header("Dashboard Overview")
    
    session = get_db_session()
    
    # Get counts
    total_products = session.query(MasterProduct).count()
    total_offers = session.query(SupplierOffer).count()
    suppliers = session.query(SupplierOffer.supplier_name).distinct().all()
    supplier_count = len(suppliers)
    unmatched_count = session.query(SupplierOffer).filter(SupplierOffer.matched_master_id.is_(None)).count()
    cart_count = len(st.session_state.cart)
    
    # Summary Cards
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        render_metric_card(total_products, "Master Products", "📦")
    with col2:
        render_metric_card(supplier_count, "Active Suppliers", "🏢")
    with col3:
        render_metric_card(total_offers, "Price Offers", "💰")
    with col4:
        render_metric_card(unmatched_count, "Unmatched", "⚠️")
    with col5:
        render_metric_card(cart_count, "Cart Items", "🛒")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("📊 Weighted Avg Unit Cost by Supplier")
        
        # Get supplier weighted avg costs (weighted by pack price/value)
        # Formula: SUM(normalized_cost * price) / SUM(price)
        supplier_costs = session.query(
            SupplierOffer.supplier_name,
            (func.sum(SupplierOffer.normalized_cost * SupplierOffer.price) / 
             func.sum(SupplierOffer.price)).label('avg_cost')
        ).filter(
            SupplierOffer.price > 0  # Avoid division issues
        ).group_by(SupplierOffer.supplier_name).all()
        
        if supplier_costs:
            df_suppliers = pd.DataFrame(supplier_costs, columns=['Supplier', 'Avg Unit Cost'])
            df_suppliers = df_suppliers.sort_values('Avg Unit Cost', ascending=True)
            
            fig = px.bar(
                df_suppliers,
                x='Supplier',
                y='Avg Unit Cost',
                color='Avg Unit Cost',
                color_continuous_scale=['#14B8A6', '#0D9488', '#0F766E'],
                template='plotly_dark'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#9CA3AF',
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            render_empty_state("📊", "No Data Yet", "Upload supplier offers to see comparisons")
    
    with chart_col2:
        st.subheader("🎯 Expiry Risk Distribution")
        
        # Get expiry risk breakdown
        offers_with_expiry = session.query(SupplierOffer).filter(SupplierOffer.expiry_date.isnot(None)).all()
        
        if offers_with_expiry:
            today = datetime.now().date()
            risk_counts = {'Safe': 0, 'Medium Risk': 0, 'High Risk': 0}
            
            for o in offers_with_expiry:
                days = (o.expiry_date - today).days
                if days < RISK_HIGH_DAYS:
                    risk_counts['High Risk'] += 1
                elif days < RISK_MEDIUM_DAYS:
                    risk_counts['Medium Risk'] += 1
                else:
                    risk_counts['Safe'] += 1
            
            df_risk = pd.DataFrame({
                'Risk Level': list(risk_counts.keys()),
                'Count': list(risk_counts.values())
            })
            
            fig = px.pie(
                df_risk,
                values='Count',
                names='Risk Level',
                color='Risk Level',
                color_discrete_map={
                    'Safe': '#22C55E',
                    'Medium Risk': '#F97316',
                    'High Risk': '#EF4444'
                },
                hole=0.4,
                template='plotly_dark'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#9CA3AF',
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            render_empty_state("📅", "No Expiry Data", "Upload offers with expiry dates to see risk distribution")
    
    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    qcol1, qcol2, qcol3 = st.columns(3)
    with qcol1:
        if st.button("📂 Upload New Data", use_container_width=True):
            st.toast("Switch to 'Upload & Process' tab to add data")
    with qcol2:
        if st.button("🔍 Review Unmatched", use_container_width=True):
            st.toast(f"You have {unmatched_count} unmatched products to review")
    with qcol3:
        if st.button("🛒 View Cart", use_container_width=True):
            st.toast(f"Your cart has {cart_count} items")
    
    session.close()

# ============================================
# TAB 1: UPLOAD & PROCESS
# ============================================

with tab1:
    st.header("📂 Upload Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="upload-zone">
            <h3 style="color: #14B8A6; margin: 0;">📋 Master Product List</h3>
            <p style="color: #9CA3AF;">Upload your master inventory list (Excel)</p>
        </div>
        """, unsafe_allow_html=True)
        
        master_file = st.file_uploader("Upload Master List (Excel)", type=["xlsx"], key="master_upload", label_visibility="collapsed")
        
        if master_file:
            is_valid, error_msg = validate_file_upload(master_file)
            if not is_valid:
                st.error(error_msg)
            else:
                try:
                    df_master_preview = pd.read_excel(master_file)
                    st.success(f"✅ File loaded: {len(df_master_preview)} rows")
                    
                    with st.expander("👀 Preview Data", expanded=True):
                        st.dataframe(df_master_preview.head(5), use_container_width=True)
                    
                    df_master_preview.columns = df_master_preview.columns.str.strip().str.lower()
                    cols = df_master_preview.columns.tolist()
                    
                    st.markdown("### 🔗 Map Columns")
                    
                    # Auto-detect columns with visual indicators
                    idx_name = find_index(cols, ['product_name', 'product name', 'trade name', 'item name', 'description'])
                    idx_code = find_index(cols, ['code', 'item code', 'item_code', 'sku'])
                    idx_dosage = find_index(cols, ['dosage', 'strength', 'uom'])
                    idx_pack = find_index(cols, ['pack', 'size'])
                    idx_cost = find_index(cols, ['cost', 'standard', 'price', 'rate', 'retail'])

                    m1, m2 = st.columns(2)
                    with m1:
                        col_name = st.selectbox("📝 Product Name", cols, index=idx_name, key='m_name')
                        col_dosage = st.selectbox("💊 Dosage", ["None"] + cols, index=idx_dosage + 1 if idx_dosage > 0 or (idx_dosage==0 and 'dosage' in cols[0]) else 0, key='m_dose')
                        col_cost = st.selectbox("💰 Standard Cost", ["None"] + cols, index=idx_cost + 1 if idx_cost > 0 or (idx_cost==0 and 'cost' in cols[0]) else 0, key='m_cost')
                    with m2:
                        col_code = st.selectbox("🏷️ Item Code", cols, index=idx_code, key='m_code')
                        col_pack = st.selectbox("📦 Pack Size", ["None"] + cols, index=idx_pack + 1 if idx_pack > 0 or (idx_pack==0 and 'pack' in cols[0]) else 0, key='m_pack')

                    if st.button("⚡ Process Master List", type="primary", use_container_width=True):
                        df_master = df_master_preview
                        df_master = df_master.dropna(subset=[col_name])
                        
                        session = get_db_session()
                        count = 0
                        progress = st.progress(0, text="Processing...")
                        
                        for index, row in df_master.iterrows():
                            p_name = str(row[col_name])
                            item_code = str(row[col_code])
                            
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
                            
                            if index % 50 == 0:
                                progress.progress(min(index / len(df_master), 1.0), text=f"Processing row {index}...")
                        
                        session.commit()
                        session.close()
                        progress.progress(1.0, text="Complete!")
                        st.toast(f"✅ Added {count} new products!", icon="🎉")
                        st.success(f"Successfully added **{count}** new products to Master List.")
                        
                except Exception as e:
                    st.error(f"Error reading file: {e}")

    with col2:
        st.markdown("""
        <div class="upload-zone">
            <h3 style="color: #F59E0B; margin: 0;">📄 Supplier Price Sheet</h3>
            <p style="color: #9CA3AF;">Upload supplier offers (Excel/CSV)</p>
        </div>
        """, unsafe_allow_html=True)
        
        supplier_file = st.file_uploader("Upload Supplier Sheet (Excel/CSV)", type=["xlsx", "csv"], key="supplier_upload", label_visibility="collapsed")
        
        c_sup, c_tag = st.columns(2)
        supplier_name = c_sup.text_input("🏢 Supplier Name")
        list_tag = c_tag.text_input("🏷️ List Tag", value="General")
        
        if supplier_file and supplier_name and list_tag:
            if supplier_file.name.endswith('.csv'):
                df_supplier = pd.read_csv(supplier_file)
            else:
                df_supplier = pd.read_excel(supplier_file)
            
            with st.expander("👀 Preview Data", expanded=True):
                st.dataframe(df_supplier.head(5), use_container_width=True)
            
            st.markdown("### 🔗 Map Columns")
            cols = df_supplier.columns.tolist()
            
            idx_item = find_index(cols, ['name', 'item', 'description', 'product', 'drug'])
            idx_price = find_index(cols, ['price', 'rate', 'cost', 'public', 'net', 'aed'])
            idx_pack = find_index(cols, ['pack', 'size', 'uom', 'format'])
            idx_bonus = find_index(cols, ['bonus', 'offer', 'free', 'scheme', 'deal'])
            idx_expiry = find_index(cols, ['expiry', 'exp', 'valid', 'date'])
            idx_credit = find_index(cols, ['credit', 'term', 'payment'])

            m1, m2 = st.columns(2)
            with m1:
                col_item = st.selectbox("📝 Item Name", cols, index=idx_item)
                col_pack = st.selectbox("📦 Pack Size", ["None"] + cols, index=idx_pack + 1 if idx_pack > 0 or (idx_pack==0 and 'pack' in cols[0].lower()) else 0)
                col_expiry = st.selectbox("📅 Expiry Date", ["None"] + cols, index=idx_expiry + 1 if idx_expiry > 0 or (idx_expiry==0 and 'exp' in cols[0].lower()) else 0)
            with m2:
                col_price = st.selectbox("💰 Price", cols, index=idx_price)
                col_bonus = st.selectbox("🎁 Bonus", ["None"] + cols, index=idx_bonus + 1 if idx_bonus > 0 or (idx_bonus==0 and 'bonus' in cols[0].lower()) else 0)
                col_credit = st.selectbox("📆 Credit Terms", ["None"] + cols, index=idx_credit + 1 if idx_credit > 0 or (idx_credit==0 and 'credit' in cols[0].lower()) else 0)
            
            st.markdown("---")
            manual_credit_days = st.slider("🕐 Default Credit Period (days)", 0, 120, 30)
            
            if st.button("⚡ Process & Archive Old Data", type="primary", use_container_width=True):
                session = get_db_session()
                
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
                
                processed_count = 0
                progress_bar = st.progress(0, text="Processing offers...")
                
                for index, row in df_supplier.iterrows():
                    raw_name = str(row[col_item])
                    
                    try:
                        price_val = row[col_price]
                        if pd.isnull(price_val):
                            price = 0.0
                        else:
                            p_str = str(price_val).upper().replace('AED', '').replace('RS', '').replace('$', '').strip()
                            price = float(p_str)
                    except ValueError:
                        match_price = re.search(r"(\d+(\.\d+)?)", str(row[col_price]))
                        price = float(match_price.group(1)) if match_price else 0.0
                    
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
                    
                    credit_days = manual_credit_days
                    if col_credit != "None" and pd.notnull(row[col_credit]):
                        c_str = str(row[col_credit])
                        match_c = re.search(r"(\d+)", c_str)
                        if match_c:
                            credit_days = int(match_c.group(1))

                    match_result = fuzzy_match(raw_name, session, price)
                    matched_id = match_result['master_id'] if match_result else None
                    
                    euc, _, norm_cost = calculate_euc(price, pack_val, bonus)
                    
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
                        progress_bar.progress(min(index / len(df_supplier), 1.0), text=f"Row {index}/{len(df_supplier)}")
                
                session.commit()
                session.close()
                progress_bar.progress(1.0, text="Complete!")
                st.toast(f"✅ Processed {processed_count} offers!", icon="🎉")
                st.success(f"Archived **{archived_count}** old records. Processed **{processed_count}** new offers.")
                time.sleep(1)
                st.rerun()

# ============================================
# TAB 2: MATCHING WORKBENCH
# ============================================

with tab2:
    st.header("🔍 Matching Workbench")
    
    session = get_db_session()
    
    # Filters
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    with filter_col1:
        supplier_filter = st.selectbox(
            "Filter by Supplier",
            ["All Suppliers"] + [s.supplier_name for s in session.query(SupplierOffer.supplier_name).distinct().all()]
        )
    with filter_col2:
        match_status = st.selectbox("Match Status", ["All", "Unmatched Only", "Matched Only"])
    with filter_col3:
        st.write("")
        st.write("")
        refresh_btn = st.button("🔄 Refresh", use_container_width=True)
    
    # Build query
    query = session.query(SupplierOffer)
    if supplier_filter != "All Suppliers":
        query = query.filter(SupplierOffer.supplier_name == supplier_filter)
    if match_status == "Unmatched Only":
        query = query.filter(SupplierOffer.matched_master_id.is_(None))
    elif match_status == "Matched Only":
        query = query.filter(SupplierOffer.matched_master_id.isnot(None))
    
    offers = query.all()
    
    data = []
    for o in offers:
        match_name = o.master_product.product_name if o.master_product else "❌ NO MATCH"
        match_status_icon = "✅" if o.master_product else "⚠️"
        data.append({
            "ID": o.id,
            "Status": match_status_icon,
            "Supplier": o.supplier_name,
            "Product": o.raw_product_name,
            "Matched To": match_name,
            "Unit Cost": f"{o.normalized_cost:.4f}" if o.normalized_cost else "-"
        })
    
    if data:
        st.markdown(f"**Showing {len(data)} offers**")
        st.dataframe(pd.DataFrame(data), use_container_width=True, height=400)
        
        st.markdown("---")
        st.subheader("🔗 Manual Linking")
        
        link_col1, link_col2 = st.columns(2)
        
        with link_col1:
            st.markdown("**Select Offer to Link**")
            offer_id = st.number_input("Offer ID", min_value=1, step=1, key="link_offer_id")
            
            # Show selected offer details
            if offer_id:
                selected_offer = session.get(SupplierOffer, offer_id)
                if selected_offer:
                    st.info(f"**Product:** {selected_offer.raw_product_name}")
        
        with link_col2:
            st.markdown("**Find Master Product**")
            search = st.text_input("Search Master Products", placeholder="Type to search...")
            target_id = None
            
            if search:
                res = session.query(MasterProduct).filter(MasterProduct.product_name.ilike(f"%{search}%")).limit(10).all()
                if res:
                    options = [f"{r.product_name} (ID: {r.id})" for r in res]
                    sel = st.selectbox("Select Master Product", options)
                    target_id = int(sel.split('ID: ')[-1].replace(')', ''))
                else:
                    st.warning("No matching products found")
        
        if st.button("✅ Link Products", type="primary", use_container_width=True):
            if offer_id and target_id:
                o = session.get(SupplierOffer, offer_id)
                if o:
                    o.matched_master_id = target_id
                    pa = ProductAlias(alias_name=o.raw_product_name, master_product_id=target_id)
                    session.add(pa)
                    session.commit()
                    st.toast("✅ Products linked successfully!", icon="🔗")
                    st.success("Linked! This alias will be remembered for future imports.")
            else:
                st.error("Please select both an offer ID and a master product")
    else:
        render_empty_state("🎉", "All Matched!", "Great job! All your products are matched.")
    
    session.close()

# ============================================
# TAB 3: BEST BUY & CART
# ============================================

with tab3:
    st.header("🛒 Best Buy Search")
    
    # Search and Cart Header
    search_col, cart_col = st.columns([3, 1])
    
    with search_col:
        query = st.text_input("🔍 Search Product", placeholder="Type product name (generic or brand)...")
    
    with cart_col:
        st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem; background: #1F2937; border-radius: 8px;">
            <span style="color: #9CA3AF;">Cart</span><br>
            <span class="cart-badge">{len(st.session_state.cart)} items</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Cart Sidebar Toggle
    show_cart = st.checkbox("📋 Show Cart Details")
    
    if show_cart:
        with st.container():
            st.markdown("---")
            st.subheader("🛒 Your Purchase Order")
            
            if st.session_state.cart:
                cart_df = pd.DataFrame(st.session_state.cart)
                st.dataframe(cart_df, use_container_width=True)
                
                total = sum(item.get('Total', 0) for item in st.session_state.cart)
                st.markdown(f"**Total: {total:.2f}**")
                
                col_dl, col_clear = st.columns(2)
                with col_dl:
                    csv = cart_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download PO (CSV)",
                        csv,
                        "purchase_order.csv",
                        "text/csv",
                        key='download-csv',
                        use_container_width=True
                    )
                with col_clear:
                    if st.button("🗑️ Clear Cart", use_container_width=True):
                        st.session_state.cart = []
                        st.toast("Cart cleared!", icon="🗑️")
                        st.rerun()
            else:
                render_empty_state("🛒", "Cart is Empty", "Search for products and add them to your cart")
        st.markdown("---")
    
    if query:
        session = get_db_session()
        masters = session.query(MasterProduct).filter(MasterProduct.product_name.ilike(f"%{query}%")).all()
        master_ids = [m.id for m in masters]
        
        if master_ids:
            results = session.query(SupplierOffer).filter(SupplierOffer.matched_master_id.in_(master_ids)).all()
            
            res_data = []
            for r in results:
                euc, _, _ = calculate_euc(r.price, r.supplier_pack_size, r.bonus_string)
                
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
                    "Norm. Unit Cost": r.normalized_cost,
                    "Expiry": r.expiry_date,
                    "Credit Days": r.credit_period_days or 30,
                    "Risk": risk
                })
            
            if res_data:
                df_res = pd.DataFrame(res_data)
                df_res = df_res.sort_values(by="Norm. Unit Cost", ascending=True)
                
                st.markdown(f"### Found **{len(df_res)}** offers • Sorted by lowest unit cost")
                
                # Risk Legend
                with st.expander("ℹ️ Understanding Risk Levels & Smart Buying Tips"):
                    st.markdown("""
                    **Risk Levels (based on Expiry Date):**
                    - 🟢 **Safe**: >12 months until expiry
                    - 🟠 **Medium Risk**: 6-12 months until expiry
                    - 🔴 **High Risk**: <6 months until expiry
                    
                    **💡 Smart Buying Tips:**
                    - Compare **Unit Cost** (not Pack Price) across suppliers
                    - Credit Period > Shelf Life Risk = Safer deal
                    - High Risk + Low Price = Only buy if turnover is fast
                    """)
                
                # Top 3 Best Deals as Cards
                st.subheader("🏆 Top Deals")
                
                top_deals = df_res.head(3).to_dict('records')
                best_cost = top_deals[0]['Norm. Unit Cost'] if top_deals else 0
                
                deal_cols = st.columns(min(3, len(top_deals)))
                for i, deal in enumerate(top_deals):
                    with deal_cols[i]:
                        savings_pct = ((df_res['Norm. Unit Cost'].max() - deal['Norm. Unit Cost']) / df_res['Norm. Unit Cost'].max() * 100) if len(df_res) > 1 else 0
                        render_deal_card(deal, is_best=(i == 0), savings_pct=savings_pct if savings_pct > 0 else None)
                        
                        qty_key = f"top_qty_{deal['RefID']}"
                        qty = st.number_input("Quantity", min_value=0, step=1, key=qty_key, label_visibility="collapsed")
                        if qty > 0:
                            if st.button(f"Add to Cart", key=f"add_{deal['RefID']}", use_container_width=True):
                                item = {
                                    "RefID": deal['RefID'],  # Track which offer this is
                                    "Supplier": deal['Supplier'],
                                    "Product": deal['Product'],
                                    "Quantity": qty,
                                    "Unit Cost": deal['Norm. Unit Cost'],
                                    "Total": qty * deal['Price (Pack)']
                                }
                                st.session_state.cart.append(item)
                                st.toast(f"Added {qty}x {deal['Product'][:20]}... to cart!", icon="🛒")
                
                # Full Results Table
                st.markdown("---")
                st.subheader("📋 All Offers")
                
                # Table Header
                h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2, 2, 1, 1, 1, 1, 1, 1])
                h1.markdown("**Supplier**")
                h2.markdown("**Product**")
                h3.markdown("**Price**")
                h4.markdown("**Unit Cost**")
                h5.markdown("**Expiry**")
                h6.markdown("**Credit**")
                h7.markdown("**Risk**")
                h8.markdown("**Qty**")
                
                # Build cart lookup: RefID -> total quantity in cart
                cart_quantities = {}
                for cart_item in st.session_state.cart:
                    ref_id = cart_item.get('RefID')
                    if ref_id:
                        cart_quantities[ref_id] = cart_quantities.get(ref_id, 0) + cart_item.get('Quantity', 0)
                
                for idx, row in df_res.iterrows():
                    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2, 2, 1, 1, 1, 1, 1, 1])
                    c1.write(f"{row['Supplier']}")
                    c2.write(f"{row['Product'][:25]}...")
                    c3.write(f"{row['Price (Pack)']}")
                    c4.markdown(f"**{row['Norm. Unit Cost']:.4f}**")
                    
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
                    
                    c6.write(f"{row['Credit Days']}d")
                    
                    color = "green"
                    if "High" in row['Risk']: color = "red"
                    elif "Medium" in row['Risk']: color = "orange"
                    c7.markdown(f":{color}[{row['Risk'][:4]}]")
                    
                    # Check if this item is already in cart and show that quantity
                    ref_id = row['RefID']
                    default_qty = cart_quantities.get(ref_id, 0)
                    key = f"qty_{ref_id}"
                    qty = c8.number_input("Qty", min_value=0, step=1, value=default_qty, key=key, label_visibility="collapsed")
                
                if st.button("🛒 Add Selected to Cart", type="primary", use_container_width=True):
                    added = 0
                    for idx, row in df_res.iterrows():
                        k = f"qty_{row['RefID']}"
                        q = st.session_state.get(k, 0)
                        if q > 0:
                            item = {
                                "RefID": row['RefID'],  # Track which offer this is
                                "Supplier": row['Supplier'],
                                "Product": row['Product'],
                                "Quantity": q,
                                "Unit Cost": row['Norm. Unit Cost'],
                                "Total": q * row['Price (Pack)']
                            }
                            st.session_state.cart.append(item)
                            added += 1
                    if added > 0:
                        st.toast(f"Added {added} items to cart!", icon="🛒")
            else:
                render_empty_state("🔍", "No Offers Found", "No supplier offers match this product yet")
        else:
            render_empty_state("🔍", "Not in Master List", "This product wasn't found in your master list")
        
        # Unmatched products section
        st.markdown("---")
        unmatched = session.query(SupplierOffer).filter(
            SupplierOffer.matched_master_id.is_(None),
            SupplierOffer.raw_product_name.ilike(f"%{query}%")
        ).all()
        
        if unmatched:
            with st.expander(f"⚠️ Unmatched Products Matching '{query}' ({len(unmatched)})", expanded=True):
                st.warning("These products match your search but need linking in 'Matching Workbench'. You can still add them to cart.")
                
                # Display unmatched items with Add to Cart option
                for idx, u in enumerate(unmatched):
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                    with col1:
                        st.markdown(f"**{u.supplier_name}**")
                    with col2:
                        st.markdown(f"{u.raw_product_name[:30]}...")
                    with col3:
                        st.markdown(f"₹{u.price}")
                    with col4:
                        qty = st.number_input("Qty", min_value=0, step=1, key=f"unmatched_qty_{u.id}", label_visibility="collapsed")
                    with col5:
                        if qty > 0:
                            if st.button("🛒", key=f"add_unmatched_{u.id}", help="Add to Cart"):
                                # Calculate normalized cost
                                pack_size = u.supplier_pack_size or 1
                                norm_cost = u.price / pack_size if pack_size > 0 else u.price
                                item = {
                                    "Supplier": u.supplier_name,
                                    "Product": u.raw_product_name,
                                    "Quantity": qty,
                                    "Unit Cost": round(norm_cost, 4),
                                    "Total": qty * u.price
                                }
                                st.session_state.cart.append(item)
                                st.toast(f"Added {qty}x {u.raw_product_name[:20]}... to cart!", icon="🛒")
                                st.rerun()
        
        session.close()
    else:
        # No search query - show helpful empty state
        session = get_db_session()
        unmatched_count = session.query(SupplierOffer).filter(SupplierOffer.matched_master_id.is_(None)).count()
        session.close()
        
        render_empty_state(
            "🔍",
            "Search for Products",
            f"Enter a product name above to find the best prices across all suppliers"
        )
        
        if unmatched_count > 0:
            st.warning(f"⚠️ You have **{unmatched_count}** unmatched products. Review them in the 'Matching Workbench' tab.")
