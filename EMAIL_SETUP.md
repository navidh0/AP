# Email Configuration Setup

This document explains how to configure email functionality for the appointment booking system.

## Features Implemented

✅ **Email Confirmation on Successful Booking**
- Sends email to patient after successful appointment booking
- Includes doctor name, appointment time, and cost
- Only sends email on successful booking (not on failures)
- Works with both form-based and AJAX booking

## Email Templates

The system includes both HTML and text email templates:
- `booking/templates/booking/appointment_confirmation_email.html` - Rich HTML email
- `booking/templates/booking/appointment_confirmation_email.txt` - Plain text fallback

## Email Content

Each confirmation email includes:
- Patient name
- Doctor name and specialty
- Appointment date and time
- Appointment duration
- **Appointment fee/cost**
- Status (Confirmed)
- Additional notes (if any)
- Important reminders for patients

## Configuration

### Development (Current Setup)
The system is currently configured for development with console backend:
```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```
Emails are printed to the console for testing.

### Production Setup
To enable real email sending, update `core/settings/base.py`:

1. Uncomment the SMTP settings:
```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@appointment.com")
```

2. Comment out the console backend:
```python
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

3. Set environment variables in your `.env` file:
```bash
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourapp.com
```

### Gmail Setup
For Gmail SMTP:
1. Enable 2-factor authentication
2. Generate an App Password (not your regular password)
3. Use the App Password in `EMAIL_HOST_PASSWORD`

## Testing

Use the management command to test email functionality:
```bash
python manage.py test_email --email test@example.com
```

This will:
- Create test patient, doctor, and appointment
- Send confirmation email
- Show email content in console (development mode)

## Files Modified/Created

### New Files:
- `booking/services.py` - Email service functions
- `booking/templates/booking/appointment_confirmation_email.html` - HTML email template
- `booking/templates/booking/appointment_confirmation_email.txt` - Text email template
- `booking/management/commands/test_email.py` - Email testing command
- `EMAIL_SETUP.md` - This documentation

### Modified Files:
- `booking/views.py` - Added email sending to booking views
- `core/settings/base.py` - Added email configuration
- `.gitignore` - Added `.env.email` for email secrets
- `users/urls.py` - Fixed view name reference

## Error Handling

The email service includes proper error handling:
- Logs email sending attempts and failures
- Continues booking process even if email fails
- Shows appropriate user messages based on email status
- Uses safe email sending to prevent exceptions

## Security Notes

- Email credentials are stored in environment variables
- `.env.email` is added to `.gitignore` to prevent committing secrets
- Email sending failures don't affect the booking process
- Patient email addresses are validated before sending
