from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class MasterProduct(Base):
    __tablename__ = 'master_products'
    id = Column(Integer, primary_key=True)
    item_code = Column(String, unique=True, nullable=False)
    product_name = Column(String, nullable=False)
    simplified_name = Column(String, index=True)  # New: Simplified for matching
    dosage = Column(String)
    pack_size = Column(String) # Handled as string "24s", "100ml"
    standard_cost = Column(Float)

class SupplierOffer(Base):
    __tablename__ = 'supplier_offers'
    id = Column(Integer, primary_key=True)
    supplier_name = Column(String, nullable=False)
    list_tag = Column(String, nullable=False, default="General") # New: For Partial Updates
    raw_product_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)  # Net rate (what pharmacy pays supplier)
    public_selling_price = Column(Float)   # Official public price (must match master's standard_cost)
    supplier_pack_size = Column(Integer, default=1) # New: For Unit Normalization
    normalized_cost = Column(Float) # New: base unit cost
    bonus_string = Column(String)
    expiry_date = Column(Date)
    credit_period_days = Column(Integer)
    matched_master_id = Column(Integer, ForeignKey('master_products.id'))
    
    master_product = relationship("MasterProduct")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key=True)
    archived_at = Column(DateTime, default=datetime.utcnow)
    supplier_name = Column(String)
    list_tag = Column(String)
    raw_product_name = Column(String)
    price = Column(Float)
    supplier_pack_size = Column(Integer)
    normalized_cost = Column(Float)
    bonus_string = Column(String)
    expiry_date = Column(Date)
    
class ProductAlias(Base):
    __tablename__ = 'product_aliases'
    id = Column(Integer, primary_key=True)
    alias_name = Column(String, nullable=False)
    master_product_id = Column(Integer, ForeignKey('master_products.id'), nullable=False)
    
    master_product = relationship("MasterProduct")

if __name__ == "__main__":
    engine = create_engine('sqlite:///pharma.db')
    Base.metadata.create_all(engine)
    print("Database initialized successfully with new schema.")
