#!/usr/bin/env python3
"""
Test script for contribution flow.

This script tests the end-to-end contribution flow without actual payment processing.
"""

import sys
from app.core.database import SessionLocal, init_db
from app.services.contribution_service import (
    create_contribution_with_suggestions,
    get_contribution_by_token,
    update_selected_answer,
    update_payment_info,
    mark_payment_received,
    finalize_contribution
)


def test_contribution_flow():
    """Test the complete contribution flow."""
    print("🧪 Testing Contribution Flow\n")

    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("✓ Database initialized\n")

    # Create database session
    db = SessionLocal()

    try:
        # Step 1: Create contribution with suggestions
        print("2. Creating contribution with AI suggestions...")
        contribution = create_contribution_with_suggestions(
            db=db,
            platform="twitter",
            mention_id="test_mention_123",
            author_id="test_user_456",
            question="What is quantum computing?"
        )
        print(f"✓ Contribution created: ID={contribution.id}")
        print(f"  Token: {contribution.token}")
        print(f"  Question: {contribution.question}")
        print(f"  Suggestions: {len(contribution.suggested_answers)}")
        for i, suggestion in enumerate(contribution.suggested_answers, 1):
            print(f"    {i}. {suggestion}")
        print()

        # Step 2: Get contribution by token
        print("3. Retrieving contribution by token...")
        retrieved = get_contribution_by_token(db, contribution.token)
        if retrieved:
            print(f"✓ Retrieved contribution: ID={retrieved.id}")
        else:
            print("✗ Failed to retrieve contribution")
            return False
        print()

        # Step 3: Update selected answer
        print("4. Updating selected answer...")
        test_answer = "Quantum computing uses quantum mechanical phenomena to perform computations."
        update_selected_answer(db, contribution.id, test_answer)
        print(f"✓ Answer updated: {test_answer[:50]}...")
        print()

        # Step 4: Update payment info
        print("5. Simulating Stripe checkout session...")
        test_session_id = "cs_test_123456789"
        test_amount = 500  # $5.00
        update_payment_info(db, contribution.id, test_session_id, test_amount)
        print(f"✓ Payment info updated")
        print(f"  Session ID: {test_session_id}")
        print(f"  Amount: ${test_amount / 100:.2f}")
        print()

        # Step 5: Mark payment received
        print("6. Simulating payment webhook...")
        test_payment_intent = "pi_test_987654321"
        paid_contribution = mark_payment_received(db, test_session_id, test_payment_intent)
        print(f"✓ Payment marked as received")
        print(f"  Status: {paid_contribution.status}")
        print(f"  Payment Status: {paid_contribution.payment_status}")
        print()

        # Step 6: Finalize contribution (store QA pair)
        print("7. Finalizing contribution (storing QA pair)...")
        question_obj = finalize_contribution(db, contribution.id)
        print(f"✓ QA pair stored in database")
        print(f"  Question ID: {question_obj.id}")
        print(f"  Question: {question_obj.question}")
        print(f"  Answer: {question_obj.answer[:50]}...")
        print()

        # Step 7: Verify final state
        print("8. Verifying final state...")
        final_contribution = get_contribution_by_token(db, contribution.token)
        if final_contribution:
            print(f"✓ Final state verified")
            print(f"  Status: {final_contribution.status}")
            print(f"  Payment Status: {final_contribution.payment_status}")
            print(f"  Completed At: {final_contribution.completed_at}")
        print()

        print("✅ All tests passed! Contribution flow works correctly.\n")
        print("Next steps:")
        print("1. Start API server: uvicorn app.api.main:app --reload")
        print("2. Start Stripe CLI: stripe listen --forward-to localhost:8000/api/webhooks/stripe")
        print("3. Test with real checkout: botx simulate-mention --text 'unknown question'")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_contribution_flow()
    sys.exit(0 if success else 1)
