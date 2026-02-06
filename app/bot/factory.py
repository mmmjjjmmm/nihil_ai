"""Factory for creating platform workers based on configuration."""

from typing import List

from app.core.config import settings
from app.bot.base import BasePlatformWorker
from app.bot.twitter_worker import TwitterWorker


def get_enabled_workers() -> List[BasePlatformWorker]:
    """
    Get list of enabled platform workers based on configuration.

    Returns:
        List of initialized platform workers
    """
    workers = []
    enabled_platforms = settings.get_enabled_platforms

    for platform in enabled_platforms:
        worker = get_worker_by_platform(platform)
        if worker:
            workers.append(worker)

    return workers


def get_worker_by_platform(platform: str) -> BasePlatformWorker | None:
    """
    Get a specific platform worker by name.

    Args:
        platform: Platform name ("twitter", "bluesky", etc.)

    Returns:
        Initialized platform worker or None if platform not supported
    """
    platform = platform.lower()

    if platform == "twitter":
        return TwitterWorker()
    elif platform == "bluesky":
        # Import here to avoid dependency issues if atproto not installed
        try:
            from app.bot.bluesky_worker import BlueskyWorker
            return BlueskyWorker()
        except ImportError as e:
            print(f"Error importing BlueskyWorker: {e}")
            print("Install atproto package to enable Bluesky support")
            return None
    else:
        print(f"Unknown platform: {platform}")
        return None
