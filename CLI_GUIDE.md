# Bot X CLI Testing Guide

The Bot X CLI tool provides commands to test and verify that all bot components are working correctly.

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
- Twitter API connection

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

### 6. Add Question-Answer Pair

Add training data to the bot:
```bash
botx add-qa -q "What is Bot X?" -a "Bot X is an intelligent Twitter bot!"
```

Options:
- `-q, --question`: The question text
- `-a, --answer`: The answer text

### 7. List All Q&A Pairs

View all question-answer pairs in the database:
```bash
botx list-qa
```

### 8. Test Similarity Matching

Test how the bot would match a given text:
```bash
botx test-match "What is this bot?"
```

This shows:
- The generated embedding
- Best matching answer and similarity score
- Whether it meets the threshold

### 9. Simulate Mention Processing

Simulate the full process of handling a tweet mention:
```bash
botx simulate-mention "Hey @bot, what is Bot X?" --tweet-id test_001
```

This shows:
- Text cleaning process
- Embedding generation
- Similarity matching
- Whether the bot would reply

### 10. View Configuration

Display current bot configuration:
```bash
botx config
```

Shows:
- Database URL (credentials masked)
- OpenAI API key (partially masked)
- Twitter bot ID
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
botx simulate-mention "@bot what is your purpose?"
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

### No Matches Found
- Add more training data with `botx add-qa`
- Lower SIMILARITY_THRESHOLD in .env
- Check if questions are semantically similar

## Tips

1. **Test before deploying**: Always run `botx test-all` before deploying
2. **Add diverse training data**: Include variations of questions
3. **Monitor similarity scores**: Use `botx test-match` to tune threshold
4. **Check configuration**: Use `botx config` to verify settings

## Integration with CI/CD

Add to your CI pipeline:
```bash
# In your CI script
botx test-db
botx test-openai
botx test-twitter
```

This ensures all components are working before deployment.
