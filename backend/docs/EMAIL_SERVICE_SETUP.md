# Email Service Setup Guide

## Overview

The email service sends transactional emails for subscription events including:
- Subscription confirmations
- Tier changes
- Cancellations
- Payment failures
- Invoice receipts

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Email Configuration
EMAIL_ENABLED=true                          # Set to "false" to disable emails (console logging only)
EMAIL_PROVIDER=sendgrid                     # Options: console, sendgrid, mailgun, smtp
EMAIL_FROM=noreply@unicorncommander.ai     # From email address
EMAIL_FROM_NAME=Unicorn Commander           # From name
EMAIL_REPLY_TO=support@unicorncommander.ai # Reply-to address

# SendGrid (if using EMAIL_PROVIDER=sendgrid)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxx

# Mailgun (if using EMAIL_PROVIDER=mailgun)
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=mg.unicorncommander.ai

# SMTP (if using EMAIL_PROVIDER=smtp)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Provider Setup

### Option 1: SendGrid (Recommended)

1. **Sign up at [SendGrid](https://sendgrid.com/)**
   - Free tier: 100 emails/day
   - Paid plans available for higher volumes

2. **Create API Key**
   - Go to Settings → API Keys
   - Create new API key with "Full Access"
   - Copy the key to `SENDGRID_API_KEY`

3. **Verify Sender Identity**
   - Go to Settings → Sender Authentication
   - Verify your domain or single sender email

4. **Update .env**
   ```bash
   EMAIL_ENABLED=true
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=SG.your-api-key-here
   EMAIL_FROM=noreply@unicorncommander.ai
   ```

### Option 2: Mailgun

1. **Sign up at [Mailgun](https://www.mailgun.com/)**
   - Free tier: 5,000 emails/month for 3 months

2. **Get API Credentials**
   - Go to Dashboard → API Keys
   - Copy your Private API key
   - Note your sending domain

3. **Update .env**
   ```bash
   EMAIL_ENABLED=true
   EMAIL_PROVIDER=mailgun
   MAILGUN_API_KEY=key-your-api-key-here
   MAILGUN_DOMAIN=mg.yourdomain.com
   EMAIL_FROM=noreply@mg.yourdomain.com
   ```

### Option 3: SMTP (Gmail, Office365, etc.)

1. **Gmail Setup**
   - Enable 2-factor authentication
   - Create App Password: Account → Security → App Passwords
   - Use app password, not your regular password

2. **Update .env**
   ```bash
   EMAIL_ENABLED=true
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAIL_FROM=your-email@gmail.com
   ```

### Option 4: Console (Development)

For development/testing, use console logging:

```bash
EMAIL_ENABLED=true
EMAIL_PROVIDER=console
```

Emails will be logged to console instead of sent.

## Email Templates

The service includes pre-built HTML email templates for:

### 1. Subscription Confirmation
Sent when: `checkout.session.completed` webhook received

Content:
- Welcome message
- Tier details
- Amount charged
- Next billing date
- Feature list
- Dashboard link

### 2. Subscription Updated
Sent when: `customer.subscription.updated` webhook received

Content:
- Tier change notification (old → new)
- New pricing
- Updated features

### 3. Subscription Canceled
Sent when: `customer.subscription.deleted` webhook received

Content:
- Cancellation confirmation
- Access end date
- Downgrade notice
- Reactivation link

### 4. Payment Failed
Sent when: `invoice.payment_failed` webhook received

Content:
- Payment failure alert
- Amount due
- Failure reason
- Update payment method link

### 5. Invoice Receipt
Sent when: `invoice.payment_succeeded` webhook received

Content:
- Payment receipt
- Invoice number
- Amount paid
- Download invoice link

## Testing

### Test Email Sending

1. **Console Mode (No Emails Sent)**
   ```bash
   EMAIL_ENABLED=true
   EMAIL_PROVIDER=console
   ```
   Check logs: `docker logs unicorn-ops-center | grep EMAIL`

2. **Test with Stripe Webhook**
   - Use Stripe CLI for local testing:
     ```bash
     stripe listen --forward-to localhost:8084/api/v1/stripe/webhook
     stripe trigger checkout.session.completed
     ```

3. **Manual Test**
   Create test endpoint (add to `server.py`):
   ```python
   @app.get("/test-email")
   async def test_email():
       await email_service.send_subscription_confirmation(
           to="test@example.com",
           tier="professional",
           amount=49.00,
           period_end="January 15, 2026"
       )
       return {"message": "Test email sent"}
   ```

### Verify Email Delivery

1. **Check logs**
   ```bash
   docker logs unicorn-ops-center | grep "Email sent successfully"
   ```

2. **Check spam folder** - First emails from new sender may go to spam

3. **SendGrid Dashboard** - View email activity and delivery status

## Troubleshooting

### Emails Not Sending

1. **Check EMAIL_ENABLED**
   ```bash
   docker exec unicorn-ops-center printenv EMAIL_ENABLED
   ```

2. **Check logs for errors**
   ```bash
   docker logs unicorn-ops-center | grep -E "email|EMAIL"
   ```

3. **Verify API credentials**
   - Test SendGrid/Mailgun key in their dashboards
   - Check SMTP credentials work with email client

### Emails Going to Spam

1. **Verify sender domain**
   - Add SPF, DKIM, DMARC records
   - Use domain authentication in SendGrid/Mailgun

2. **Warm up sender reputation**
   - Start with small volumes
   - Gradually increase over time

3. **Improve email content**
   - Avoid spam trigger words
   - Include unsubscribe link
   - Use proper HTML structure

### Development Errors

1. **Import error: aiosmtplib**
   ```bash
   docker exec unicorn-ops-center pip install aiosmtplib
   ```

2. **Redis connection issues**
   - Session invalidation requires Redis
   - Check Redis is running: `docker ps | grep redis`

## Best Practices

### Production Checklist

- [ ] Use verified sender domain (not free email)
- [ ] Set up SPF/DKIM/DMARC DNS records
- [ ] Enable EMAIL_ENABLED=true
- [ ] Use production API keys (not test keys)
- [ ] Monitor email delivery rates
- [ ] Set up error alerting for failed emails
- [ ] Test all email templates before launch
- [ ] Comply with email regulations (CAN-SPAM, GDPR)

### Security

- [ ] Store API keys in environment variables (not code)
- [ ] Use read-only filesystem for container
- [ ] Rotate API keys periodically
- [ ] Monitor for unauthorized use
- [ ] Rate limit email sending
- [ ] Validate email addresses before sending

### Monitoring

Track these metrics:
- Emails sent per day
- Delivery rate
- Bounce rate
- Spam complaint rate
- Open rate (if tracking enabled)

## Cost Estimates

### SendGrid
- Free: 100 emails/day
- Essentials: $19.95/mo (50,000 emails)
- Pro: $89.95/mo (100,000 emails)

### Mailgun
- Free trial: 5,000 emails/3 months
- Pay as you go: $0.80/1,000 emails
- Foundation: $35/mo (50,000 emails)

### SMTP
- Gmail: Free (limited to ~500/day)
- Office365: Included with subscription
- Custom SMTP server: Self-hosted cost

## Support

For issues:
1. Check logs: `docker logs unicorn-ops-center`
2. Verify configuration in `.env`
3. Test with console provider first
4. Check provider dashboards for errors
5. Contact support@unicorncommander.ai

## Advanced Configuration

### Custom Email Templates

To customize email templates, edit methods in `email_service.py`:
- `send_subscription_confirmation()`
- `send_subscription_updated()`
- `send_subscription_canceled()`
- `send_payment_failed()`
- `send_invoice()`

### Adding New Email Types

1. Create template method in `EmailService` class
2. Add webhook handler in `server.py`
3. Call email method from webhook
4. Test thoroughly

### Email Analytics

For open/click tracking, integrate with:
- SendGrid Event Webhook
- Mailgun Tracking API
- Custom pixel tracking

## Related Documentation

- [Stripe Webhook Guide](./STRIPE_WEBHOOK_GUIDE.md)
- [Database Schema](./DATABASE_SCHEMA.md)
- [Session Management](./SESSION_MANAGEMENT.md)
