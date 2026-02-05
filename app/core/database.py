from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

from app.core.config import settings

# Create database engine
engine = create_engine(settings.database_url, echo=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class Question(Base):
    """Question-answer pairs with vector embeddings."""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # text-embedding-3-small produces 1536 dimensions
    created_at = Column(DateTime, server_default=func.now())


class MentionTracking(Base):
    """Track processed mentions to avoid duplicates."""

    __tablename__ = "mention_tracking"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String, unique=True, nullable=False, index=True)
    processed_at = Column(DateTime, server_default=func.now())


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and pgvector extension."""
    # Create pgvector extension if not exists
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()

    # Create all tables
    Base.metadata.create_all(bind=engine)
