"""Stripe webhook router"""
import logging
import os
from fastapi import Depends
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import stripe
from app.services.auth_dependency import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.modules.auth.models import User
from app.modules.auth.constants import (
    SUBSCRIPTION_PLAN_FREE,
    SUBSCRIPTION_PLAN_PREMIUM,
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_INACTIVE
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Subscriptions"])

# Initialize Stripe (test mode)
# Will be set from settings if available

@router.post("/create-checkout-session")
def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout Session for PREMIUM subscription.
    This endpoint does NOT grant premium access directly.
    Stripe webhooks are the only authority.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe secret key not configured"
        )
    
    if not settings.STRIPE_PRICE_PREMIUM:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe price ID not configured"
        )

    # Set Stripe API key
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        # Create Stripe customer if missing
        customer_id = current_user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)}
            )
            customer_id = customer.id
            # Update user with customer ID
            try:
                current_user.stripe_customer_id = customer_id
                db.commit()
                db.refresh(current_user)
            except Exception as e:
                logger.warning(f"Failed to save stripe_customer_id: {e}")
                db.rollback()

        # Create Checkout Session
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[
                {
                    "price": settings.STRIPE_PRICE_PREMIUM,
                    "quantity": 1,
                }
            ],
            success_url=f"{settings.FRONTEND_URL}/billing/success",
            cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
            metadata={
                "user_id": str(current_user.id)
            },
        )

        return {"url": checkout_session.url}

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    This endpoint is the ONLY automatic authority for granting premium access.
    All subscription state changes must come through Stripe webhooks.
    
    Security:
    - Verifies webhook signature using STRIPE_WEBHOOK_SECRET
    - Rejects invalid signatures with 400 error
    
    Events handled:
    - checkout.session.completed: Grant premium access
    - invoice.payment_succeeded: Refresh subscription expiration
    - customer.subscription.deleted: Revoke premium access
    
    Idempotent: Safe to receive the same event multiple times.
    """
    # Get raw request body for signature verification
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        logger.warning("Stripe webhook called without signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured"
        )
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            body,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload in Stripe webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature in Stripe webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    # Handle the event
    event_type = event["type"]
    event_id = event["id"]
    
    logger.info(f"Received Stripe webhook event: {event_type} (id: {event_id})")
    
    try:
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(event, db)
        elif event_type == "invoice.payment_succeeded":
            await handle_invoice_payment_succeeded(event, db)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event, db)
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        # Return 200 to acknowledge receipt
        return Response(status_code=200)
    
    except Exception as e:
        logger.error(f"Error processing Stripe webhook event {event_id}: {e}", exc_info=True)
        # Still return 200 to prevent Stripe from retrying
        # Log the error for manual investigation
        return Response(status_code=200)


async def handle_checkout_completed(event: dict, db: Session):
    """
    Handle checkout.session.completed event.
    
    Grants premium access to user:
    - subscription_plan = "PREMIUM"
    - subscription_status = "ACTIVE"
    - stripe_customer_id = customer ID
    - subscription_expires_at = period end from subscription
    
    Idempotent: Only updates if user doesn't already have PREMIUM/ACTIVE.
    """
    session = event["data"]["object"]
    customer_id = session.get("customer")
    
    if not customer_id:
        logger.warning("checkout.session.completed event missing customer ID")
        return
    
    # Get user_id from metadata (should be set when creating checkout session)
    user_id = session.get("metadata", {}).get("user_id")
    
    if not user_id:
        logger.warning(f"checkout.session.completed event missing user_id in metadata for customer {customer_id}")
        return
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"User {user_id} not found for checkout session {session.get('id')}")
        return
    
    # Idempotency check: Skip if already has PREMIUM and ACTIVE
    if user.subscription_plan == SUBSCRIPTION_PLAN_PREMIUM and user.subscription_status == SUBSCRIPTION_STATUS_ACTIVE:
        logger.info(f"User {user_id} already has PREMIUM/ACTIVE, skipping checkout completion")
        # Still update stripe_customer_id if missing
        if not user.stripe_customer_id:
            user.stripe_customer_id = customer_id
            db.commit()
        return
    
    # Get subscription to get period end
    subscription_id = session.get("subscription")
    expires_at = None
    
    if subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            period_end = subscription.get("current_period_end")
            if period_end:
                expires_at = datetime.fromtimestamp(period_end, tz=timezone.utc)
        except Exception as e:
            logger.warning(f"Could not retrieve subscription {subscription_id}: {e}")
    
    # Update user
    user.subscription_plan = SUBSCRIPTION_PLAN_PREMIUM
    user.subscription_status = SUBSCRIPTION_STATUS_ACTIVE
    user.stripe_customer_id = customer_id
    user.subscription_expires_at = expires_at
    user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Granted premium access to user {user_id} via checkout.session.completed (expires: {expires_at})")


async def handle_invoice_payment_succeeded(event: dict, db: Session):
    """
    Handle invoice.payment_succeeded event.
    
    Refreshes subscription_expires_at from the subscription period end.
    
    Idempotent: Always safe to update expiration date.
    """
    invoice = event["data"]["object"]
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")
    
    if not customer_id:
        logger.warning("invoice.payment_succeeded event missing customer ID")
        return
    
    # Find user by stripe_customer_id
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.warning(f"User not found for Stripe customer {customer_id}")
        return
    
    # Get subscription to get period end
    expires_at = None
    if subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            period_end = subscription.get("current_period_end")
            if period_end:
                expires_at = datetime.fromtimestamp(period_end, tz=timezone.utc)
        except Exception as e:
            logger.warning(f"Could not retrieve subscription {subscription_id}: {e}")
    
    # Update expiration date
    if expires_at:
        user.subscription_expires_at = expires_at
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated subscription expiration for user {user.id} to {expires_at}")


async def handle_subscription_deleted(event: dict, db: Session):
    """
    Handle customer.subscription.deleted event.
    
    Revokes premium access:
    - subscription_plan = "FREE"
    - subscription_status = "INACTIVE"
    - subscription_expires_at = NULL
    
    Idempotent: Only updates if user doesn't already have FREE/INACTIVE.
    """
    subscription = event["data"]["object"]
    customer_id = subscription.get("customer")
    
    if not customer_id:
        logger.warning("customer.subscription.deleted event missing customer ID")
        return
    
    # Find user by stripe_customer_id
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.warning(f"User not found for Stripe customer {customer_id}")
        return
    
    # Idempotency check: Skip if already has FREE and INACTIVE
    if user.subscription_plan == SUBSCRIPTION_PLAN_FREE and user.subscription_status == SUBSCRIPTION_STATUS_INACTIVE:
        logger.info(f"User {user.id} already has FREE/INACTIVE, skipping subscription deletion")
        return
    
    # Revoke premium access
    user.subscription_plan = SUBSCRIPTION_PLAN_FREE
    user.subscription_status = SUBSCRIPTION_STATUS_INACTIVE
    user.subscription_expires_at = None
    user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Revoked premium access from user {user.id} via customer.subscription.deleted")
