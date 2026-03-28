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
from .google_api_utils import get_or_create_subscriber_folder_url


@receiver(post_save, sender=SubscriberRequest)
def handle_subscriber_request_automation(sender, instance, created, **kwargs):
    """
    Automate Google Drive folder, spreadsheet row, and confirmation email for
    all new subscriber requests (paid and fee waiver). Fee waiver applicants
    use the same folder link to upload supporting evidence (see email template).
    """
    if not created:
        return

    # Prevent duplicate triggers
    if hasattr(instance, '_automation_done'):
        return

    instance._automation_done = True

    # Step 1–2: Reuse folder URL from sheet if email already exists; else create folder + upsert sheet
    folder_url = get_or_create_subscriber_folder_url(instance)

    if not folder_url:
        print(f"Warning: No folder URL for {instance.email} (sheet lookup and folder creation both failed or empty)")
        # TODO: Send notification to admin about failure
        # Continue with email using placeholder link

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
    else:
        deadline_str = "1 week from registration date"

    context = {
        'name': subscriber_request.name,
        'plan': subscriber_request.get_plan_display(),
        'folder_url': folder_url or '#',
        'deadline': deadline_str,
        'free_waiver': subscriber_request.free_waiver,
    }

    try:
        html_message = render_to_string('emails/paid_user_confirmation.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Thank you for your subscription request',
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[subscriber_request.email],
            html_message=html_message,
            fail_silently=True,
        )

        print(f"Payment instructions email sent to {subscriber_request.email}")

    except Exception as e:
        print(f"Error sending payment email to {subscriber_request.email}: {e}")
