# Improvement Feature: Competitive Answer Replacement

## Overview

The bot now **always** offers users the option to contribute, even when an existing answer is found. Users can "outbid" previous contributors by paying more to replace an answer with a better one.

## How It Works

### Previous Behavior
- Match found (similarity > 0.8) → Reply with answer → Done
- No match found → Offer to contribute new answer

### New Behavior
- **Match found** → Reply with answer + "Not satisfied? Teach me a better answer: [checkout-link]"
- **No match found** → Offer to contribute new answer

## User Flow

### Improving an Existing Answer

1. **User mentions bot** with a question
2. **Bot finds match** (similarity > 0.8)
3. **Bot replies** with:
   ```
   [The current answer]

   💡 Not satisfied? Teach me a better answer: http://your-domain.com/checkout/xyz
   ```
4. **User clicks link** → Sees checkout page showing:
   - The question
   - **Current answer** (marked as "to be replaced")
   - 3 AI-generated alternative suggestions
   - Option to write custom answer
   - **Minimum payment**: Previous contribution + $1.00
5. **User pays more** → Answer replaced
6. **Bot posts thank you** reply to original mention

### Contributing New Answer

Same as before - when no match is found (similarity < 0.8).

## Technical Implementation

### Database Changes

#### `questions` Table
Added column:
- `contribution_amount_cents INTEGER DEFAULT 0` - Tracks how much was paid for this answer

#### `pending_contributions` Table
Added columns:
- `improvement_of_question_id INTEGER` - Question ID being improved (NULL for new)
- `existing_answer TEXT` - Current answer being replaced (for display)
- `minimum_amount_cents INTEGER DEFAULT 100` - Minimum required payment

### Service Layer Changes

#### `contribution_service.py`
New function:
- `create_improvement_contribution()` - Creates contribution for replacing existing answer
  - Sets `improvement_of_question_id` to existing question ID
  - Sets `minimum_amount_cents` to `existing_amount + $1.00`
  - Stores existing answer for display

Updated function:
- `finalize_contribution()` - Now handles both new and improvement contributions
  - If `improvement_of_question_id` is set: **updates** existing Question
  - If NULL: creates new Question
  - Updates `contribution_amount_cents` on Question

#### `responder.py`
Updated functions:
- `find_best_match()` - Now returns: `(question_id, question, answer, similarity, contribution_amount)`
- `process_mention()` - When match found:
  - Creates improvement contribution
  - Includes checkout link in reply
  - Graceful fallback if improvement creation fails

### API Changes

#### `/checkout/{token}` Endpoint
Now passes to template:
- `is_improvement` - Boolean flag
- `existing_answer` - Current answer (if improving)
- `minimum_amount_cents` - Dynamic minimum based on contribution type
- `minimum_amount_dollars` - Same in dollars for display

#### `/api/contributions/{id}/create-checkout` Endpoint
- Validates amount against `contribution.minimum_amount_cents` instead of fixed minimum
- Error message shows dynamic minimum: "Minimum contribution is $X.XX"

### Frontend Changes

#### `checkout.html` Template

**When Improving** (`is_improvement = true`):
- Title: "Improve This Answer" (instead of "Help the Bot Learn!")
- Shows existing answer in orange-bordered box
- Info box explains: "You must contribute at least $X.XX to replace the current answer"
- Amount field pre-filled with minimum required
- All validation enforces dynamic minimum

**When New** (`is_improvement = false`):
- Same as before
- Uses standard $1.00 minimum

## Examples

### Example 1: First Contribution (New Answer)

```
User: @bot What is TypeScript?
Bot: I don't have an answer for this yet! 🤔
     Help me learn: http://domain.com/checkout/abc123

User: [Pays $5.00, writes answer]
Bot: Thank you for teaching me! 🎉
```

**Database State:**
- Question: "What is TypeScript?"
- Answer: "TypeScript is..."
- contribution_amount_cents: 500

### Example 2: Improvement

```
User: @bot What is TypeScript?
Bot: TypeScript is a programming language.

     💡 Not satisfied? Teach me a better answer: http://domain.com/checkout/xyz456

User: [Clicks link, sees existing answer, must pay >$5.00]
User: [Pays $10.00, writes better answer]
Bot: Thank you for teaching me! 🎉
```

**Database State:**
- Same Question ID (updated)
- Answer: "TypeScript is a statically typed superset of JavaScript..." (new)
- contribution_amount_cents: 1000 (updated)

### Example 3: Multiple Improvements

```
Contribution 1: $5.00 → "Basic answer"
Contribution 2: Must pay >$5.00 → $10.00 → "Better answer"
Contribution 3: Must pay >$10.00 → $20.00 → "Even better answer"
```

Each improvement must pay more than the previous one.

## Business Logic

### Minimum Payment Rules

- **New contribution**: $1.00 minimum (configurable via `STRIPE_MIN_CONTRIBUTION_CENTS`)
- **Improvement**: Previous amount + $1.00

Formula: `minimum_amount_cents = existing_amount_cents + 100`

### What Gets Replaced

When an improvement is finalized:
- ✅ Answer is replaced
- ✅ Embedding is regenerated (new semantic meaning)
- ✅ Contribution amount updated
- ✅ Timestamp updated (created_at)
- ❌ Question ID stays the same (no new record)
- ❌ Old answer is not versioned (direct replacement)

### Revenue Model

This creates a "continuous improvement auction" where:
1. Initial answer costs $1+ to add
2. Better answers must pay progressively more
3. Quality naturally increases with contribution amount
4. Users are incentivized to provide genuinely better answers

## Testing

### Test Scenarios

1. **New contribution with no match**
   - Expected: Standard $1.00 minimum

2. **Improvement of $5.00 answer**
   - Expected: Minimum $6.00 required
   - Checkout shows existing answer
   - Payment <$6.00 rejected

3. **Improvement of $100.00 answer**
   - Expected: Minimum $101.00 required
   - High-value answer requires significant improvement investment

4. **Improvement creation fails**
   - Expected: Bot still replies with just the answer (no checkout link)
   - Graceful degradation

### Manual Testing

```bash
# Terminal 1: API
uvicorn app.api.main:app --reload

# Terminal 2: Stripe
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Terminal 3: Bot
python -m app.bot.runner

# Terminal 4: Test
# 1. Add a question with known answer
uv run botx add-qa -q "What is Python?" -a "A programming language"

# 2. Simulate mention
uv run botx simulate-mention --text "What is Python?"

# Expected: Bot replies with answer + checkout link
# 3. Access checkout URL, should show existing answer and require >$1.00
```

### Database Queries

```sql
-- Check questions with contributions
SELECT id, question, answer, contribution_amount_cents / 100.0 as amount_dollars
FROM questions
WHERE contribution_amount_cents > 0
ORDER BY contribution_amount_cents DESC;

-- Check improvement contributions
SELECT id, question, existing_answer, minimum_amount_cents / 100.0 as min_dollars,
       improvement_of_question_id, status
FROM pending_contributions
WHERE improvement_of_question_id IS NOT NULL
ORDER BY created_at DESC;

-- Check contribution history for a question
SELECT pc.created_at, pc.amount_cents / 100.0 as amount_dollars,
       pc.selected_answer, pc.status
FROM pending_contributions pc
WHERE pc.improvement_of_question_id = 123  -- Replace with question ID
   OR (pc.improvement_of_question_id IS NULL AND pc.question = 'Question text')
ORDER BY pc.created_at ASC;
```

## Configuration

No new environment variables needed. Uses existing:
- `STRIPE_MIN_CONTRIBUTION_CENTS` - Base minimum for new contributions (default: 100 = $1.00)
- All other settings remain the same

## Migration

### Apply Database Migration

```bash
# Option 1: SQLAlchemy auto-create
uv run botx init-db

# Option 2: Manual SQL
psql $DATABASE_URL -f migrations/add_improvement_features.sql
```

### Verify Migration

```sql
-- Check new columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'questions' AND column_name = 'contribution_amount_cents';

SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'pending_contributions'
  AND column_name IN ('improvement_of_question_id', 'existing_answer', 'minimum_amount_cents');
```

## Future Enhancements

1. **Answer Versioning**: Keep history of all previous answers
2. **Refund System**: Refund if better answer submitted within X days
3. **Contributor Leaderboard**: Show top contributors by total amount
4. **Answer Quality Voting**: Users vote on answer quality (free)
5. **Dynamic Minimum**: Base minimum on answer popularity/usage
6. **Improvement Threshold**: Require minimum % improvement via AI evaluation
7. **Collaborative Improvements**: Multiple users can contribute to improve together

## Breaking Changes

None. This is backwards compatible:
- Existing questions get `contribution_amount_cents = 0`
- Existing contributions work as before (new answers)
- Old checkout URLs continue working

## Rollback

If needed, rollback migration:

```sql
ALTER TABLE questions DROP COLUMN IF EXISTS contribution_amount_cents;

ALTER TABLE pending_contributions
DROP COLUMN IF EXISTS improvement_of_question_id,
DROP COLUMN IF EXISTS existing_answer,
DROP COLUMN IF EXISTS minimum_amount_cents;
```

Then revert code changes and restart services.
