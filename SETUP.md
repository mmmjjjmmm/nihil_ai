# Bot X Setup Guide

This guide covers setting up the Bot X multi-platform bot backend.

## Project Structure

```
/app
  /api       # FastAPI application
  /bot       # Multi-platform bot workers
    base.py           # Abstract platform interface
    twitter_worker.py # Twitter implementation
    bluesky_worker.py # Bluesky implementation
    factory.py        # Worker factory
    runner.py         # Main bot loop
  /core      # Configuration and database
  /services  # Business logic (embeddings, responses)
/frontend    # React admin (to be implemented)
Dockerfile
requirements.txt
docker-compose.yml
```

## Prerequisites

1. Python 3.12+
2. PostgreSQL with pgvector extension
3. OpenAI API key
4. Platform credentials (at least one):
   - Twitter API credentials (API v2) for Twitter/X
   - Bluesky handle and app password for Bluesky

## Local Development Setup

### 1. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:
- Database URL
- OpenAI API key
- Platform selection (ENABLED_PLATFORMS)
- Twitter API credentials (if using Twitter)
- Bluesky credentials (if using Bluesky)

### 3. Set Up Database

#### Option A: Using Docker Compose (Recommended)
```bash
docker-compose up db -d
```

#### Option B: Local PostgreSQL
Install pgvector extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Initialize Database

The database tables will be created automatically on first run, or you can initialize manually:
```python
from app.core.database import init_db
init_db()
```

### 5. Run the Application

#### API Server
```bash
uvicorn app.api.main:app --reload --port 8000
```

API will be available at: http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

#### Bot Worker
```bash
python -m app.bot.runner
```

## Docker Deployment

Build and run all services:
```bash
docker-compose up --build
```

This starts:
- PostgreSQL with pgvector
- FastAPI API server (port 8000)
- Bot worker

## Adding Question-Answer Pairs

Use the `/qa` endpoint to add training data:

```bash
curl -X POST http://localhost:8000/qa \
  -H "Content-Type: application/json" \
  -d '{
    "q": "What is Bot X?",
    "a": "Bot X is an intelligent Twitter bot that uses vector embeddings to match questions with answers."
  }'
```

## Platform Setup

### Twitter/X

1. Create a Twitter Developer account at [developer.twitter.com](https://developer.twitter.com/)
2. Create a new app and generate API credentials
3. Enable OAuth 2.0 and get access tokens
4. Note your bot's user ID
5. Add credentials to `.env`:
   ```
   TWITTER_API_KEY=...
   TWITTER_API_SECRET=...
   TWITTER_ACCESS_TOKEN=...
   TWITTER_ACCESS_TOKEN_SECRET=...
   TWITTER_BEARER_TOKEN=...
   TWITTER_BOT_ID=...
   ```

### Bluesky

1. Create a Bluesky account at [bsky.app](https://bsky.app)
2. Go to Settings → App Passwords
3. Generate a new app password
4. Add credentials to `.env`:
   ```
   BLUESKY_HANDLE=yourbot.bsky.social
   BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```

### Platform Selection

In `.env`, set which platforms to enable:
```bash
# Enable Twitter only
ENABLED_PLATFORMS=["twitter"]

# Enable Bluesky only
ENABLED_PLATFORMS=["bluesky"]

# Enable both
ENABLED_PLATFORMS=["twitter", "bluesky"]
```

## How It Works

1. **Training**: Add question-answer pairs via `/qa` endpoint
   - Questions are converted to embeddings using OpenAI
   - Stored in PostgreSQL with pgvector

2. **Detection**: Bot worker polls enabled platforms for mentions
   - Checks every 60 seconds (configurable)
   - Tracks processed mentions per platform to avoid duplicates

3. **Matching**: For each mention:
   - Clean and normalize text
   - Generate embedding
   - Search database using cosine similarity
   - Threshold: 0.8 (configurable)

4. **Response**: If match found:
   - Reply using platform-specific worker
   - Mark as processed

## Configuration

Edit settings in `.env`:
- `SIMILARITY_THRESHOLD`: Minimum similarity score (0-1)
- `EMBEDDING_MODEL`: OpenAI embedding model
- Poll interval: Edit `poll_interval` in `app/bot/runner.py`

## API Endpoints

- `POST /qa` - Add question-answer pair
- `GET /health` - Health check

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Verify DATABASE_URL in .env
- Check pgvector extension is installed

### Platform API Issues

**Twitter:**
- Verify all credentials are correct
- Ensure bot has proper permissions
- Check rate limits

**Bluesky:**
- Verify handle format (e.g., bot.bsky.social)
- Check app password is correct
- Ensure account is not restricted

### No Responses
- Lower SIMILARITY_THRESHOLD
- Add more training data
- Check bot worker logs

## Testing with CLI Tool

Bot X includes a comprehensive CLI tool for testing all components:

```bash
# Test everything at once
botx test-all

# Test individual components
botx test-db        # Database connection
botx test-openai    # OpenAI API
botx test-twitter   # Twitter API
botx test-bluesky   # Bluesky API
botx test-platform twitter  # Test specific platform

# Add training data
botx add-qa -q "What is Bot X?" -a "An intelligent Twitter bot!"

# List all Q&A pairs
botx list-qa

# Test matching
botx test-match "What is this bot?"

# Simulate mention processing
botx simulate-mention "@bot what is your purpose?" --platform twitter
botx simulate-mention "@bot.bsky.social hello" --platform bluesky

# View configuration
botx config
```

See [CLI_GUIDE.md](CLI_GUIDE.md) for detailed documentation.

## Next Steps

- Implement frontend (issue #13-15)
- Set up CI/CD (issue #16-20)
- Deploy to cloud (GCP)
