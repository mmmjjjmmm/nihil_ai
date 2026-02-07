
# Bot X - Multi-Platform Social Media Bot

Bot X is an intelligent social media bot that uses vector embeddings and semantic search to automatically respond to mentions across multiple platforms. It leverages OpenAI's embeddings to match user questions with pre-configured answers.

## Features

- **Multi-Platform Support**: Works with Twitter/X and Bluesky
- **Semantic Matching**: Uses vector embeddings for intelligent question matching
- **Payment-Enabled Learning**: Users can teach the bot new answers via Stripe payments
- **AI-Powered Suggestions**: ChatGPT generates answer options for contributions
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
or
```bash
uv run -m app.cli init-db
```
I need to run this in another terminal to "simulate the db locally"
```bash
./cloud-sql-proxy nihilai:europe-west9:nihil-korg-ai
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

## Contribution Flow (New!)

The bot **always** offers users the chance to contribute, whether or not an answer exists:

### When Answer Exists (Improvement)
1. **Bot replies** with current answer + "💡 Not satisfied? Teach me a better answer: [link]"
2. **User pays MORE** than previous contributor (e.g., if current answer cost $5, must pay $6+)
3. **Answer replaced** with the better one

### When No Answer Exists (New)
1. **Bot replies** "I don't know this yet! Help me learn: [link]"
2. **User pays minimum** $1+ to contribute new answer
3. **Answer added** to knowledge base

### Contribution Process
1. **AI Generates Suggestions**: ChatGPT creates 3 diverse answer options
2. **User Selects/Writes**: Choose suggestion or write custom answer
3. **Payment Processing**: Stripe handles secure payment (user-chosen amount)
4. **QA Stored**: Answer is embedded and added to bot's knowledge base
5. **Confirmation**: Bot replies thanking the contributor

This creates a **competitive improvement system** where answers get progressively better through higher contributions.

### Setting Up Contributions

1. **Get Stripe API Keys**:
   - Sign up at [stripe.com](https://stripe.com)
   - Get test keys from Dashboard → Developers → API keys
   - Add to `.env`: `STRIPE_API_KEY` and `STRIPE_WEBHOOK_SECRET`

2. **Configure Webhook**:
   - In Stripe Dashboard → Developers → Webhooks
   - Add endpoint: `https://yourdomain.com/api/webhooks/stripe`
   - Select event: `checkout.session.completed`
   - Copy signing secret to `.env`

3. **Local Testing with Stripe CLI**:
   ```bash
   # Install Stripe CLI
   stripe listen --forward-to localhost:8000/api/webhooks/stripe

   # Use test card: 4242 4242 4242 4242
   ```

4. **Set Base URL** in `.env`:
   ```bash
   BASE_URL=http://localhost:8000  # Development
   BASE_URL=https://yourdomain.com  # Production
   ```

## Architecture

- **FastAPI**: REST API for Q&A management and contribution flow
- **PostgreSQL + pgvector**: Vector similarity search
- **OpenAI**: Embedding generation and ChatGPT for answer suggestions
- **Stripe**: Payment processing for contributions
- **Jinja2**: HTML templates for checkout pages
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
