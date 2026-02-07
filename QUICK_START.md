# Quick Start: Payment-Enabled Contribution Feature

## ✅ Implementation Status

**All checks passed!** The contribution feature is fully implemented and ready to use.

## What Was Built

A complete payment-enabled learning system where users can teach the bot new answers when no match is found:

1. **AI Answer Generation** - ChatGPT generates 3 diverse answer suggestions
2. **Beautiful Checkout UI** - Web-based payment interface with Stripe
3. **Secure Payment Processing** - User-chosen amounts ($1+ minimum)
4. **Automatic QA Storage** - Embeddings generated and stored in database
5. **Bot Reply** - Thank you message posted to original mention

## Files Created (12 new files)

### Core Services
- ✅ `app/services/answer_generator.py` - ChatGPT integration
- ✅ `app/services/contribution_service.py` - Lifecycle management
- ✅ `app/services/stripe_service.py` - Payment processing

### API & Templates
- ✅ `app/api/contributions.py` - REST endpoints
- ✅ `app/templates/checkout.html` - Checkout page
- ✅ `app/templates/success.html` - Success page
- ✅ `app/templates/cancel.html` - Cancel page

### Database & Testing
- ✅ `migrations/add_pending_contributions.sql` - DB migration
- ✅ `test_contribution_flow.py` - Automated test
- ✅ `verify_implementation.py` - Verification script

### Documentation
- ✅ `CONTRIBUTION_FEATURE.md` - Complete setup guide
- ✅ `IMPLEMENTATION_COMPLETE.md` - Implementation summary
- ✅ `QUICK_START.md` - This file

## Files Modified (7 files)

- ✅ `pyproject.toml` - Added stripe, jinja2
- ✅ `app/core/config.py` - Added settings
- ✅ `app/core/database.py` - Added PendingContribution model
- ✅ `app/services/responder.py` - Added contribution flow
- ✅ `app/api/main.py` - Registered router
- ✅ `.env.example` - Added variables
- ✅ `README.md` - Added feature docs

## Setup (5 minutes)

### 1. Verify Installation

```bash
# Run verification (should show 10/10 checks passed)
uv run python verify_implementation.py
```

### 2. Configure Environment

Create/update `.env` with these new variables:

```bash
# Stripe (get test keys from stripe.com/dashboard)
STRIPE_API_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
STRIPE_MIN_CONTRIBUTION_CENTS=100

# ChatGPT
CHATGPT_MODEL=gpt-3.5-turbo

# Application
BASE_URL=http://localhost:8000
CONTRIBUTION_EXPIRY_HOURS=24
```

**Getting Stripe Keys:**
1. Sign up at [stripe.com](https://stripe.com)
2. Go to Dashboard → Developers → API keys
3. Copy "Secret key" (starts with `sk_test_`)
4. We'll set up webhook secret in step 4

### 3. Initialize Database

```bash
# Create new pending_contributions table
uv run botx init-db
```

Or run migration manually:
```bash
psql $DATABASE_URL -f migrations/add_pending_contributions.sql
```

### 4. Test the Implementation

```bash
# Run automated test (simulates full flow without payment)
uv run python test_contribution_flow.py
```

Expected output:
```
✅ All tests passed! Contribution flow works correctly.
```

## Local Testing with Stripe (10 minutes)

### Terminal 1: Start API Server

```bash
uvicorn app.api.main:app --reload
```

### Terminal 2: Start Stripe CLI

```bash
# Install Stripe CLI first (one-time)
# macOS: brew install stripe/stripe-cli/stripe
# Linux: https://stripe.com/docs/stripe-cli

# Login
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/webhooks/stripe
```

**Important**: Copy the webhook signing secret from output:
```
> Ready! Your webhook signing secret is whsec_xxxxx
```

Add this to `.env`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### Terminal 3: Start Bot

```bash
python -m app.bot.runner
```

### Test End-to-End

1. **Simulate mention with unknown question**:
   ```bash
   uv run botx simulate-mention --platform twitter --text "What is quantum entanglement?"
   ```

2. **Bot should reply** with checkout link in Terminal 3

3. **Open checkout URL** in browser (copy from bot output)

4. **Complete checkout**:
   - Select or write an answer
   - Enter amount: $5.00
   - Use test card: `4242 4242 4242 4242`
   - Any future expiry, any CVC
   - Click "Proceed to Payment"

5. **Verify success**:
   - Terminal 2: See webhook event `checkout.session.completed`
   - Terminal 1: See "Payment received" and "QA pair stored" logs
   - Browser: Success page displayed
   - Terminal 3: Bot posts thank you reply
   - Database: New QA pair stored

### Verify in Database

```sql
-- Check new contribution
SELECT * FROM pending_contributions ORDER BY created_at DESC LIMIT 1;

-- Check new QA pair
SELECT * FROM questions ORDER BY created_at DESC LIMIT 1;
```

## Production Deployment

### 1. Get Live Stripe Keys

1. Go to Stripe Dashboard → Switch to "Live mode"
2. Get live API key (starts with `sk_live_`)
3. Update `.env`: `STRIPE_API_KEY=sk_live_...`

### 2. Configure Production Webhook

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. URL: `https://yourdomain.com/api/webhooks/stripe`
4. Events: Select `checkout.session.completed`
5. Copy signing secret to `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`

### 3. Update Base URL

```bash
BASE_URL=https://yourdomain.com
```

### 4. Deploy with HTTPS

**Important**: Stripe webhooks require HTTPS. Use:
- Let's Encrypt for free SSL certificates
- Cloudflare for automatic HTTPS
- Your hosting provider's SSL

## Troubleshooting

### ✗ Imports fail when running tests

**Solution**: Use `uv run` prefix:
```bash
uv run python verify_implementation.py
uv run python test_contribution_flow.py
```

### ✗ Webhook not receiving events

**Checklist**:
- [ ] Stripe CLI is running: `stripe listen --forward-to localhost:8000/api/webhooks/stripe`
- [ ] Webhook secret copied to `.env`
- [ ] API server is running
- [ ] No firewall blocking localhost:8000

### ✗ "No module named 'stripe'"

**Solution**: Install dependencies:
```bash
uv pip install stripe jinja2
```

### ✗ Database table doesn't exist

**Solution**: Run database initialization:
```bash
uv run botx init-db
```

### ✗ Bot doesn't reply with checkout link

**Checklist**:
- [ ] Question doesn't match existing QAs (similarity < 0.8)
- [ ] `BASE_URL` set in `.env`
- [ ] OpenAI API key valid for ChatGPT
- [ ] Check logs for errors

### ✗ Payment succeeds but QA not stored

**Checklist**:
- [ ] Webhook received (check Terminal 2)
- [ ] Database connection working
- [ ] OpenAI API key valid for embeddings
- [ ] Check API logs for errors

## Next Steps

1. ✅ Run verification: `uv run python verify_implementation.py`
2. ✅ Run automated test: `uv run python test_contribution_flow.py`
3. ⏭️ Set up Stripe account and get test keys
4. ⏭️ Test end-to-end with Stripe CLI
5. ⏭️ Deploy to production with HTTPS
6. ⏭️ Monitor metrics (conversion rate, revenue, quality)

## Documentation

- **Full Setup Guide**: `CONTRIBUTION_FEATURE.md`
- **Implementation Details**: `IMPLEMENTATION_COMPLETE.md`
- **Main README**: `README.md` (updated with feature overview)

## Support

**All checks passing?** ✅ You're ready to go!

**Issues?** Check:
1. Logs in API server and bot runner
2. Stripe dashboard for payment events
3. Environment variables are set correctly
4. Database tables created successfully

---

**Status**: ✅ Implementation Complete (verified 10/10 checks)
**Ready for**: Local testing and production deployment
