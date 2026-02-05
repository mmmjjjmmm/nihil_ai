import tweepy
from typing import List

from app.core.config import settings

# Initialize Twitter API client
client = tweepy.Client(
    bearer_token=settings.twitter_bearer_token,
    consumer_key=settings.twitter_api_key,
    consumer_secret=settings.twitter_api_secret,
    access_token=settings.twitter_access_token,
    access_token_secret=settings.twitter_access_token_secret,
    wait_on_rate_limit=True
)


def check_mentions(since_id: str | None = None) -> List[tweepy.Tweet]:
    """
    Fetch tweets mentioning the bot since the last check.

    Args:
        since_id: ID of the last processed tweet. Only tweets after this ID will be fetched.

    Returns:
        List of tweets mentioning the bot
    """
    try:
        # Fetch mentions of the bot
        mentions = client.get_users_mentions(
            id=settings.twitter_bot_id,
            since_id=since_id,
            tweet_fields=["created_at", "author_id", "text", "conversation_id"],
            expansions=["author_id"],
            max_results=100
        )

        if mentions.data is None:
            return []

        return mentions.data

    except tweepy.TweepyException as e:
        print(f"Error fetching mentions: {e}")
        return []


def post_reply(tweet_id: str, text: str) -> tweepy.Response | None:
    """
    Post a reply to a specific tweet.

    Args:
        tweet_id: ID of the tweet to reply to
        text: Reply text

    Returns:
        Response from Twitter API or None if failed
    """
    try:
        response = client.create_tweet(
            text=text,
            in_reply_to_tweet_id=tweet_id
        )
        return response

    except tweepy.TweepyException as e:
        print(f"Error posting reply: {e}")
        return None
