"""Base platform worker interface for multi-platform bot support."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Mention:
    """Platform-agnostic representation of a mention."""

    id: str
    text: str
    author_id: str
    created_at: datetime
    platform: str


class BasePlatformWorker(ABC):
    """Abstract base class defining the interface for all platform workers."""

    @abstractmethod
    def check_mentions(self, since_id: str | None = None) -> List[Mention]:
        """
        Fetch mentions since the last check.

        Args:
            since_id: ID of the last processed mention. Only mentions after this ID will be fetched.

        Returns:
            List of Mention objects
        """
        pass

    @abstractmethod
    def post_reply(self, mention_id: str, text: str) -> bool:
        """
        Post a reply to a specific mention.

        Args:
            mention_id: ID of the mention to reply to
            text: Reply text

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_bot_username(self) -> str:
        """
        Get the bot's username on this platform.

        Returns:
            Bot username
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name identifier.

        Returns:
            Platform name (e.g., "twitter", "bluesky")
        """
        pass
