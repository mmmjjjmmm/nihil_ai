-- Migration: Add improvement features
-- Created: 2025-02-07
-- Description: Adds contribution tracking to questions and improvement support to pending_contributions

-- Add contribution amount tracking to questions table
ALTER TABLE questions
ADD COLUMN IF NOT EXISTS contribution_amount_cents INTEGER DEFAULT 0;

-- Add improvement tracking fields to pending_contributions table
ALTER TABLE pending_contributions
ADD COLUMN IF NOT EXISTS improvement_of_question_id INTEGER,
ADD COLUMN IF NOT EXISTS existing_answer TEXT,
ADD COLUMN IF NOT EXISTS minimum_amount_cents INTEGER DEFAULT 100;

-- Add comments
COMMENT ON COLUMN questions.contribution_amount_cents IS 'Amount (in cents) paid to contribute this answer';
COMMENT ON COLUMN pending_contributions.improvement_of_question_id IS 'Question ID being improved (NULL for new contributions)';
COMMENT ON COLUMN pending_contributions.existing_answer IS 'Current answer being replaced (for display to user)';
COMMENT ON COLUMN pending_contributions.minimum_amount_cents IS 'Minimum required payment (higher for improvements)';

-- Update existing questions to have 0 contribution amount (free/manually added)
UPDATE questions
SET contribution_amount_cents = 0
WHERE contribution_amount_cents IS NULL;
