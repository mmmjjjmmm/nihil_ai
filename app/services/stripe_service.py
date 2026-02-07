import stripe
from app.core.config import settings

# Initialize Stripe with API key
stripe.api_key = settings.stripe_api_key


def create_checkout_session(
    contribution_id: int,
    amount_cents: int,
    success_url: str,
    cancel_url: str,
    question: str
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout Session for a contribution.

    Args:
        contribution_id: Database ID of the contribution
        amount_cents: Payment amount in cents (user-chosen)
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect after cancelled payment
        question: Question text for payment description

    Returns:
        Stripe checkout session object
    """
    # Truncate question for description
    description = f"QA contribution: {question[:100]}"
    if len(question) > 100:
        description += "..."

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Bot Training Contribution',
                    'description': description,
                },
                'unit_amount': amount_cents,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            'contribution_id': str(contribution_id),
        },
        payment_intent_data={
            'description': description
        }
    )

    return session


def verify_webhook_signature(payload: bytes, signature: str) -> dict:
    """
    Verify Stripe webhook signature and parse event.

    Args:
        payload: Raw webhook payload
        signature: Stripe signature header value

    Returns:
        Parsed event object

    Raises:
        ValueError: If signature verification fails
        stripe.error.SignatureVerificationError: If signature is invalid
    """
    if not settings.stripe_webhook_secret:
        raise ValueError("Stripe webhook secret not configured")

    event = stripe.Webhook.construct_event(
        payload, signature, settings.stripe_webhook_secret
    )

    return event


def get_checkout_session(session_id: str) -> stripe.checkout.Session:
    """
    Retrieve a checkout session from Stripe.

    Args:
        session_id: Stripe checkout session ID

    Returns:
        Stripe checkout session object
    """
    return stripe.checkout.Session.retrieve(session_id)
