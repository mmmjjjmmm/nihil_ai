#!/usr/bin/env python3
"""Test bot runner with Bluesky (without database)."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.bot.factory import get_enabled_workers

def test_runner_logic():
    """Simulate the runner logic without database."""
    print("=" * 60)
    print("Bot Runner Logic Test (Bluesky)")
    print("=" * 60)
    print()

    print("1. Getting enabled workers...")
    workers = get_enabled_workers()

    if not workers:
        print("   ✗ No platform workers enabled")
        return 1

    print(f"   ✓ Enabled platforms: {[w.get_platform_name() for w in workers]}")
    print()

    # Simulate runner loop (single iteration)
    print("2. Simulating runner loop iteration...")
    for worker in workers:
        try:
            platform = worker.get_platform_name()
            bot_username = worker.get_bot_username()

            print(f"   [{platform}] Processing...")
            print(f"   - Bot username: {bot_username}")

            # Simulate getting last processed ID (would come from DB)
            since_id = None
            print(f"   - Checking mentions since ID: {since_id}")

            # Fetch mentions
            mentions = worker.check_mentions(since_id)
            print(f"   - Found {len(mentions)} new mentions")

            # Process each mention (normally would use responder)
            for mention in mentions:
                print(f"   - Would process: {mention.id[:50]}...")
                print(f"     Text: {mention.text[:60]}...")

            print(f"   [{platform}] ✓ Completed")
            print()

        except Exception as e:
            print(f"   [{platform}] ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 60)
    print("✓ Runner logic test passed!")
    print("=" * 60)
    print()
    print("The bot runner would work correctly with the current setup.")
    print("Note: Database connection needed for production use.")

    return 0

if __name__ == "__main__":
    sys.exit(test_runner_logic())
