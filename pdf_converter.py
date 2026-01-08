"""
PDF to Excel Converter Utility
Extracts tables from PDF supplier price lists and converts them to Excel format.
"""

import pdfplumber
import pandas as pd
import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def is_header_row(row: List, header_keywords: List[str] = None) -> bool:
    """
    Check if a row is a header/title row that should be skipped.
    
    Args:
        row: List of cell values from a table row
        header_keywords: Keywords that indicate header rows
        
    Returns:
        True if the row appears to be a header
    """
    if header_keywords is None:
        header_keywords = [
            "ministry", "registration", "drug control", "price list",
            "united arab emirates", "supplier", "page", "confidential"
        ]
    
    # Convert row to string for checking
    row_str = " ".join([str(cell).lower() for cell in row if cell])
    
    # Check for header keywords
    for keyword in header_keywords:
        if keyword in row_str:
            return True
    
    # Check if row is all None or empty
    if not any(row):
        return True
        
    return False


def clean_dataframe(df: pd.DataFrame, skip_header_keywords: bool = True) -> pd.DataFrame:
    """
    Clean a DataFrame by removing header rows and empty rows.
    
    Args:
        df: Input DataFrame
        skip_header_keywords: Whether to skip rows containing header keywords
        
    Returns:
        Cleaned DataFrame
    """
    if df.empty:
        return df
    
    # Remove rows where all values are None or empty
    df = df.dropna(how='all')
    
    if skip_header_keywords:
        # Remove rows that look like headers
        mask = df.apply(
            lambda row: not is_header_row(row.tolist()),
            axis=1
        )
        df = df[mask]
    
    # Reset index
    df = df.reset_index(drop=True)
    
    return df


def extract_tables_from_pdf(pdf_file) -> List[pd.DataFrame]:
    """
    Extract all tables from a PDF file.
    
    Args:
        pdf_file: Uploaded PDF file object (Streamlit UploadedFile)
        
    Returns:
        List of DataFrames, one per detected table
    """
    tables = []
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            logger.info(f"Processing PDF with {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages):
                # Extract tables from this page
                page_tables = page.extract_tables()
                
                if page_tables:
                    for table in page_tables:
                        if table and len(table) > 1:  # At least header + 1 row
                            # Convert to DataFrame
                            # Use first row as header if it looks like one
                            first_row = table[0]
                            if is_header_row(first_row):
                                df = pd.DataFrame(table[1:], columns=first_row)
                            else:
                                df = pd.DataFrame(table[1:], columns=table[0])
                            
                            # Clean the DataFrame
                            df = clean_dataframe(df)
                            
                            if not df.empty:
                                tables.append(df)
                                logger.info(f"Extracted table from page {page_num + 1} with {len(df)} rows")
    
    except Exception as e:
        logger.error(f"Error extracting tables from PDF: {e}")
        raise
    
    return tables


def merge_tables(tables: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple tables with same columns into one DataFrame.
    
    Args:
        tables: List of DataFrames to merge
        
    Returns:
        Single merged DataFrame
    """
    if not tables:
        return pd.DataFrame()
    
    if len(tables) == 1:
        return tables[0]
    
    # Get the most common column structure
    col_counts = {}
    for df in tables:
        col_tuple = tuple(df.columns)
        col_counts[col_tuple] = col_counts.get(col_tuple, 0) + 1
    
    # Use most common column structure
    main_columns = max(col_counts.keys(), key=lambda x: col_counts[x])
    
    # Filter tables with matching column structure
    matching_tables = [df for df in tables if tuple(df.columns) == main_columns]
    
    # Concatenate
    merged = pd.concat(matching_tables, ignore_index=True)
    
    logger.info(f"Merged {len(matching_tables)} tables into {len(merged)} rows")
    
    return merged


def convert_pdf_to_excel(
    pdf_file,
    column_mapping: Dict[str, str],
    output_path: str,
    merge_all: bool = True
) -> tuple:
    """
    Convert PDF to Excel with column mapping.
    
    Args:
        pdf_file: Uploaded PDF file
        column_mapping: Dict mapping source column names to target column names
                       e.g., {'Product Details': 'Product Name', 'P.P. AED': 'Price'}
        output_path: Path where Excel file should be saved
        merge_all: Whether to merge all tables into one
        
    Returns:
        Tuple of (success: bool, message: str, row_count: int)
    """
    try:
        # Extract tables
        tables = extract_tables_from_pdf(pdf_file)
        
        if not tables:
            return False, "No tables found in PDF", 0
        
        # Merge if requested
        if merge_all:
            df = merge_tables(tables)
        else:
            df = tables[0]  # Use first table
        
        # Apply column mapping
        # Only keep columns that are mapped
        mapped_columns = {}
        for source_col, target_col in column_mapping.items():
            if source_col in df.columns and target_col:  # target_col not None/empty
                mapped_columns[source_col] = target_col
        
        df = df[list(mapped_columns.keys())]
        df = df.rename(columns=mapped_columns)
        
        # Clean up the data
        for col in df.columns:
            # Remove newlines and extra whitespace
            df[col] = df[col].astype(str).str.replace('\n', ' ').str.strip()
            # Replace 'None' string with empty
            df[col] = df[col].replace('None', '')
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        
        logger.info(f"Successfully converted PDF to Excel: {len(df)} rows saved to {output_path}")
        
        return True, f"Successfully converted {len(df)} rows", len(df)
        
    except Exception as e:
        logger.error(f"Error converting PDF to Excel: {e}")
        return False, f"Error: {str(e)}", 0


def get_column_suggestions(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Suggest column mappings based on column names in the DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with target field names as keys and suggested source columns as values
    """
    suggestions = {
        'Product Name': None,
        'Public Selling Price': None,  # Official regulated price
        'Net Rate': None,               # What pharmacy pays supplier
        'Pack Size': None,
        'Bonus': None,
        'Expiry Date': None,
        'Credit Terms': None
    }
    
    columns_lower = {col: col.lower() for col in df.columns}
    
    for col, col_lower in columns_lower.items():
        # Product Name
        if any(kw in col_lower for kw in ['product', 'name', 'item', 'description', 'drug']):
            if suggestions['Product Name'] is None:
                suggestions['Product Name'] = col
        
        # Public Selling Price (PP, MRP, Retail Price)
        if any(kw in col_lower for kw in ['public', 'pp', 'p.p', 'mrp', 'retail', 'selling price']):
            if suggestions['Public Selling Price'] is None:
                suggestions['Public Selling Price'] = col
        
        # Net Rate (Supplier Price, Offer Price, Cost)
        if any(kw in col_lower for kw in ['net', 'supplier', 'offer', 'cost', 'rate']) and 'public' not in col_lower:
            if suggestions['Net Rate'] is None:
                suggestions['Net Rate'] = col
        
        # If only "price" column exists and no public/net found, use it as net rate
        if 'price' in col_lower and suggestions['Net Rate'] is None and suggestions['Public Selling Price'] is None:
            suggestions['Net Rate'] = col
        
        # Pack Size
        if any(kw in col_lower for kw in ['pack', 'size', 'uom', 'format', 'packaging']):
            if suggestions['Pack Size'] is None:
                suggestions['Pack Size'] = col
        
        # Bonus
        if any(kw in col_lower for kw in ['bonus', 'offer', 'free', 'scheme', 'deal']):
            if suggestions['Bonus'] is None:
                suggestions['Bonus'] = col
        
        # Expiry
        if any(kw in col_lower for kw in ['expiry', 'exp', 'valid', 'date']):
            if suggestions['Expiry Date'] is None:
                suggestions['Expiry Date'] = col
        
        # Credit
        if any(kw in col_lower for kw in ['credit', 'term', 'payment', 'days']):
            if suggestions['Credit Terms'] is None:
                suggestions['Credit Terms'] = col
    
    return suggestions
