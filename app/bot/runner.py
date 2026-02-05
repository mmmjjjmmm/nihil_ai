import time
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, MentionTracking
from app.bot.worker import check_mentions
from app.services.responder import process_mention


def get_last_processed_id(db: Session) -> str | None:
    """Get the ID of the last processed tweet."""
    last_mention = db.query(MentionTracking).order_by(
        MentionTracking.processed_at.desc()
    ).first()

    return last_mention.tweet_id if last_mention else None


def run_bot(poll_interval: int = 60):
    """
    Run the bot worker in a continuous loop.

    Args:
        poll_interval: Time in seconds to wait between checking for new mentions
    """
    print("Starting bot worker...")

    while True:
        try:
            db = SessionLocal()

            # Get last processed tweet ID
            since_id = get_last_processed_id(db)
            print(f"Checking mentions since ID: {since_id}")

            # Fetch new mentions
            mentions = check_mentions(since_id)
            print(f"Found {len(mentions)} new mentions")

            # Process each mention
            for mention in mentions:
                try:
                    process_mention(
                        db=db,
                        tweet_id=mention.id,
                        tweet_text=mention.text,
                        bot_username="bot"  # Replace with actual bot username
                    )
                except Exception as e:
                    print(f"Error processing mention {mention.id}: {e}")

            db.close()

        except Exception as e:
            print(f"Error in bot loop: {e}")

        # Wait before next check
        print(f"Waiting {poll_interval} seconds before next check...")
        time.sleep(poll_interval)


if __name__ == "__main__":
    run_bot()
