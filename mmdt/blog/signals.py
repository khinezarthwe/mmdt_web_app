from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.crypto import get_random_string

from .models import SubscriberRequest, CohortMembership


@receiver(pre_save, sender=SubscriberRequest)
def track_status_change(sender, instance, **kwargs):
    """Track if status is changing to 'approved' for automatic provisioning."""
    if instance.pk:
        try:
            old_instance = SubscriberRequest.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._status_changed_to_approved = (
                old_instance.status != 'approved' and instance.status == 'approved'
            )
        except SubscriberRequest.DoesNotExist:
            instance._old_status = None
            instance._status_changed_to_approved = False
    else:
        instance._old_status = None
        instance._status_changed_to_approved = instance.status == 'approved'


@receiver(post_save, sender=SubscriberRequest)
def provision_user_on_approval(sender, instance, created, **kwargs):
    """Automatically provision user account when SubscriberRequest is approved."""
    status_changed = getattr(instance, '_status_changed_to_approved', False)

    if not status_changed:
        return

    if instance.status != 'approved':
        return

    if not instance.cohort:
        return

    if hasattr(instance, '_provisioning_done'):
        return

    instance._provisioning_done = True

    email = instance.email.lower().strip()

    try:
        user = User.objects.get(email__iexact=email)
        is_new_user = False
    except User.DoesNotExist:
        is_new_user = True
        temporary_password = get_random_string(12)

        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        name_parts = instance.name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=temporary_password,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )

    profile = user.profile
    profile.expiry_date = instance.expiry_date
    profile.current_cohort = instance.cohort
    profile.expired = False
    profile.save()

    if not is_new_user:
        CohortMembership.objects.filter(user=user, is_active=True).update(is_active=False)

    CohortMembership.objects.create(
        user=user,
        cohort=instance.cohort,
        plan=instance.plan,
        expiry_date=instance.expiry_date,
        subscriber_request=instance,
        is_active=True
    )

    try:
        if is_new_user:
            subject = 'Welcome to Myanmar Data Tech - Account Created'
            context = {
                'name': instance.name,
                'username': user.username,
                'password': temporary_password,
                'email': email,
                'plan': instance.get_plan_display(),
                'expiry_date': instance.expiry_date.strftime('%B %d, %Y'),
                'cohort': instance.cohort.name,
            }
            html_message = render_to_string('emails/user_account_created.html', context)
            plain_message = strip_tags(html_message)
        else:
            subject = 'Myanmar Data Tech - Membership Renewed'
            context = {
                'name': instance.name,
                'plan': instance.get_plan_display(),
                'expiry_date': instance.expiry_date.strftime('%B %d, %Y'),
                'cohort': instance.cohort.name,
            }
            html_message = render_to_string('emails/user_membership_renewed.html', context)
            plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        pass
