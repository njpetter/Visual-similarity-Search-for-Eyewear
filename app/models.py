"""
Database models for product metadata
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Product(Base):
    """Product metadata model"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, unique=True, index=True)
    brand = Column(String, index=True)
    price = Column(Float, index=True)
    material = Column(String, index=True)
    style_tags = Column(String)  # Comma-separated tags like "Aviator,Black,Metal"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # For feedback loop
    click_count = Column(Integer, default=0)
    relevance_score = Column(Float, default=0.0)


class Feedback(Base):
    """User feedback model for learning"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    query_image_path = Column(String)
    product_id = Column(Integer, index=True)
    is_relevant = Column(Integer)  # 1 for relevant, 0 for not relevant
    created_at = Column(DateTime, default=datetime.utcnow)


# Database setup
DATABASE_URL = "sqlite:///./data/db.sqlite"
os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

