# Stripe Webhook Implementation

## Overview
Secure Stripe webhook handler that is the **ONLY automatic authority** for granting premium access. All subscription state changes must come through Stripe webhooks.

## Security Features

### Signature Verification
- Reads raw request body (required for signature verification)
- Verifies webhook signature using `STRIPE_WEBHOOK_SECRET`
- Rejects invalid signatures with `400 Bad Request`
- Prevents unauthorized access to subscription endpoints

### Idempotent Logic
All event handlers are idempotent - safe to receive the same event multiple times:
- **checkout.session.completed**: Only updates if user doesn't already have PREMIUM/ACTIVE
- **invoice.payment_succeeded**: Always safe to update expiration date
- **customer.subscription.deleted**: Only updates if user doesn't already have FREE/INACTIVE

## Endpoint

### POST /subscriptions/webhook

**Authentication:** None (Stripe webhook signature verification)

**Headers Required:**
- `stripe-signature`: Stripe webhook signature

**Request Body:** Raw Stripe event JSON

**Response:** `200 OK` (always returns 200 to acknowledge receipt, even on errors)

## Events Handled

### 1. checkout.session.completed

**When:** User completes checkout and payment succeeds

**Actions:**
- Extracts `user_id` from checkout session metadata
- Sets `subscription_plan = "PREMIUM"`
- Sets `subscription_status = "ACTIVE"`
- Sets `stripe_customer_id` from customer ID
- Sets `subscription_expires_at` from subscription period end

**Idempotency:** Skips if user already has PREMIUM/ACTIVE (but still updates `stripe_customer_id` if missing)

**Metadata Required:**
When creating checkout session, include:
```python
metadata = {
    "user_id": user.id
}
```

### 2. invoice.payment_succeeded

**When:** Subscription payment succeeds (recurring billing)

**Actions:**
- Finds user by `stripe_customer_id`
- Updates `subscription_expires_at` from subscription period end
- Refreshes subscription expiration date

**Idempotency:** Always safe to update expiration date

### 3. customer.subscription.deleted

**When:** Subscription is canceled or deleted

**Actions:**
- Finds user by `stripe_customer_id`
- Sets `subscription_plan = "FREE"`
- Sets `subscription_status = "INACTIVE"`
- Sets `subscription_expires_at = NULL`

**Idempotency:** Skips if user already has FREE/INACTIVE

## Configuration

### Environment Variables

Add to `.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...  # Your Stripe secret key (test mode)
STRIPE_WEBHOOK_SECRET=whsec_...  # Webhook signing secret from Stripe Dashboard
```

### Getting Webhook Secret

1. Go to Stripe Dashboard → Developers → Webhooks
2. Create or select your webhook endpoint
3. Copy the "Signing secret" (starts with `whsec_`)
4. Add to `.env` as `STRIPE_WEBHOOK_SECRET`

## Database Compatibility

- **SQLite**: Fully compatible
- **PostgreSQL**: Fully compatible
- Uses standard SQLAlchemy operations

## Error Handling

### Invalid Signature
- Returns `400 Bad Request`
- Logs error
- Does not process event

### Missing Configuration
- Returns `500 Internal Server Error` if `STRIPE_WEBHOOK_SECRET` not set
- Logs error

### Processing Errors
- Logs error with full traceback
- Returns `200 OK` to prevent Stripe retries
- Errors are logged for manual investigation

### Missing Data
- Logs warning for missing required fields
- Returns `200 OK` (event acknowledged)
- Does not crash on missing optional data

## Testing

### Using Stripe CLI

1. **Install Stripe CLI:**
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe
   
   # Windows
   # Download from https://github.com/stripe/stripe-cli/releases
   ```

2. **Login to Stripe:**
   ```bash
   stripe login
   ```

3. **Forward webhooks to local server:**
   ```bash
   stripe listen --forward-to localhost:8000/subscriptions/webhook
   ```

4. **Trigger test events:**
   ```bash
   # Test checkout completion
   stripe trigger checkout.session.completed
   
   # Test payment succeeded
   stripe trigger invoice.payment_succeeded
   
   # Test subscription deletion
   stripe trigger customer.subscription.deleted
   ```

### Manual Testing

1. **Set up webhook in Stripe Dashboard:**
   - URL: `https://your-domain.com/subscriptions/webhook`
   - Events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`

2. **Test with curl:**
   ```bash
   # Note: This requires a valid signature, use Stripe CLI instead
   curl -X POST http://localhost:8000/subscriptions/webhook \
     -H "stripe-signature: ..." \
     -d @test_event.json
   ```

## Implementation Details

### Files Created/Modified

1. **`app/modules/subscriptions/routers.py`**
   - Webhook endpoint handler
   - Signature verification
   - Event handlers for all three events

2. **`app/core/config.py`**
   - Added `STRIPE_WEBHOOK_SECRET` configuration

3. **`app/main.py`**
   - Registered subscriptions router at `/subscriptions`

### Security Considerations

1. **Signature Verification:**
   - Uses Stripe's official `stripe.Webhook.construct_event()` method
   - Verifies HMAC signature using webhook secret
   - Prevents replay attacks and unauthorized access

2. **Raw Body Reading:**
   - FastAPI's `Request.body()` is used to get raw bytes
   - Required for signature verification (can't use parsed JSON)

3. **Error Responses:**
   - Invalid signatures return 400 (client error)
   - Processing errors return 200 (to prevent retries)
   - All errors are logged for investigation

### Idempotency Strategy

Instead of tracking event IDs in a database table, we use state-based idempotency:

1. **checkout.session.completed:**
   - Check if user already has PREMIUM/ACTIVE
   - If yes, skip update (but still update `stripe_customer_id` if missing)

2. **invoice.payment_succeeded:**
   - Always safe to update expiration date
   - No state check needed

3. **customer.subscription.deleted:**
   - Check if user already has FREE/INACTIVE
   - If yes, skip update

This approach is simpler and doesn't require additional database tables.

## Integration with Frontend

When creating a checkout session, include user_id in metadata:

```javascript
const session = await stripe.checkout.sessions.create({
  customer_email: user.email,
  payment_method_types: ['card'],
  line_items: [{
    price: 'price_...',  // Your Stripe price ID
    quantity: 1,
  }],
  mode: 'subscription',
  success_url: 'https://your-app.com/success',
  cancel_url: 'https://your-app.com/cancel',
  metadata: {
    user_id: user.id  // Required for webhook to identify user
  }
});
```

## Monitoring

### Logs to Monitor

- `Received Stripe webhook event: {event_type}` - Successful event receipt
- `Invalid signature in Stripe webhook` - Security issue
- `User {user_id} not found` - Integration issue
- `Granted premium access to user {user_id}` - Successful grant
- `Revoked premium access from user {user_id}` - Successful revocation

### Stripe Dashboard

Monitor webhook delivery in:
- Stripe Dashboard → Developers → Webhooks
- Check for failed deliveries
- Review event logs

## Notes

- **No frontend changes required**: Webhook works independently
- **Stripe is the authority**: Only webhooks can automatically grant premium
- **Admin endpoints still work**: Manual admin grants still function
- **Test mode supported**: Works with Stripe test mode
- **Production ready**: Includes all security best practices





