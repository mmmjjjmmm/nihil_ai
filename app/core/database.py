from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, UniqueConstraint, text, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from datetime import datetime, timedelta

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
    contribution_amount_cents = Column(Integer, default=0)  # Amount paid to contribute this answer
    created_at = Column(DateTime, server_default=func.now())


class MentionTracking(Base):
    """Track processed mentions to avoid duplicates."""

    __tablename__ = "mention_tracking"
    __table_args__ = (
        UniqueConstraint('platform', 'mention_id', name='_platform_mention_uc'),
    )

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False, index=True)
    mention_id = Column(String, nullable=False, index=True)
    processed_at = Column(DateTime, server_default=func.now())


class PendingContribution(Base):
    """Track contributions from initiation through completion."""

    __tablename__ = "pending_contributions"

    id = Column(Integer, primary_key=True, index=True)

    # Mention tracking
    platform = Column(String, nullable=False)
    mention_id = Column(String, nullable=False)
    author_id = Column(String, nullable=False)

    # QA data
    question = Column(Text, nullable=False)
    suggested_answers = Column(JSONB, nullable=False)  # Array of 3 AI suggestions
    selected_answer = Column(Text)

    # Improvement tracking (when replacing existing answer)
    improvement_of_question_id = Column(Integer)  # Question ID being improved (NULL for new)
    existing_answer = Column(Text)  # Current answer being replaced (for display)
    minimum_amount_cents = Column(Integer, default=100)  # Minimum required payment

    # Payment tracking
    stripe_session_id = Column(String, unique=True)
    stripe_payment_intent = Column(String)
    payment_status = Column(String, default='pending')  # pending, paid, failed
    amount_cents = Column(Integer)  # User-chosen amount

    # State
    status = Column(String, default='awaiting_payment')
    # Status flow: awaiting_payment → payment_received → qa_stored → complete

    # Token for secure checkout URL
    token = Column(String, unique=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    paid_at = Column(DateTime)
    completed_at = Column(DateTime)


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
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Migrate existing mention_tracking table if needed
    _migrate_mention_tracking()

    # Create all tables
    Base.metadata.create_all(bind=engine)


def _migrate_mention_tracking():
    """Migrate existing mention_tracking table to new schema."""
    with engine.connect() as conn:
        # Check if table exists and needs migration
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'mention_tracking'
            AND column_name = 'tweet_id'
        """))

        if result.fetchone():
            print("Migrating mention_tracking table...")

            # Add platform column with default value
            conn.execute(text("""
                ALTER TABLE mention_tracking
                ADD COLUMN IF NOT EXISTS platform VARCHAR DEFAULT 'twitter'
            """))

            # Rename tweet_id to mention_id
            conn.execute(text("""
                ALTER TABLE mention_tracking
                RENAME COLUMN tweet_id TO mention_id
            """))

            # Drop old unique constraint if exists
            conn.execute(text("""
                ALTER TABLE mention_tracking
                DROP CONSTRAINT IF EXISTS mention_tracking_tweet_id_key
            """))

            # Add new composite unique constraint
            conn.execute(text("""
                ALTER TABLE mention_tracking
                ADD CONSTRAINT _platform_mention_uc UNIQUE (platform, mention_id)
            """))

            # Update platform column to be not nullable
            conn.execute(text("""
                ALTER TABLE mention_tracking
                ALTER COLUMN platform SET NOT NULL
            """))

            conn.commit()
            print("Migration completed successfully.")
