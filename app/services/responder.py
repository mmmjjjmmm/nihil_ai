import re
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.embedding import get_embedding
from app.bot.base import BasePlatformWorker, Mention
from app.core.database import MentionTracking


def clean_tweet_text(tweet_text: str, bot_username: str) -> str:
    """
    Clean mention text by removing mentions, URLs, and extra whitespace.

    Args:
        tweet_text: Raw mention text
        bot_username: Bot's username to remove from mentions

    Returns:
        Cleaned text
    """
    # Remove URLs
    text = re.sub(r'http\S+|www.\S+', '', tweet_text)

    # Remove @mentions
    text = re.sub(r'@\w+', '', text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text.strip()


def find_best_match(db: Session, tweet_vector: list[float]) -> tuple[str, float] | None:
    """
    Find the best matching answer using vector similarity search.

    Args:
        db: Database session
        tweet_vector: Embedding vector of the mention

    Returns:
        Tuple of (answer, similarity_score) if match found above threshold, None otherwise
    """
    # SQL query to find most similar question using pgvector
    query = text("""
        SELECT answer, 1 - (embedding <=> :tweet_vector) as similarity
        FROM questions
        WHERE 1 - (embedding <=> :tweet_vector) > :threshold
        ORDER BY similarity DESC
        LIMIT 1;
    """)

    result = db.execute(
        query,
        {
            "tweet_vector": str(tweet_vector),
            "threshold": settings.similarity_threshold
        }
    ).fetchone()

    if result:
        return result[0], result[1]

    return None


def process_mention(db: Session, mention: Mention, worker: BasePlatformWorker, bot_username: str) -> bool:
    """
    Process a mention by finding a matching answer and replying.

    Args:
        db: Database session
        mention: Mention object to process
        worker: Platform worker to use for posting reply
        bot_username: Bot's username on the platform

    Returns:
        True if successfully processed and replied, False otherwise
    """
    # Check if already processed
    existing = db.query(MentionTracking).filter(
        MentionTracking.platform == mention.platform,
        MentionTracking.mention_id == mention.id
    ).first()

    if existing:
        print(f"{mention.platform} mention {mention.id} already processed, skipping")
        return False

    # Clean the mention text
    cleaned_text = clean_tweet_text(mention.text, bot_username)

    if not cleaned_text:
        print(f"{mention.platform} mention {mention.id} has no content after cleaning, skipping")
        return False

    # Generate embedding for the mention
    try:
        mention_vector = get_embedding(cleaned_text)
    except Exception as e:
        print(f"Error generating embedding for {mention.platform} mention {mention.id}: {e}")
        return False

    # Find best matching answer
    match = find_best_match(db, mention_vector)

    if match:
        answer, similarity = match
        print(f"Found match for {mention.platform} mention {mention.id} with similarity {similarity:.2f}")

        # Post reply using the worker
        success = worker.post_reply(mention.id, answer)

        if success:
            # Mark as processed
            tracking = MentionTracking(
                platform=mention.platform,
                mention_id=mention.id
            )
            db.add(tracking)
            db.commit()
            print(f"Successfully replied to {mention.platform} mention {mention.id}")
            return True
        else:
            print(f"Failed to post reply to {mention.platform} mention {mention.id}")
            return False
    else:
        print(f"No match found for {mention.platform} mention {mention.id} above threshold {settings.similarity_threshold}")
        # Still mark as processed to avoid reprocessing
        tracking = MentionTracking(
            platform=mention.platform,
            mention_id=mention.id
        )
        db.add(tracking)
        db.commit()
        return False
