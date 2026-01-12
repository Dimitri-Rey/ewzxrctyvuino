"""Database models using SQLAlchemy."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum
from enum import Enum as PyEnum
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
    # Get absolute path for data directory
    data_dir = os.path.abspath("./data")
    os.makedirs(data_dir, exist_ok=True)
    # Ensure the directory has write permissions
    os.chmod(data_dir, 0o755)
    
    # If path is relative, make it absolute
    if not os.path.isabs(db_path):
        # Extract just the filename if it includes a directory
        if "/" in db_path or "\\" in db_path:
            filename = os.path.basename(db_path)
            db_path = os.path.join(data_dir, filename)
        else:
            db_path = os.path.join(data_dir, db_path)
    else:
        # If absolute, ensure parent directory exists
        parent_dir = os.path.dirname(db_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
    
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
    # Relationship with reviews
    reviews = relationship("Review", back_populates="location", cascade="all, delete-orphan")


class Review(Base):
    """Model for Google Business Profile reviews."""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    review_id = Column(String, unique=True, index=True, nullable=False)
    author_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    reply = Column(Text, nullable=True)
    reply_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)  # Date de création de l'avis
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Date de synchronisation
    
    # Relationship with location
    location = relationship("Location", back_populates="reviews")


class ReplyTemplate(Base):
    """Model for reply templates."""
    __tablename__ = "reply_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # Template content with variables
    rating_min = Column(Integer, nullable=False, default=1)  # Minimum rating (1-5)
    rating_max = Column(Integer, nullable=False, default=5)  # Maximum rating (1-5)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PendingReplyStatus(PyEnum):
    """Status enum for pending replies."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PendingReply(Base):
    """Model for pending replies awaiting approval."""
    __tablename__ = "pending_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, unique=True)
    suggested_reply = Column(Text, nullable=False)
    status = Column(Enum(PendingReplyStatus), default=PendingReplyStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationship with review
    review = relationship("Review", backref="pending_reply")


def init_db():
    """Initialize the database by creating all tables and default templates."""
    import os
    # Create data directory if using SQLite
    if "sqlite" in settings.DATABASE_URL:
        data_dir = os.path.abspath("./data")
        os.makedirs(data_dir, exist_ok=True)
        os.chmod(data_dir, 0o755)
    
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating database tables: {e}")
        raise
    
    # Create default templates
    _create_default_templates()


def _create_default_templates():
    """Create default reply templates if they don't exist."""
    import logging
    logger = logging.getLogger(__name__)
    
    db = SessionLocal()
    try:
        # Check if templates already exist
        existing_templates = db.query(ReplyTemplate).count()
        if existing_templates > 0:
            logger.info("Default templates already exist, skipping creation")
            return  # Templates already exist
        
        # Template 5 étoiles : Remerciement chaleureux
        template_5 = ReplyTemplate(
            name="5 étoiles - Remerciement chaleureux",
            content="Bonjour {author_name},\n\nMerci infiniment pour votre excellent avis et vos 5 étoiles ! Nous sommes ravis d'apprendre que votre expérience chez {location_name} a été à la hauteur de vos attentes.\n\nVotre satisfaction est notre priorité et nous sommes honorés de votre confiance. Nous espérons vous revoir très bientôt !\n\nCordialement,\nL'équipe de {location_name}",
            rating_min=5,
            rating_max=5,
            is_active=True
        )
        
        # Template 4 étoiles : Remerciement + demande d'amélioration
        template_4 = ReplyTemplate(
            name="4 étoiles - Remerciement et amélioration",
            content="Bonjour {author_name},\n\nMerci beaucoup pour votre avis et vos 4 étoiles concernant {location_name} ! Nous sommes heureux d'apprendre que vous avez globalement apprécié votre expérience.\n\nNous prenons note de vos commentaires et nous nous efforçons constamment d'améliorer nos services. N'hésitez pas à nous contacter directement si vous souhaitez partager des suggestions spécifiques.\n\nNous espérons vous accueillir à nouveau et vous offrir une expérience encore meilleure !\n\nCordialement,\nL'équipe de {location_name}",
            rating_min=4,
            rating_max=4,
            is_active=True
        )
        
        # Template 3 étoiles : Remerciement + proposition de contact
        template_3 = ReplyTemplate(
            name="3 étoiles - Remerciement et contact",
            content="Bonjour {author_name},\n\nMerci d'avoir pris le temps de partager votre avis sur {location_name}. Nous sommes désolés d'apprendre que votre expérience n'a pas été entièrement satisfaisante.\n\nVotre retour est précieux pour nous et nous aimerions en savoir plus sur ce qui n'a pas fonctionné. Nous vous invitons à nous contacter directement afin que nous puissions discuter de votre expérience et trouver une solution adaptée.\n\nNous espérons avoir l'occasion de vous offrir une meilleure expérience à l'avenir.\n\nCordialement,\nL'équipe de {location_name}",
            rating_min=3,
            rating_max=3,
            is_active=True
        )
        
        # Template 1-2 étoiles : Excuses + proposition de résolution
        template_1_2 = ReplyTemplate(
            name="1-2 étoiles - Excuses et résolution",
            content="Bonjour {author_name},\n\nNous sommes sincèrement désolés d'apprendre que votre expérience chez {location_name} n'a pas été à la hauteur de vos attentes. Nous prenons votre avis très au sérieux.\n\nNous aimerions comprendre ce qui s'est mal passé et trouver une solution. Nous vous invitons vivement à nous contacter directement afin que nous puissions discuter de votre situation et faire notre possible pour résoudre le problème.\n\nVotre satisfaction est notre priorité et nous nous engageons à améliorer nos services pour éviter que cela ne se reproduise.\n\nNous espérons avoir l'opportunité de regagner votre confiance.\n\nCordialement,\nL'équipe de {location_name}",
            rating_min=1,
            rating_max=2,
            is_active=True
        )
        
        db.add(template_5)
        db.add(template_4)
        db.add(template_3)
        db.add(template_1_2)
        db.commit()
        logger.info("Default templates created successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating default templates: {e}")
    finally:
        db.close()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


