"""Bluesky platform worker implementation."""

from typing import List
from datetime import datetime, timezone

try:
    from atproto import Client, models
except ImportError:
    Client = None
    models = None

from app.core.config import settings
from app.bot.base import BasePlatformWorker, Mention


class BlueskyWorker(BasePlatformWorker):
    """Bluesky/AT Protocol platform worker implementation."""

    def __init__(self):
        """Initialize Bluesky API client."""
        if Client is None:
            raise ImportError(
                "atproto package is required for Bluesky support. "
                "Install it with: pip install atproto"
            )

        self.client = Client()
        self.handle = settings.bluesky_handle
        self.app_password = settings.bluesky_app_password
        self.service_url = settings.bluesky_service_url

        # Authenticate
        try:
            self.client.login(self.handle, self.app_password)
        except Exception as e:
            raise RuntimeError(f"Failed to authenticate with Bluesky: {e}")

    def check_mentions(self, since_id: str | None = None) -> List[Mention]:
        """
        Fetch Bluesky notifications mentioning the bot.

        Note: Duplicate filtering is handled by process_mention via database check,
        so we return all mention notifications and let the database be the source of truth.

        Args:
            since_id: Not used for Bluesky (kept for interface compatibility)

        Returns:
            List of Mention objects
        """
        try:
            # Fetch notifications
            notifications = self.client.app.bsky.notification.list_notifications()

            if not notifications.notifications:
                return []

            mentions = []
            for notif in notifications.notifications:
                # Only process mention notifications
                if notif.reason != "mention":
                    continue

                # Extract post information
                if not hasattr(notif, 'record') or not notif.record:
                    continue

                mention = Mention(
                    id=notif.uri,  # Use URI as unique identifier
                    text=notif.record.text if hasattr(notif.record, 'text') else "",
                    author_id=notif.author.did,
                    created_at=self._parse_timestamp(notif.indexed_at),
                    platform="bluesky"
                )
                mentions.append(mention)

            return mentions

        except Exception as e:
            print(f"Error fetching Bluesky mentions: {e}")
            return []

    def post_reply(self, mention_id: str, text: str) -> bool:
        """
        Post a reply to a specific Bluesky post.

        Args:
            mention_id: URI of the post to reply to
            text: Reply text

        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse the mention URI to get repo and rkey
            # Format: at://did:plc:xxx/app.bsky.feed.post/yyy
            parts = mention_id.replace("at://", "").split("/")
            if len(parts) < 3:
                print(f"Invalid mention URI format: {mention_id}")
                return False

            repo_did = parts[0]
            rkey = parts[2]

            # Get the original post to set up reply references
            try:
                original_post = self.client.get_posts(uris=[mention_id])
                if not original_post.posts:
                    print(f"Could not find original post: {mention_id}")
                    return False

                post = original_post.posts[0]
            except Exception as e:
                print(f"Error fetching original post: {e}")
                return False

            # Create reply with proper references
            reply_ref = models.AppBskyFeedPost.ReplyRef(
                parent=models.ComAtprotoRepoStrongRef.Main(
                    uri=mention_id,
                    cid=post.cid
                ),
                root=models.ComAtprotoRepoStrongRef.Main(
                    uri=post.record.reply.root.uri if hasattr(post.record, 'reply') and post.record.reply else mention_id,
                    cid=post.record.reply.root.cid if hasattr(post.record, 'reply') and post.record.reply else post.cid
                )
            )

            # Send the reply using the simpler send_post method
            self.client.send_post(text=text, reply_to=reply_ref)

            return True

        except Exception as e:
            print(f"Error posting Bluesky reply: {e}")
            return False

    def get_bot_username(self) -> str:
        """
        Get the bot's Bluesky handle.

        Returns:
            Bot handle
        """
        return self.handle

    def get_platform_name(self) -> str:
        """
        Get the platform name identifier.

        Returns:
            Platform name "bluesky"
        """
        return "bluesky"

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO timestamp string to datetime object.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            datetime object
        """
        try:
            # Handle various ISO formats
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            return datetime.fromisoformat(timestamp_str)
        except Exception:
            # Fallback to current time if parsing fails
            return datetime.now(timezone.utc)
