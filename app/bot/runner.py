import time
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, MentionTracking
from app.bot.factory import get_enabled_workers
from app.services.responder import process_mention


def get_last_processed_id(db: Session, platform: str) -> str | None:
    """
    Get the ID of the last processed mention for a specific platform.

    Args:
        db: Database session
        platform: Platform name (e.g., "twitter", "bluesky")

    Returns:
        Last processed mention ID or None
    """
    last_mention = db.query(MentionTracking).filter(
        MentionTracking.platform == platform
    ).order_by(
        MentionTracking.processed_at.desc()
    ).first()

    return last_mention.mention_id if last_mention else None


def run_bot(poll_interval: int = 60):
    """
    Run the bot worker in a continuous loop for all enabled platforms.

    Args:
        poll_interval: Time in seconds to wait between checking for new mentions
    """
    print("Starting multi-platform bot worker...")

    # Get enabled platform workers
    workers = get_enabled_workers()

    if not workers:
        print("No platform workers enabled. Check your ENABLED_PLATFORMS configuration.")
        return

    print(f"Enabled platforms: {[w.get_platform_name() for w in workers]}")

    while True:
        try:
            db = SessionLocal()

            # Process each platform
            for worker in workers:
                try:
                    platform = worker.get_platform_name()
                    bot_username = worker.get_bot_username()

                    # Get last processed mention ID for this platform
                    since_id = get_last_processed_id(db, platform)
                    print(f"[{platform}] Checking mentions since ID: {since_id}")

                    # Fetch new mentions
                    mentions = worker.check_mentions(since_id)
                    print(f"[{platform}] Found {len(mentions)} new mentions")

                    # Process each mention
                    for mention in mentions:
                        try:
                            process_mention(
                                db=db,
                                mention=mention,
                                worker=worker,
                                bot_username=bot_username
                            )
                        except Exception as e:
                            print(f"[{platform}] Error processing mention {mention.id}: {e}")

                except Exception as e:
                    print(f"Error processing platform {worker.get_platform_name()}: {e}")

            db.close()

        except Exception as e:
            print(f"Error in bot loop: {e}")

        # Wait before next check
        print(f"Waiting {poll_interval} seconds before next check...")
        time.sleep(poll_interval)


if __name__ == "__main__":
    run_bot()
