# Payment-Enabled QA Learning Feature

## Overview

This feature enables users to teach the bot new answers when no match is found by contributing through a payment-enabled web interface. When the bot receives a mention that doesn't match any stored QA pairs (similarity < 0.8), it generates AI-powered answer suggestions and provides a checkout link where users can select or write their own answer and contribute via Stripe payment.

## How It Works

### User Flow

```
User mentions bot → No match found (similarity < 0.8)
  ↓
Bot generates 3 AI suggestions via ChatGPT
  ↓
Bot replies: "I don't know this yet! Help me learn: [checkout-link]"
  ↓
User clicks → Web page shows question + 3 options + custom field
  ↓
User selects/writes answer → Enters payment amount ($1+) → Stripe checkout
  ↓
Payment succeeds → Stripe webhook → Backend processes:
  - Generates embedding for question
  - Stores QA pair in questions table
  - Bot replies to original mention with thank you
  - Shows success page
```

### Technical Flow

1. **No Match Detection**: `responder.py` detects no match (similarity < 0.8)
2. **Contribution Creation**: `contribution_service.py` creates pending contribution
3. **AI Suggestions**: `answer_generator.py` generates 3 diverse answers via ChatGPT
4. **Checkout Page**: User accesses web page with question and suggestions
5. **Payment Processing**: Stripe handles secure payment ($1+ minimum, user-chosen)
6. **Webhook Handler**: Receives payment confirmation from Stripe
7. **QA Storage**: Generates embedding and stores in database
8. **Bot Reply**: Posts thank you message to original mention

## Setup Instructions

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Stripe Payment Settings
STRIPE_API_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret
STRIPE_MIN_CONTRIBUTION_CENTS=100

# ChatGPT Settings
CHATGPT_MODEL=gpt-3.5-turbo

# Application Settings
BASE_URL=http://localhost:8000  # Change to production URL in production
CONTRIBUTION_EXPIRY_HOURS=24
```

### 2. Stripe Setup

#### Get API Keys
1. Sign up at [stripe.com](https://stripe.com) (use test mode for development)
2. Go to Dashboard → Developers → API keys
3. Copy "Secret key" to `STRIPE_API_KEY` in `.env`

#### Configure Webhook
1. Go to Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Enter endpoint URL:
   - **Development**: Use Stripe CLI (see below)
   - **Production**: `https://yourdomain.com/api/webhooks/stripe`
4. Select events to listen for: `checkout.session.completed`
5. Copy "Signing secret" to `STRIPE_WEBHOOK_SECRET` in `.env`

### 3. Database Migration

Run the migration to create the `pending_contributions` table:

```bash
# Using the migration script
psql $DATABASE_URL -f migrations/add_pending_contributions.sql

# Or let SQLAlchemy create it automatically
botx init-db
```

### 4. Local Development Testing

#### Using Stripe CLI

1. **Install Stripe CLI**:
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe

   # Linux
   wget https://github.com/stripe/stripe-cli/releases/download/v1.19.5/stripe_1.19.5_linux_x86_64.tar.gz
   tar -xvf stripe_1.19.5_linux_x86_64.tar.gz
   sudo mv stripe /usr/local/bin/
   ```

2. **Login to Stripe**:
   ```bash
   stripe login
   ```

3. **Forward webhooks to local server**:
   ```bash
   stripe listen --forward-to localhost:8000/api/webhooks/stripe
   ```

   This will output a webhook signing secret - copy it to `STRIPE_WEBHOOK_SECRET` in `.env`

4. **Test with Stripe test cards**:
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
   - Any future expiry date, any CVC

### 5. Production Deployment

1. **Switch to Live Mode**:
   - Get live API keys from Stripe dashboard
   - Update `STRIPE_API_KEY` with live key
   - Configure webhook with production URL

2. **HTTPS Required**:
   - Stripe webhooks require HTTPS
   - Use Let's Encrypt for free SSL certificates
   - Configure `BASE_URL` with `https://` prefix

3. **Webhook Configuration**:
   - Add production webhook endpoint in Stripe dashboard
   - Update `STRIPE_WEBHOOK_SECRET` with production secret

## Testing

### Manual Testing

1. **Start the API server**:
   ```bash
   uvicorn app.api.main:app --reload
   ```

2. **Start Stripe CLI** (in another terminal):
   ```bash
   stripe listen --forward-to localhost:8000/api/webhooks/stripe
   ```

3. **Start the bot**:
   ```bash
   python -m app.bot.runner
   ```

4. **Simulate a mention with unknown question**:
   ```bash
   botx simulate-mention --platform twitter --text "What is quantum computing?"
   ```

5. **Check bot response** - should include checkout link

6. **Access checkout URL** in browser

7. **Complete payment flow**:
   - Select or write an answer
   - Enter amount ($5.00 recommended)
   - Use test card: `4242 4242 4242 4242`
   - Complete checkout

8. **Verify**:
   - Check Stripe CLI for webhook event
   - Check API logs for processing
   - Verify QA stored in database: `SELECT * FROM questions ORDER BY created_at DESC LIMIT 1;`
   - Verify bot posted thank you reply

### Testing Answer Generation

Test the ChatGPT answer generation:

```python
from app.services.answer_generator import generate_answer_suggestions

suggestions = generate_answer_suggestions("What is AI?")
print(suggestions)
# Should output 3 diverse, concise answers
```

### Database Verification

Check pending contributions:

```sql
-- View all contributions
SELECT id, platform, question, status, payment_status, created_at
FROM pending_contributions
ORDER BY created_at DESC;

-- View successful contributions
SELECT * FROM pending_contributions
WHERE status = 'complete'
ORDER BY completed_at DESC;

-- Check new QA pairs
SELECT q.id, q.question, q.answer, q.created_at
FROM questions q
ORDER BY q.created_at DESC
LIMIT 10;
```

## API Endpoints

### Checkout Page
```
GET /checkout/{token}
```
Displays the checkout page with question, AI suggestions, and payment form.

### Create Checkout Session
```
POST /api/contributions/{contribution_id}/create-checkout
Body: {
  "answer": "Selected or custom answer",
  "amount_cents": 500  // $5.00
}
```
Creates Stripe checkout session and returns checkout URL.

### Success Page
```
GET /checkout/success/{token}
```
Displays success page after payment completion.

### Cancel Page
```
GET /checkout/cancel/{token}
```
Displays cancellation page if payment was cancelled.

### Stripe Webhook
```
POST /api/webhooks/stripe
Headers: {
  "stripe-signature": "..."
}
```
Receives webhook events from Stripe. Handles `checkout.session.completed` event.

## Database Schema

### pending_contributions Table

```sql
CREATE TABLE pending_contributions (
    id SERIAL PRIMARY KEY,
    platform VARCHAR NOT NULL,
    mention_id VARCHAR NOT NULL,
    author_id VARCHAR NOT NULL,
    question TEXT NOT NULL,
    suggested_answers JSONB NOT NULL,
    selected_answer TEXT,
    stripe_session_id VARCHAR UNIQUE,
    stripe_payment_intent VARCHAR,
    payment_status VARCHAR DEFAULT 'pending',
    amount_cents INTEGER,
    status VARCHAR DEFAULT 'awaiting_payment',
    token VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    paid_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Status Flow

1. **awaiting_payment**: Contribution created, waiting for payment
2. **payment_received**: Payment confirmed by Stripe
3. **qa_stored**: QA pair stored in database
4. **complete**: Bot reply posted successfully

## Security Considerations

1. **Webhook Verification**: All webhook requests are verified using Stripe signature
2. **Token Security**: UUIDs used for checkout URLs, checked for expiration
3. **Input Validation**:
   - Question length: 10-500 characters
   - Answer length: 10-1000 characters
   - Payment amount: $1.00 minimum, $10,000 maximum
4. **HTTPS Required**: Production must use HTTPS for Stripe webhooks
5. **No Sensitive Data Storage**: Only Stripe session IDs stored, not card details

## Monitoring & Maintenance

### Metrics to Track

1. **Conversion Rate**: Mentions without matches → Contributions completed
2. **Revenue**: Total contribution amount, average per contribution
3. **Quality**: How often contributed QAs match future questions
4. **Expiration**: How many contributions expire without payment

### Cleanup Tasks

Consider adding a cleanup job to handle expired contributions:

```sql
-- Delete expired contributions older than 7 days
DELETE FROM pending_contributions
WHERE status = 'awaiting_payment'
AND expires_at < NOW() - INTERVAL '7 days';
```

### Logs to Monitor

- Contribution creation
- Payment received webhooks
- QA pair storage
- Bot reply posting
- Webhook verification failures
- Payment processing errors

## Troubleshooting

### Webhook Not Receiving Events

1. Check Stripe CLI is running: `stripe listen --forward-to localhost:8000/api/webhooks/stripe`
2. Verify webhook endpoint in Stripe dashboard
3. Check `STRIPE_WEBHOOK_SECRET` in `.env`
4. Check API server logs for webhook verification errors

### Payment Succeeds but QA Not Stored

1. Check webhook handler logs for errors
2. Verify database connection
3. Check `pending_contributions` table for record status
4. Verify OpenAI API key is valid for embeddings

### Bot Not Posting Reply

1. Check platform credentials (Twitter/Bluesky)
2. Verify bot has permission to reply
3. Check worker logs for posting errors
4. QA pair still stored even if reply fails

### Checkout Page Not Loading

1. Verify `BASE_URL` in `.env`
2. Check contribution token is valid and not expired
3. Check Jinja2 templates exist in `app/templates/`
4. Check API server is running

## Future Enhancements

1. **Multiple Payment Methods**: Add PayPal, cryptocurrency
2. **Contributor Dashboard**: Show user's contributions and impact
3. **Moderation Queue**: Review contributions before publishing
4. **Refund System**: Handle refund requests
5. **Analytics Dashboard**: Track metrics and revenue
6. **Contributor Rewards**: Badges, leaderboards, free credits
7. **Bulk Import**: Allow moderators to approve/reject contributions
8. **API for Contributions**: Programmatic contribution submission

## Support

For issues or questions:
- Check logs in API server and bot runner
- Review Stripe dashboard for payment issues
- Verify environment variables are set correctly
- Test with Stripe CLI in development mode
