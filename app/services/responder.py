import re
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.embedding import get_embedding
from app.bot.worker import post_reply
from app.core.database import MentionTracking


def clean_tweet_text(tweet_text: str, bot_username: str) -> str:
    """
    Clean tweet text by removing mentions, URLs, and extra whitespace.

    Args:
        tweet_text: Raw tweet text
        bot_username: Bot's Twitter username to remove from mentions

    Returns:
        Cleaned tweet text
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
        tweet_vector: Embedding vector of the tweet

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


def process_mention(db: Session, tweet_id: str, tweet_text: str, bot_username: str) -> bool:
    """
    Process a mention by finding a matching answer and replying.

    Args:
        db: Database session
        tweet_id: ID of the tweet to process
        tweet_text: Text content of the tweet
        bot_username: Bot's Twitter username

    Returns:
        True if successfully processed and replied, False otherwise
    """
    # Check if already processed
    existing = db.query(MentionTracking).filter(
        MentionTracking.tweet_id == tweet_id
    ).first()

    if existing:
        print(f"Tweet {tweet_id} already processed, skipping")
        return False

    # Clean the tweet text
    cleaned_text = clean_tweet_text(tweet_text, bot_username)

    if not cleaned_text:
        print(f"Tweet {tweet_id} has no content after cleaning, skipping")
        return False

    # Generate embedding for the tweet
    try:
        tweet_vector = get_embedding(cleaned_text)
    except Exception as e:
        print(f"Error generating embedding for tweet {tweet_id}: {e}")
        return False

    # Find best matching answer
    match = find_best_match(db, tweet_vector)

    if match:
        answer, similarity = match
        print(f"Found match for tweet {tweet_id} with similarity {similarity:.2f}")

        # Post reply
        response = post_reply(tweet_id, answer)

        if response:
            # Mark as processed
            tracking = MentionTracking(tweet_id=tweet_id)
            db.add(tracking)
            db.commit()
            print(f"Successfully replied to tweet {tweet_id}")
            return True
        else:
            print(f"Failed to post reply to tweet {tweet_id}")
            return False
    else:
        print(f"No match found for tweet {tweet_id} above threshold {settings.similarity_threshold}")
        # Still mark as processed to avoid reprocessing
        tracking = MentionTracking(tweet_id=tweet_id)
        db.add(tracking)
        db.commit()
        return False
