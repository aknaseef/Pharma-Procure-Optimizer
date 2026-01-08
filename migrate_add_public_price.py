"""
Database Migration: Add public_selling_price column to supplier_offers table
"""
from sqlalchemy import create_engine, text
from config import DATABASE_PATH

def migrate():
    engine = create_engine(DATABASE_PATH)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(supplier_offers)"))
        columns = [row[1] for row in result]
        
        if 'public_selling_price' not in columns:
            print("Adding public_selling_price column to supplier_offers...")
            conn.execute(text("ALTER TABLE supplier_offers ADD COLUMN public_selling_price FLOAT"))
            conn.commit()
            print("✅ Migration completed successfully!")
        else:
            print("⚠️  Column public_selling_price already exists. Skipping migration.")

if __name__ == "__main__":
    migrate()
