
# Bot X - Multi-Platform Social Media Bot

Bot X is an intelligent social media bot that uses vector embeddings and semantic search to automatically respond to mentions across multiple platforms. It leverages OpenAI's embeddings to match user questions with pre-configured answers.

## Features

- **Multi-Platform Support**: Works with Twitter/X and Bluesky
- **Semantic Matching**: Uses vector embeddings for intelligent question matching
- **Configurable**: Easy platform selection and threshold tuning
- **Scalable**: PostgreSQL with pgvector for efficient similarity search
- **REST API**: Add Q&A pairs programmatically
- **CLI Tool**: Comprehensive testing and management commands

## Supported Platforms

- **Twitter/X**: Monitors mentions and replies automatically
- **Bluesky**: AT Protocol integration for decentralized social networking
- Configure which platforms to enable in `.env`

## Quick Start

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Initialize database:
```bash
botx init-db
```

4. Add training data:
```bash
botx add-qa -q "What is Bot X?" -a "An intelligent multi-platform bot!"
```

5. Run the bot:
```bash
python -m app.bot.runner
```

## Documentation

- [Setup Guide](SETUP.md) - Detailed installation and configuration
- [CLI Guide](CLI_GUIDE.md) - CLI commands and testing

## Platform Setup

### Twitter/X
Get API credentials from [Twitter Developer Portal](https://developer.twitter.com/)

### Bluesky
1. Create account at [bsky.app](https://bsky.app)
2. Generate app password at Settings → App Passwords
3. Configure `BLUESKY_HANDLE` and `BLUESKY_APP_PASSWORD` in `.env`

## Testing

```bash
# Test all platforms
botx test-all

# Test specific platform
botx test-twitter
botx test-bluesky

# Simulate mention
botx simulate-mention "Hey @bot, what are you?" --platform twitter
```

## Architecture

- **FastAPI**: REST API for Q&A management
- **PostgreSQL + pgvector**: Vector similarity search
- **OpenAI**: Embedding generation
- **Multi-platform workers**: Abstract platform interface for easy extensibility

---

## Development Setup (WSL)

step 1: install wsl
```powershell
wsl --install
```

step 2: install nvm and node.js on wsl
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
```

step 3: install claude code
```bash
npm install -g @anthropic-ai/claude-code
```

step 4: configure github
```bash
sudo mkdir -p -m 755 /etc/apt/keyrings && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
apt update
apt install gh -y
gh auth login
```
