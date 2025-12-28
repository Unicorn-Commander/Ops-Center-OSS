# UC-1 Pro Email Service

Production-ready email notification system for UC-1 Pro Operations Center with Office 365 SMTP integration.

## Features

- **Office 365 SMTP Integration** with TLS encryption
- **Beautiful HTML Email Templates** with UC-1 Pro branding
- **Async Email Sending** for non-blocking operations
- **Retry Logic** with exponential backoff (3 attempts)
- **HTML + Plain Text** fallback for all emails
- **Attachment Support** for invoices and documents
- **Template Rendering** with Jinja2
- **Comprehensive Error Logging**

## Quick Start

### 1. Install Dependencies

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center/backend
pip install -r requirements.txt
```

### 2. Configure Email

Copy example configuration:
```bash
cp .env.email.example .env.email
```

Edit `.env.email` with your Office 365 credentials:
```env
SMTP_USER=noreply@your-domain.com
SMTP_PASSWORD=your-app-password-here
FROM_EMAIL=noreply@your-domain.com
```

Or add directly to your main `.env` file.

### 3. Test Configuration

```bash
python3 email_service.py
```

This will:
- Display your configuration
- Prompt for test recipient email
- Send welcome email test

## Email Templates

All templates located in `email_templates/`:

### 1. Welcome Email (`welcome.html`)
Send to new users after registration:
```python
await email_service.send_welcome_email(
    to="user@example.com",
    username="johndoe"
)
```

### 2. Password Reset (`password_reset.html`)
Send password reset link with optional temporary password:
```python
await email_service.send_password_reset(
    to="user@example.com",
    reset_link="https://your-domain.com/reset?token=xxx",
    temporary_password="Temp123!"  # Optional
)
```

### 3. Subscription Confirmed (`subscription_confirmed.html`)
Notify user of successful subscription:
```python
await email_service.send_subscription_confirmation(
    to="user@example.com",
    tier="Professional",
    amount=49.00
)
```

### 4. Subscription Canceled (`subscription_canceled.html`)
Notify user of subscription cancellation:
```python
await email_service.send_subscription_canceled(
    to="user@example.com",
    tier="Professional",
    end_date="October 15, 2025"
)
```

### 5. Payment Failed (`payment_failed.html`)
Alert user to payment issues:
```python
await email_service.send_payment_failed(
    to="user@example.com",
    amount=49.00,
    reason="Insufficient funds"
)
```

### 6. Invoice (`invoice.html`)
Send invoice with optional PDF attachment:
```python
invoice_data = {
    "invoice_number": "INV-2025-001",
    "date": "October 8, 2025",
    "items": [
        {"description": "UC-1 Pro Professional", "amount": 49.00}
    ],
    "subtotal": 49.00,
    "tax": 0.00,
    "total": 49.00,
    "billing_period": "October 2025"
}

# Optional: Generate PDF attachment
pdf_bytes = generate_invoice_pdf(invoice_data)

await email_service.send_invoice(
    to="user@example.com",
    invoice_data=invoice_data,
    pdf_attachment=pdf_bytes  # Optional
)
```

### 7. Admin Alert (`admin_alert.html`)
Send system alerts to administrators:
```python
await email_service.send_admin_alert(
    to="admin@your-domain.com",
    subject="High Memory Usage",
    message="System memory usage exceeded 90%"
)
```

## Usage in Your Application

### Import and Initialize

```python
from email_service import EmailService

email_service = EmailService()
```

### Check Configuration

```python
if email_service.is_configured:
    # Safe to send emails
    await email_service.send_welcome_email(...)
else:
    logger.warning("Email service not configured")
```

### Error Handling

All email methods return `bool`:
- `True` = Email sent successfully
- `False` = Failed to send after retries

```python
success = await email_service.send_welcome_email(
    to="user@example.com",
    username="johndoe"
)

if success:
    logger.info("Welcome email sent")
else:
    logger.error("Failed to send welcome email")
```

### Integration with FastAPI

```python
from fastapi import BackgroundTasks
from email_service import EmailService

email_service = EmailService()

@app.post("/api/v1/user/register")
async def register_user(
    user_data: UserRegistration,
    background_tasks: BackgroundTasks
):
    # Create user...

    # Queue email in background
    background_tasks.add_task(
        email_service.send_welcome_email,
        to=user_data.email,
        username=user_data.username
    )

    return {"status": "success"}
```

### Integration with Stripe Webhooks

```python
@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    payload = await request.body()
    event = stripe.Webhook.construct_event(...)

    if event.type == "invoice.payment_succeeded":
        customer = event.data.object.customer
        amount = event.data.object.amount_paid / 100

        # Send confirmation email
        background_tasks.add_task(
            email_service.send_subscription_confirmation,
            to=customer.email,
            tier="Professional",
            amount=amount
        )

    elif event.type == "invoice.payment_failed":
        # Send payment failed notification
        background_tasks.add_task(
            email_service.send_payment_failed,
            to=customer.email,
            amount=amount,
            reason=event.data.object.failure_message
        )
```

## Office 365 Setup

### 1. Create Email Account

Create a dedicated mailbox (e.g., `noreply@your-domain.com`) in your Microsoft 365 Admin Center.

### 2. Enable SMTP Authentication

1. Go to Microsoft 365 Admin Center
2. Settings → Mail → Security & Privacy
3. Enable "Authenticated SMTP"

### 3. Generate App Password

**IMPORTANT**: Use app-specific password, NOT your regular password!

1. Visit: https://account.live.com/proofs/AppPassword
2. Click "Create a new app password"
3. Copy the password (shown once)
4. Use as `SMTP_PASSWORD` in your `.env`

### 4. Configure Sender Domain (Optional)

For better deliverability:
1. Add SPF record: `v=spf1 include:spf.protection.outlook.com ~all`
2. Add DKIM signing in Exchange Admin Center
3. Add DMARC policy: `v=DMARC1; p=quarantine; rua=mailto:admin@your-domain.com`

## Alternative Email Providers

### Gmail

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

Setup:
1. Enable 2-Factor Authentication
2. Visit: https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"

### SendGrid

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxxxxxxxxxxx
```

Setup:
1. Sign up at https://sendgrid.com
2. Create API key with "Mail Send" permission
3. Verify sender identity
4. Use "apikey" as username, API key as password

## Template Customization

Templates are in `email_templates/` directory. Edit HTML files to customize:

### Branding
- Logo: Change 🦄 emoji to image URL
- Colors: Purple (#a855f7) and gold (#fbbf24)
- Fonts: Default is system font stack

### Add New Template

1. Create `email_templates/my_template.html`
2. Add method to `EmailService` class:

```python
async def send_my_email(self, to: str, data: dict) -> bool:
    context = {
        'data': data,
        'year': datetime.now().year
    }

    html_body = self._render_template('my_template.html', context)

    return await self._send_email(
        to=to,
        subject="My Subject",
        html_body=html_body
    )
```

## Testing

### Run Full Test Suite

```bash
python3 email_service.py
```

### Send Test Email to Specific Address

```bash
export SMTP_USER=noreply@your-domain.com
export SMTP_PASSWORD=your-app-password
export FROM_EMAIL=noreply@your-domain.com

python3 -c "
import asyncio
from email_service import EmailService

async def test():
    service = EmailService()
    await service.send_welcome_email('your@email.com', 'TestUser')

asyncio.run(test())
"
```

### Check Logs

```bash
# View email service logs
docker logs unicorn-ops-center | grep -E "Email|SMTP"
```

## Troubleshooting

### Issue: "Email service not configured"
**Solution**: Set `SMTP_USER` and `SMTP_PASSWORD` environment variables

### Issue: "aiosmtplib not installed"
**Solution**: `pip install aiosmtplib`

### Issue: "Authentication failed"
**Solution**:
- Use app-specific password, not regular password
- Verify SMTP authentication enabled in Office 365
- Check username is full email address

### Issue: "Connection timeout"
**Solution**:
- Verify port 587 not blocked by firewall
- Try port 25 or 465 as alternative
- Check SMTP_HOST is correct

### Issue: "Email sent but not received"
**Solution**:
- Check spam/junk folder
- Verify sender domain reputation
- Add SPF, DKIM, DMARC records
- Use email testing tools like mail-tester.com

### Issue: "Template rendering error"
**Solution**:
- Check template file exists in `email_templates/`
- Verify all variables provided in context
- Check Jinja2 syntax in template

## Production Deployment

### Docker Integration

Add to `docker-compose.yml`:

```yaml
services:
  ops-center:
    environment:
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - FROM_EMAIL=${FROM_EMAIL}
      - FROM_NAME=${FROM_NAME}
      - APP_URL=${APP_URL}
```

### Environment Variables

Create `.env.email` or add to main `.env`:

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=noreply@your-domain.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
FROM_EMAIL=noreply@your-domain.com
FROM_NAME=UC-1 Pro Ops Center
APP_URL=https://your-domain.com
```

### Restart Services

```bash
docker-compose restart unicorn-ops-center
```

## Security Best Practices

1. **Never commit credentials** to Git
2. **Use app-specific passwords** instead of account passwords
3. **Enable TLS** for SMTP connections (port 587)
4. **Rotate passwords** regularly
5. **Use environment variables** for configuration
6. **Monitor email logs** for suspicious activity
7. **Implement rate limiting** to prevent abuse
8. **Validate recipient addresses** before sending

## Rate Limits

### Office 365 Limits
- **10,000 recipients per day** (Microsoft 365 Business)
- **30 messages per minute**
- **500 recipients per message**

### Recommended Limits
- Implement your own rate limiting
- Queue emails for batch processing
- Use background tasks for email sending

## Support

For issues or questions:
- Check logs: `docker logs unicorn-ops-center`
- Review configuration: `python3 email_service.py`
- Test SMTP connection: Use telnet or openssl
- Contact support: admin@your-domain.com

## License

Part of UC-1 Pro Operations Center
© 2025 Magic Unicorn Unconventional Technology & Stuff Inc
