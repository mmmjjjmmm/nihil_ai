# Quick Start: Competitive Answer Improvement

## What's New?

The bot now **always** offers users the chance to contribute, even when an answer exists. Users can "outbid" previous contributors to replace answers with better ones.

## TL;DR

- ✅ **Bot always replies** with answer + checkout link
- ✅ **Improvements cost more** than the previous contribution ($1+ minimum increase)
- ✅ **Better answers win** - competitive pricing ensures quality
- ✅ **Backwards compatible** - existing functionality unchanged

## Quick Test (5 minutes)

### 1. Apply Migration

```bash
uv run botx init-db
```

This adds new columns to track contribution amounts and improvements.

### 2. Add a Test Question

```bash
uv run botx add-qa -q "What is Python?" -a "A programming language"
```

This creates an answer worth $0 (manually added).

### 3. Start Services

Terminal 1 - API:
```bash
uvicorn app.api.main:app --reload
```

Terminal 2 - Stripe CLI:
```bash
stripe listen --forward-to localhost:8000/api/webhooks/stripe
```

Terminal 3 - Bot:
```bash
python -m app.bot.runner
```

### 4. Test the Flow

Terminal 4 - Simulate mention:
```bash
uv run botx simulate-mention --text "What is Python?"
```

**Expected bot reply**:
```
A programming language

💡 Not satisfied? Teach me a better answer: http://localhost:8000/checkout/xyz
```

### 5. Access Checkout Link

Copy the checkout URL from bot output and open in browser.

**You should see**:
- Question: "What is Python?"
- **Current Answer** (orange box): "A programming language"
- Warning: "You must contribute at least $1.00"
- 3 AI-generated alternative suggestions
- Custom answer option
- Amount field (minimum $1.00)

### 6. Complete Payment

- Select or write a better answer
- Enter amount: $5.00 (or more)
- Use test card: `4242 4242 4242 4242`
- Complete checkout

**Result**:
- Payment processed
- Answer replaced in database
- Bot posts thank you reply
- `contribution_amount_cents` updated to 500

### 7. Test Improvement Again

```bash
uv run botx simulate-mention --text "What is Python?"
```

**Expected**:
- Bot replies with NEW answer
- Checkout link still provided
- **Minimum now $6.00** (previous $5 + $1)

## How It Works

### Pricing Logic

```python
if is_improvement:
    minimum_amount = previous_contribution + $1.00
else:
    minimum_amount = $1.00  # Default for new answers
```

### What Gets Updated

When improvement is paid:
```sql
UPDATE questions SET
  answer = new_answer,
  embedding = new_embedding,
  contribution_amount_cents = new_amount,
  created_at = NOW()
WHERE id = question_id;
```

### Database State After Improvements

```
Initial:     Question "What is Python?" → "A language" → $0
After 1st:   Question "What is Python?" → "Better answer" → $5
After 2nd:   Question "What is Python?" → "Even better" → $10
After 3rd:   Question "What is Python?" → "Best answer" → $20
```

Same question ID, progressively better answers.

## Configuration

No new environment variables! Uses existing settings:
- `STRIPE_MIN_CONTRIBUTION_CENTS=100` (applies to new answers)
- Improvements automatically calculated as `previous + $1.00`

## Verification

### Check Database After Improvement

```sql
-- View questions with contributions
SELECT id, question, answer,
       contribution_amount_cents / 100.0 as amount_dollars
FROM questions
WHERE contribution_amount_cents > 0
ORDER BY contribution_amount_cents DESC;

-- View improvement contributions
SELECT id, question, existing_answer, selected_answer,
       minimum_amount_cents / 100.0 as min_dollars,
       amount_cents / 100.0 as paid_dollars,
       status
FROM pending_contributions
WHERE improvement_of_question_id IS NOT NULL
ORDER BY created_at DESC;
```

### Expected Output

After first improvement of "What is Python?":
```
 id |     question     |        answer         | amount_dollars
----+------------------+-----------------------+---------------
  1 | What is Python?  | Better answer here... |          5.00
```

After second improvement:
```
 id |     question     |        answer         | amount_dollars
----+------------------+-----------------------+---------------
  1 | What is Python?  | Even better answer... |         10.00
```

## API Behavior Changes

### Before
```
GET /checkout/{token}
Returns: Standard checkout page with $1.00 minimum
```

### After
```
GET /checkout/{token}
Returns:
  - If is_improvement: Shows existing answer, dynamic minimum
  - If new: Standard page, $1.00 minimum
```

### Validation
```python
# Before
if amount < 1.00:
    raise Error("Minimum $1.00")

# After
if amount < contribution.minimum_amount_cents / 100:
    raise Error(f"Minimum ${contribution.minimum_amount_cents / 100:.2f}")
```

## Troubleshooting

### ❌ "Column 'contribution_amount_cents' does not exist"

**Solution**: Run migration
```bash
uv run botx init-db
```

### ❌ Bot replies without checkout link

**Possible causes**:
1. Improvement contribution creation failed (check logs)
2. Graceful fallback activated (bot still replies with answer)

**Solution**: Check API server logs for errors

### ❌ Checkout page shows wrong minimum

**Cause**: Old checkout link (before improvement)

**Solution**: Get fresh link from latest bot reply

### ❌ Payment rejected: "Minimum contribution is $X.XX"

**Cause**: Trying to pay less than required for improvement

**Solution**: Pay at least the minimum shown ($previous + $1.00)

## Rollback

If needed:

```sql
-- Remove new columns
ALTER TABLE questions DROP COLUMN contribution_amount_cents;
ALTER TABLE pending_contributions
  DROP COLUMN improvement_of_question_id,
  DROP COLUMN existing_answer,
  DROP COLUMN minimum_amount_cents;

-- Restart services
```

## Full Documentation

- **Complete guide**: `IMPROVEMENT_FEATURE.md`
- **Implementation details**: `IMPROVEMENT_IMPLEMENTATION_SUMMARY.md`
- **Original feature**: `CONTRIBUTION_FEATURE.md`

## Summary

✅ **Migration**: Add 4 new columns to 2 tables
✅ **Behavior**: Bot always offers improvement option
✅ **Pricing**: Must pay more than previous contribution
✅ **UI**: Shows existing answer when improving
✅ **Quality**: Competitive pricing ensures continuous improvement

**Status**: Ready to use! 🚀
