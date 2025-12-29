"""
Django signals for subscriber automation.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import timedelta

from .models import SubscriberRequest
from .google_api_utils import (
    create_subscriber_folder,
    log_to_spreadsheet,
    PAYMENT_AMOUNTS
)


@receiver(post_save, sender=SubscriberRequest)
def handle_paid_subscriber_request(sender, instance, created, **kwargs):
    """
    Automate Google Drive folder creation and payment email for paid subscribers.

    Triggered when a SubscriberRequest is created with free_waiver=False.
    """
    # Only trigger for new requests with paid subscription
    if not created or instance.free_waiver:
        return

    # Prevent duplicate triggers
    if hasattr(instance, '_automation_done'):
        return

    instance._automation_done = True

    # Step 1: Create Google Drive folder
    folder_url = create_subscriber_folder(instance)

    if not folder_url:
        print(f"Warning: Failed to create Google Drive folder for {instance.email}")
        # TODO: Send notification to admin about failure
        # For now, we'll continue with email even if folder creation fails

    # Step 2: Log to Google Sheets
    log_success = log_to_spreadsheet(instance, folder_url)

    if not log_success:
        print(f"Warning: Failed to log to Google Sheets for {instance.email}")
        # TODO: Send notification to admin about failure

    # Step 3: Send payment instructions email
    send_payment_instructions_email(instance, folder_url)


def send_payment_instructions_email(subscriber_request, folder_url):
    """
    Send email with payment instructions and folder link.

    Args:
        subscriber_request: SubscriberRequest instance
        folder_url: URL to Google Drive folder for receipt upload
    """
    # Calculate deadline: 1 week after cohort registration closes
    # Use hasattr for backward compatibility with branches without cohort field
    if hasattr(subscriber_request, 'cohort') and subscriber_request.cohort:
        deadline = subscriber_request.cohort.reg_end_date + timedelta(days=7)
        deadline_str = deadline.strftime('%B %d, %Y')
        cohort_name = subscriber_request.cohort.name
    else:
        deadline_str = "1 week from registration date"
        cohort_name = "General"

    # Get payment amount
    # TODO: Update PAYMENT_AMOUNTS in google_api_utils.py when supervisor provides amounts
    amount = PAYMENT_AMOUNTS.get(subscriber_request.plan, 0)

    # TODO: Ask supervisor for currency (USD, MMK, etc.)
    currency = "USD"  # Placeholder

    context = {
        'name': subscriber_request.name,
        'plan': subscriber_request.get_plan_display(),
        'cohort': cohort_name,
        'amount': amount,
        'currency': currency,
        'folder_url': folder_url or '#',
        'deadline': deadline_str,
    }

    try:
        html_message = render_to_string('emails/payment_instructions.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Payment Instructions - Myanmar Data Tech',
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[subscriber_request.email],
            html_message=html_message,
            fail_silently=True,
        )

        print(f"Payment instructions email sent to {subscriber_request.email}")

    except Exception as e:
        print(f"Error sending payment email to {subscriber_request.email}: {e}")
        # TODO: Log this error properly
