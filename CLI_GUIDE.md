# Bot X CLI Testing Guide

The Bot X CLI tool provides commands to test and verify that all bot components are working correctly across multiple platforms.

## Installation

After installing dependencies:
```bash
uv sync
```

The `botx` command will be available in your environment.

## Available Commands

### 1. Test All Components

Run all tests at once:
```bash
botx test-all
```

This will test:
- Database connection and pgvector extension
- OpenAI API connection
- All enabled platform APIs (Twitter, Bluesky, etc.)

### 2. Test Database

Check database connection and verify pgvector extension:
```bash
botx test-db
```

### 3. Initialize Database

Create database tables:
```bash
botx init-db
```

### 4. Test OpenAI API

Verify OpenAI API connection and embedding generation:
```bash
botx test-openai
```

### 5. Test Twitter API

Verify Twitter API credentials and connection:
```bash
botx test-twitter
```

### 6. Test Bluesky API

Verify Bluesky API credentials and connection:
```bash
botx test-bluesky
```

### 7. Test Any Platform

Test a specific platform by name:
```bash
botx test-platform twitter
botx test-platform bluesky
```

### 8. Add Question-Answer Pair

Add training data to the bot:
```bash
botx add-qa -q "What is Bot X?" -a "Bot X is an intelligent Twitter bot!"
```

Options:
- `-q, --question`: The question text
- `-a, --answer`: The answer text

### 9. List All Q&A Pairs

View all question-answer pairs in the database:
```bash
botx list-qa
```

### 10. Test Similarity Matching

Test how the bot would match a given text:
```bash
botx test-match "What is this bot?"
```

This shows:
- The generated embedding
- Best matching answer and similarity score
- Whether it meets the threshold

### 11. Simulate Mention Processing

Simulate the full process of handling a mention from any platform:
```bash
# Twitter mention
botx simulate-mention "Hey @bot, what is Bot X?" --platform twitter --mention-id test_001

# Bluesky mention
botx simulate-mention "Hello @bot.bsky.social" --platform bluesky --mention-id test_002

# Default is Twitter
botx simulate-mention "Hey @bot, help!" --mention-id test_003
```

This shows:
- Text cleaning process
- Embedding generation
- Similarity matching
- Whether the bot would reply

Options:
- `--platform, -p`: Platform to simulate (twitter, bluesky). Default: twitter
- `--mention-id`: ID for testing. Default: test_123

### 12. View Configuration

Display current bot configuration:
```bash
botx config
```

Shows:
- Database URL (credentials masked)
- OpenAI API key (partially masked)
- Enabled platforms
- Twitter bot ID
- Bluesky handle
- Embedding model
- Similarity threshold

## Example Workflow

### 1. Initial Setup Test
```bash
# Run all tests
botx test-all

# Initialize database if needed
botx init-db
```

### 2. Add Training Data
```bash
botx add-qa -q "What is your purpose?" -a "I help answer questions about Bot X!"
botx add-qa -q "How do you work?" -a "I use vector embeddings to match questions with answers."
botx add-qa -q "Who created you?" -a "I was created using OpenAI and Twitter APIs."
```

### 3. View Data
```bash
botx list-qa
```

### 4. Test Matching
```bash
# Test with similar questions
botx test-match "What's your purpose?"
botx test-match "How does this bot work?"
botx test-match "Who made you?"
```

### 5. Simulate Full Process
```bash
# Test Twitter
botx simulate-mention "@bot what is your purpose?" --platform twitter

# Test Bluesky
botx simulate-mention "@bot.bsky.social what is your purpose?" --platform bluesky
```

## Troubleshooting

### Database Connection Failed
- Check DATABASE_URL in .env
- Ensure PostgreSQL is running
- Verify credentials are correct

### OpenAI API Failed
- Check OPENAI_API_KEY in .env
- Verify API key is valid and has credits
- Check internet connection

### Twitter API Failed
- Check all Twitter credentials in .env
- Verify TWITTER_BOT_ID is correct
- Ensure API access level is appropriate

### Bluesky API Failed
- Check BLUESKY_HANDLE format (should be like: bot.bsky.social)
- Verify BLUESKY_APP_PASSWORD is correct
- Ensure you generated an app password (not your main password)
- Check BLUESKY_SERVICE_URL (default: https://bsky.social)

### No Matches Found
- Add more training data with `botx add-qa`
- Lower SIMILARITY_THRESHOLD in .env
- Check if questions are semantically similar

## Tips

1. **Test before deploying**: Always run `botx test-all` before deploying
2. **Add diverse training data**: Include variations of questions
3. **Monitor similarity scores**: Use `botx test-match` to tune threshold
4. **Check configuration**: Use `botx config` to verify settings
5. **Test each platform**: Use platform-specific tests to isolate issues
6. **Simulate mentions**: Test with realistic mention text for each platform

## Integration with CI/CD

Add to your CI pipeline:
```bash
# In your CI script
botx test-db
botx test-openai

# Test enabled platforms
if [[ "$ENABLED_PLATFORMS" == *"twitter"* ]]; then
  botx test-twitter
fi

if [[ "$ENABLED_PLATFORMS" == *"bluesky"* ]]; then
  botx test-bluesky
fi

# Or simply
botx test-all
```

This ensures all components are working before deployment.

## Multi-Platform Testing

### Testing Both Platforms Simultaneously

```bash
# Set in .env
ENABLED_PLATFORMS=["twitter", "bluesky"]

# Test all at once
botx test-all

# Add Q&A (shared across platforms)
botx add-qa -q "What platforms do you support?" -a "I support Twitter and Bluesky!"

# Test matching on both
botx simulate-mention "What platforms?" --platform twitter
botx simulate-mention "What platforms?" --platform bluesky
```

### Platform-Specific Testing

```bash
# Enable only one platform
ENABLED_PLATFORMS=["twitter"]
botx test-all

# Switch to other platform
ENABLED_PLATFORMS=["bluesky"]
botx test-all
```
