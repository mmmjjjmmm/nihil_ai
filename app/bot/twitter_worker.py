"""Twitter platform worker implementation."""

import tweepy
from typing import List

from app.core.config import settings
from app.bot.base import BasePlatformWorker, Mention


class TwitterWorker(BasePlatformWorker):
    """Twitter/X platform worker implementation."""

    def __init__(self):
        """Initialize Twitter API client."""
        self.client = tweepy.Client(
            bearer_token=settings.twitter_bearer_token,
            consumer_key=settings.twitter_api_key,
            consumer_secret=settings.twitter_api_secret,
            access_token=settings.twitter_access_token,
            access_token_secret=settings.twitter_access_token_secret,
            wait_on_rate_limit=True
        )
        self.bot_id = settings.twitter_bot_id

    def check_mentions(self, since_id: str | None = None) -> List[Mention]:
        """
        Fetch tweets mentioning the bot since the last check.

        Args:
            since_id: ID of the last processed tweet. Only tweets after this ID will be fetched.

        Returns:
            List of Mention objects
        """
        try:
            # Fetch mentions of the bot
            response = self.client.get_users_mentions(
                id=self.bot_id,
                since_id=since_id,
                tweet_fields=["created_at", "author_id", "text", "conversation_id"],
                expansions=["author_id"],
                max_results=100
            )

            if response.data is None:
                return []

            # Convert tweepy.Tweet objects to Mention dataclasses
            mentions = []
            for tweet in response.data:
                mention = Mention(
                    id=tweet.id,
                    text=tweet.text,
                    author_id=tweet.author_id,
                    created_at=tweet.created_at,
                    platform="twitter"
                )
                mentions.append(mention)

            return mentions

        except tweepy.TweepyException as e:
            print(f"Error fetching Twitter mentions: {e}")
            return []

    def post_reply(self, mention_id: str, text: str) -> bool:
        """
        Post a reply to a specific tweet.

        Args:
            mention_id: ID of the tweet to reply to
            text: Reply text

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.create_tweet(
                text=text,
                in_reply_to_tweet_id=mention_id
            )
            return True

        except tweepy.TweepyException as e:
            print(f"Error posting Twitter reply: {e}")
            return False

    def get_bot_username(self) -> str:
        """
        Get the bot's Twitter username.

        Returns:
            Bot username
        """
        # Try to fetch from API, fallback to "bot"
        try:
            user = self.client.get_user(id=self.bot_id)
            if user.data:
                return user.data.username
        except tweepy.TweepyException:
            pass
        return "bot"

    def get_platform_name(self) -> str:
        """
        Get the platform name identifier.

        Returns:
            Platform name "twitter"
        """
        return "twitter"
