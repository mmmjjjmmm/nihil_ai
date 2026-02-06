"""
Backward compatibility wrapper for Twitter worker.

This module maintains backward compatibility for any external imports.
For new code, use TwitterWorker directly from app.bot.twitter_worker.
"""

import tweepy
from typing import List

from app.bot.twitter_worker import TwitterWorker

# Initialize default Twitter worker instance
_twitter_worker = TwitterWorker()


def check_mentions(since_id: str | None = None) -> List[tweepy.Tweet]:
    """
    Fetch tweets mentioning the bot since the last check.

    DEPRECATED: Use TwitterWorker.check_mentions() directly.

    Args:
        since_id: ID of the last processed tweet. Only tweets after this ID will be fetched.

    Returns:
        List of tweets mentioning the bot
    """
    # Convert Mention objects back to tweepy.Tweet for compatibility
    mentions = _twitter_worker.check_mentions(since_id)

    # For backward compatibility, we need to return tweepy.Tweet objects
    # This is a simplified approach - in practice, the calling code should be updated
    # to use the new Mention dataclass
    tweet_objects = []
    for mention in mentions:
        # Create a mock tweepy.Tweet-like object
        # Note: This is a simplified version for compatibility
        class MockTweet:
            def __init__(self, mention):
                self.id = mention.id
                self.text = mention.text
                self.author_id = mention.author_id
                self.created_at = mention.created_at

        tweet_objects.append(MockTweet(mention))

    return tweet_objects


def post_reply(tweet_id: str, text: str) -> bool:
    """
    Post a reply to a specific tweet.

    DEPRECATED: Use TwitterWorker.post_reply() directly.

    Args:
        tweet_id: ID of the tweet to reply to
        text: Reply text

    Returns:
        True if successful, False otherwise
    """
    return _twitter_worker.post_reply(tweet_id, text)
