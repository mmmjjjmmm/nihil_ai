"""
Bot X - Twitter Bot with Vector-based Response System

Usage:
    - Run API server: uvicorn app.api.main:app --reload
    - Run bot worker: python -m app.bot.runner
    - With Docker: docker-compose up
"""

if __name__ == "__main__":
    print("Bot X - Twitter Bot with Vector-based Response System")
    print("\nAvailable commands:")
    print("  - Run API: uvicorn app.api.main:app --reload")
    print("  - Run Bot: python -m app.bot.runner")
    print("  - Docker: docker-compose up")
