"""Database models using SQLAlchemy."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.config import settings

# Create database engine
# For SQLite, ensure the path is correct and thread-safe
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    # Extract the path after sqlite:///
    db_path = db_url.replace("sqlite:///", "")
    # Ensure data directory exists
    import os
    os.makedirs("./data", exist_ok=True)
    # Use absolute path for better compatibility
    if not os.path.isabs(db_path):
        db_path = os.path.join("./data", db_path)
    db_url = f"sqlite:///{db_path}"

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Account(Base):
    """Model for Google Business Profile accounts."""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    google_email = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship with locations
    locations = relationship("Location", back_populates="account", cascade="all, delete-orphan")


class Location(Base):
    """Model for Google Business Profile locations."""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    location_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship with account
    account = relationship("Account", back_populates="locations")


def init_db():
    """Initialize the database by creating all tables."""
    import os
    # Create data directory if using SQLite
    if "sqlite" in settings.DATABASE_URL:
        os.makedirs("./data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
