# Bot X Setup Guide

This guide covers setting up the Bot X backend (issues #9, #10, #11, #12).

## Project Structure

```
/app
  /api       # FastAPI application
  /bot       # Twitter bot worker
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
4. Twitter API credentials (API v2)

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
- Twitter API credentials
- Bot user ID

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

## How It Works

1. **Training**: Add question-answer pairs via `/qa` endpoint
   - Questions are converted to embeddings using OpenAI
   - Stored in PostgreSQL with pgvector

2. **Detection**: Bot worker polls Twitter for mentions
   - Checks every 60 seconds (configurable)
   - Tracks processed mentions to avoid duplicates

3. **Matching**: For each mention:
   - Clean and normalize tweet text
   - Generate embedding
   - Search database using cosine similarity
   - Threshold: 0.8 (configurable)

4. **Response**: If match found:
   - Reply with matched answer
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

### Twitter API Issues
- Verify all credentials are correct
- Ensure bot has proper permissions
- Check rate limits

### No Responses
- Lower SIMILARITY_THRESHOLD
- Add more training data
- Check bot worker logs

## Next Steps

- Implement frontend (issue #13-15)
- Set up CI/CD (issue #16-20)
- Deploy to cloud (GCP)
