from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe

from app.core.database import get_db
from app.core.config import settings
from app.services.contribution_service import (
    get_contribution_by_token,
    get_contribution_by_id,
    update_selected_answer,
    update_payment_info,
    mark_payment_received,
    finalize_contribution,
    mark_contribution_complete
)
from app.services.stripe_service import (
    create_checkout_session,
    verify_webhook_signature
)
from app.bot.factory import get_worker_by_platform

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


class CreateCheckoutRequest(BaseModel):
    """Request model for creating checkout session."""
    answer: str
    amount_cents: int


@router.get("/checkout/{token}", response_class=HTMLResponse)
async def show_checkout_page(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Show checkout page with question, suggestions, and payment form.

    Args:
        token: Secure contribution token
        request: FastAPI request object
        db: Database session

    Returns:
        HTML page with checkout form
    """
    contribution = get_contribution_by_token(db, token)

    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found or expired")

    # Check if this is an improvement contribution
    is_improvement = contribution.improvement_of_question_id is not None

    return templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "contribution_id": contribution.id,
            "question": contribution.question,
            "suggested_answers": contribution.suggested_answers,
            "token": token,
            "is_improvement": is_improvement,
            "existing_answer": contribution.existing_answer if is_improvement else None,
            "minimum_amount_cents": contribution.minimum_amount_cents,
            "minimum_amount_dollars": contribution.minimum_amount_cents / 100
        }
    )


@router.post("/api/contributions/{contribution_id}/create-checkout")
async def create_checkout(
    contribution_id: int,
    data: CreateCheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Create Stripe checkout session for a contribution.

    Args:
        contribution_id: Contribution ID
        data: Answer and payment amount
        db: Database session

    Returns:
        Checkout URL
    """
    # Validate contribution exists
    contribution = get_contribution_by_id(db, contribution_id)
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    # Validate answer
    if len(data.answer.strip()) < 10:
        raise HTTPException(status_code=400, detail="Answer must be at least 10 characters")
    if len(data.answer.strip()) > 1000:
        raise HTTPException(status_code=400, detail="Answer must be less than 1000 characters")

    # Validate amount (check against contribution's minimum, which may be higher for improvements)
    minimum_required = contribution.minimum_amount_cents
    if data.amount_cents < minimum_required:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum contribution is ${minimum_required / 100:.2f}"
        )
    if data.amount_cents > 1000000:  # $10,000 max
        raise HTTPException(status_code=400, detail="Amount exceeds maximum")

    # Update selected answer
    update_selected_answer(db, contribution_id, data.answer.strip())

    # Create Stripe checkout session
    try:
        success_url = f"{settings.base_url}/checkout/success/{contribution.token}"
        cancel_url = f"{settings.base_url}/checkout/cancel/{contribution.token}"

        session = create_checkout_session(
            contribution_id=contribution_id,
            amount_cents=data.amount_cents,
            success_url=success_url,
            cancel_url=cancel_url,
            question=contribution.question
        )

        # Update contribution with payment info
        update_payment_info(db, contribution_id, session.id, data.amount_cents)

        return {
            "checkout_url": session.url,
            "session_id": session.id
        }

    except Exception as e:
        print(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.get("/checkout/success/{token}", response_class=HTMLResponse)
async def show_success_page(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Show success page after payment completion.

    Args:
        token: Secure contribution token
        request: FastAPI request object
        db: Database session

    Returns:
        HTML success page
    """
    contribution = get_contribution_by_token(db, token)

    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "question": contribution.question,
            "answer": contribution.selected_answer,
            "amount": f"{contribution.amount_cents / 100:.2f}" if contribution.amount_cents else "0.00"
        }
    )


@router.get("/checkout/cancel/{token}", response_class=HTMLResponse)
async def show_cancel_page(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Show cancellation page if payment was cancelled.

    Args:
        token: Secure contribution token
        request: FastAPI request object
        db: Database session

    Returns:
        HTML cancel page
    """
    contribution = get_contribution_by_token(db, token)

    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    return templates.TemplateResponse(
        "cancel.html",
        {
            "request": request,
            "token": token
        }
    )


@router.post("/api/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.

    This endpoint receives notifications from Stripe when payments are completed,
    failed, or other events occur.

    Args:
        request: FastAPI request object with webhook payload
        db: Database session

    Returns:
        Success status
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        # Verify webhook signature
        event = verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        print(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except stripe.error.SignatureVerificationError as e:
        print(f"Stripe signature verification error: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        try:
            # Mark payment as received
            contribution = mark_payment_received(
                db,
                session["id"],
                session.get("payment_intent", "")
            )

            print(f"Payment received for contribution {contribution.id}")

            # Finalize contribution (store QA pair)
            question_obj = finalize_contribution(db, contribution.id)

            print(f"QA pair stored: Question ID {question_obj.id}")

            # Post bot reply
            try:
                worker = get_worker_by_platform(contribution.platform)

                thank_you_message = (
                    f"Thank you for teaching me! 🎉\n\n"
                    f"Your answer has been added to my knowledge base and will help me respond "
                    f"to similar questions in the future."
                )

                if worker.post_reply(contribution.mention_id, thank_you_message):
                    print(f"Thank you reply posted for contribution {contribution.id}")
                    # Mark as complete
                    mark_contribution_complete(db, contribution.id)
                else:
                    print(f"Failed to post reply for contribution {contribution.id}")
                    # Still mark as complete since QA is stored
                    mark_contribution_complete(db, contribution.id)

            except Exception as e:
                print(f"Error posting bot reply: {e}")
                # Still mark as complete since QA is stored
                mark_contribution_complete(db, contribution.id)

        except Exception as e:
            print(f"Error processing webhook: {e}")
            # Don't raise exception - we don't want Stripe to retry if it's a processing error
            # Just log it and return success

    return {"status": "success"}
