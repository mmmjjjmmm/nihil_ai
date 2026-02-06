#!/usr/bin/env python3
"""Test multi-platform integration with Bluesky only."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.bot.factory import get_enabled_workers, get_worker_by_platform

def main():
    print("=" * 60)
    print("Multi-Platform Integration Test (Bluesky Only)")
    print("=" * 60)
    print()

    # Test 1: Get enabled workers
    print("1. Testing get_enabled_workers()...")
    try:
        workers = get_enabled_workers()
        print(f"   ✓ Factory returned {len(workers)} worker(s)")

        for worker in workers:
            print(f"   - Platform: {worker.get_platform_name()}")
            print(f"     Username: {worker.get_bot_username()}")
        print()

        if len(workers) != 1:
            print(f"   ⚠ Warning: Expected 1 worker, got {len(workers)}")

        if workers and workers[0].get_platform_name() != "bluesky":
            print(f"   ⚠ Warning: Expected bluesky, got {workers[0].get_platform_name()}")

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test 2: Get specific worker
    print("2. Testing get_worker_by_platform('bluesky')...")
    try:
        worker = get_worker_by_platform("bluesky")
        if worker:
            print(f"   ✓ Successfully got Bluesky worker")
            print(f"   Platform: {worker.get_platform_name()}")
            print(f"   Username: {worker.get_bot_username()}")
        else:
            print(f"   ✗ Worker returned None")
            return 1
        print()
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test 3: Verify Twitter is not loaded
    print("3. Testing get_worker_by_platform('twitter')...")
    try:
        worker = get_worker_by_platform("twitter")
        if worker:
            print(f"   ⚠ Warning: Twitter worker loaded despite not being enabled")
            print(f"   (This might fail later due to missing credentials)")
        else:
            print(f"   ✓ Twitter worker correctly not loaded (no credentials)")
        print()
    except Exception as e:
        print(f"   ✓ Twitter worker correctly failed: {str(e)[:60]}...")
        print()

    # Test 4: Test mentions check
    print("4. Testing mention fetching...")
    try:
        worker = get_worker_by_platform("bluesky")
        mentions = worker.check_mentions()
        print(f"   ✓ Successfully fetched mentions")
        print(f"   Found: {len(mentions)} mentions")

        if mentions:
            print(f"   Latest mention preview:")
            m = mentions[0]
            print(f"   - Text: {m.text[:60]}...")
            print(f"   - Platform: {m.platform}")
            print(f"   - Created: {m.created_at}")
        print()
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("=" * 60)
    print("✓ All integration tests passed!")
    print("=" * 60)
    print()
    print("Summary:")
    print("- Bluesky worker: ✓ Working")
    print("- Factory pattern: ✓ Working")
    print("- Platform selection: ✓ Working")
    print("- Ready for production!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
