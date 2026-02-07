-- Migration: Add pending_contributions table
-- Created: 2025-02-07
-- Description: Adds table to track user contributions from initiation through completion

CREATE TABLE IF NOT EXISTS pending_contributions (
    id SERIAL PRIMARY KEY,

    -- Mention tracking
    platform VARCHAR NOT NULL,
    mention_id VARCHAR NOT NULL,
    author_id VARCHAR NOT NULL,

    -- QA data
    question TEXT NOT NULL,
    suggested_answers JSONB NOT NULL,  -- Array of 3 AI suggestions
    selected_answer TEXT,

    -- Payment tracking
    stripe_session_id VARCHAR UNIQUE,
    stripe_payment_intent VARCHAR,
    payment_status VARCHAR DEFAULT 'pending',  -- pending, paid, failed
    amount_cents INTEGER,  -- User-chosen amount

    -- State
    status VARCHAR DEFAULT 'awaiting_payment',
    -- Status flow: awaiting_payment → payment_received → qa_stored → complete

    -- Token for secure checkout URL
    token VARCHAR UNIQUE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    paid_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_pending_contributions_mention ON pending_contributions(platform, mention_id);
CREATE INDEX IF NOT EXISTS idx_pending_contributions_session ON pending_contributions(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_pending_contributions_status ON pending_contributions(status);
CREATE INDEX IF NOT EXISTS idx_pending_contributions_token ON pending_contributions(token);

-- Add comment
COMMENT ON TABLE pending_contributions IS 'Tracks user contributions with payment and QA storage lifecycle';
