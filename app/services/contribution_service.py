import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import PendingContribution, Question
from app.services.answer_generator import generate_answer_suggestions
from app.services.embedding import get_embedding


def create_improvement_contribution(
    db: Session,
    platform: str,
    mention_id: str,
    author_id: str,
    question: str,
    existing_question_id: int,
    existing_answer: str,
    existing_amount_cents: int
) -> PendingContribution:
    """
    Create a pending contribution to improve an existing answer.

    Args:
        db: Database session
        platform: Platform name (twitter, bluesky)
        mention_id: Platform-specific mention ID
        author_id: Platform-specific author ID
        question: The question text
        existing_question_id: ID of the question being improved
        existing_answer: Current answer (for display)
        existing_amount_cents: Amount paid for current answer

    Returns:
        Created PendingContribution object
    """
    # Generate AI suggestions for improvement
    suggestions = generate_answer_suggestions(question)

    # Generate secure token
    token = str(uuid.uuid4())

    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(hours=settings.contribution_expiry_hours)

    # Minimum payment must be at least $1 more than existing
    minimum_amount = existing_amount_cents + 100  # Existing + $1.00

    # Create contribution record
    contribution = PendingContribution(
        platform=platform,
        mention_id=mention_id,
        author_id=author_id,
        question=question,
        suggested_answers=suggestions,
        improvement_of_question_id=existing_question_id,
        existing_answer=existing_answer,
        minimum_amount_cents=minimum_amount,
        token=token,
        expires_at=expires_at
    )

    db.add(contribution)
    db.commit()
    db.refresh(contribution)

    return contribution


def create_contribution_with_suggestions(
    db: Session,
    platform: str,
    mention_id: str,
    author_id: str,
    question: str
) -> PendingContribution:
    """
    Create a new pending contribution with AI-generated answer suggestions.

    Args:
        db: Database session
        platform: Platform name (twitter, bluesky)
        mention_id: Platform-specific mention ID
        author_id: Platform-specific author ID
        question: The question to generate answers for

    Returns:
        Created PendingContribution object
    """
    # Generate AI suggestions
    suggestions = generate_answer_suggestions(question)

    # Generate secure token
    token = str(uuid.uuid4())

    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(hours=settings.contribution_expiry_hours)

    # Create contribution record
    contribution = PendingContribution(
        platform=platform,
        mention_id=mention_id,
        author_id=author_id,
        question=question,
        suggested_answers=suggestions,
        token=token,
        expires_at=expires_at
    )

    db.add(contribution)
    db.commit()
    db.refresh(contribution)

    return contribution


def get_contribution_by_token(db: Session, token: str) -> PendingContribution | None:
    """
    Get contribution by token, validating expiration.

    Args:
        db: Database session
        token: Secure token

    Returns:
        PendingContribution object if valid and not expired, None otherwise
    """
    contribution = db.query(PendingContribution).filter(
        PendingContribution.token == token
    ).first()

    if not contribution:
        return None

    # Check if expired
    if contribution.expires_at < datetime.utcnow():
        return None

    return contribution


def get_contribution_by_id(db: Session, contribution_id: int) -> PendingContribution | None:
    """
    Get contribution by ID.

    Args:
        db: Database session
        contribution_id: Contribution ID

    Returns:
        PendingContribution object if found, None otherwise
    """
    return db.query(PendingContribution).filter(
        PendingContribution.id == contribution_id
    ).first()


def update_selected_answer(
    db: Session,
    contribution_id: int,
    answer: str
) -> PendingContribution:
    """
    Update the selected answer for a contribution.

    Args:
        db: Database session
        contribution_id: Contribution ID
        answer: Selected or custom answer

    Returns:
        Updated PendingContribution object
    """
    contribution = get_contribution_by_id(db, contribution_id)
    if not contribution:
        raise ValueError(f"Contribution {contribution_id} not found")

    contribution.selected_answer = answer
    db.commit()
    db.refresh(contribution)

    return contribution


def update_payment_info(
    db: Session,
    contribution_id: int,
    stripe_session_id: str,
    amount_cents: int
) -> PendingContribution:
    """
    Update payment information for a contribution.

    Args:
        db: Database session
        contribution_id: Contribution ID
        stripe_session_id: Stripe checkout session ID
        amount_cents: Payment amount in cents

    Returns:
        Updated PendingContribution object
    """
    contribution = get_contribution_by_id(db, contribution_id)
    if not contribution:
        raise ValueError(f"Contribution {contribution_id} not found")

    contribution.stripe_session_id = stripe_session_id
    contribution.amount_cents = amount_cents
    db.commit()
    db.refresh(contribution)

    return contribution


def mark_payment_received(
    db: Session,
    stripe_session_id: str,
    payment_intent_id: str
) -> PendingContribution:
    """
    Mark a contribution as payment received.

    Args:
        db: Database session
        stripe_session_id: Stripe checkout session ID
        payment_intent_id: Stripe payment intent ID

    Returns:
        Updated PendingContribution object
    """
    contribution = db.query(PendingContribution).filter(
        PendingContribution.stripe_session_id == stripe_session_id
    ).first()

    if not contribution:
        raise ValueError(f"Contribution with session {stripe_session_id} not found")

    contribution.payment_status = 'paid'
    contribution.stripe_payment_intent = payment_intent_id
    contribution.status = 'payment_received'
    contribution.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(contribution)

    return contribution


def finalize_contribution(db: Session, contribution_id: int) -> Question:
    """
    Finalize a contribution by storing the QA pair in the database.

    For new contributions, creates a Question record.
    For improvements, updates the existing Question record.

    Args:
        db: Database session
        contribution_id: Contribution ID

    Returns:
        Created or updated Question object
    """
    contribution = get_contribution_by_id(db, contribution_id)
    if not contribution:
        raise ValueError(f"Contribution {contribution_id} not found")

    if not contribution.selected_answer:
        raise ValueError(f"Contribution {contribution_id} has no selected answer")

    if contribution.payment_status != 'paid':
        raise ValueError(f"Contribution {contribution_id} payment not received")

    # Generate embedding for the question
    embedding = get_embedding(contribution.question)

    # Check if this is an improvement or new contribution
    if contribution.improvement_of_question_id:
        # Update existing question
        question = db.query(Question).filter(
            Question.id == contribution.improvement_of_question_id
        ).first()

        if not question:
            raise ValueError(f"Question {contribution.improvement_of_question_id} not found")

        # Update with new answer and contribution amount
        question.answer = contribution.selected_answer
        question.embedding = embedding
        question.contribution_amount_cents = contribution.amount_cents
        question.created_at = datetime.utcnow()  # Update timestamp

    else:
        # Create new Question record
        question = Question(
            question=contribution.question,
            answer=contribution.selected_answer,
            embedding=embedding,
            contribution_amount_cents=contribution.amount_cents or 0
        )
        db.add(question)

    # Update contribution status
    contribution.status = 'qa_stored'
    contribution.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(question)
    db.refresh(contribution)

    return question


def mark_contribution_complete(db: Session, contribution_id: int) -> PendingContribution:
    """
    Mark a contribution as complete after bot reply is posted.

    Args:
        db: Database session
        contribution_id: Contribution ID

    Returns:
        Updated PendingContribution object
    """
    contribution = get_contribution_by_id(db, contribution_id)
    if not contribution:
        raise ValueError(f"Contribution {contribution_id} not found")

    contribution.status = 'complete'
    if not contribution.completed_at:
        contribution.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(contribution)

    return contribution
