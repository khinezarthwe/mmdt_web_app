from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created."""
    if created:
        # Get the user's creation date (date_joined)
        user_creation_date = instance.date_joined or timezone.now()
        
        # Try to find an active cohort first using the existing method
        from blog.models import Cohort, SubscriberRequest
        cohort = Cohort.get_active_cohort(user_creation_date)
        
        # If no active cohort found, find any cohort whose registration window contains the user creation date
        if not cohort:
            cohort = Cohort.objects.filter(
                reg_start_date__lte=user_creation_date,
                reg_end_date__gte=user_creation_date
            ).order_by('-reg_start_date').first()
        
        # Try to find an approved subscriber request matching the user's email
        subscriber_request = None
        if instance.email:
            subscriber_request = SubscriberRequest.objects.filter(
                email=instance.email,
                status='approved'
            ).order_by('-created_at').first()
            
            if subscriber_request:
                # If cohort not found from date, use cohort from subscriber request
                if not cohort and subscriber_request.cohort:
                    cohort = subscriber_request.cohort
        
        # Create UserProfile with the assigned cohort and subscriber request
        UserProfile.objects.create(
            user=instance,
            current_cohort=cohort,
            subscriber_request=subscriber_request
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender='blog.SubscriberRequest')
def sync_subscriber_request_to_user_profile(sender, instance, **kwargs):
    """Create user and sync approved subscriber request to user profile when approved."""
    if instance.status == 'approved' and instance.email:
        # Check if user already exists (emails must be unique)
        try:
            user = User.objects.get(email=instance.email)
        except User.DoesNotExist:
            # User doesn't exist, create one
            user = None
        
        if not user:
            # Split name into first and last name
            name_parts = instance.name.strip().split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            # Create user with default password
            user = User.objects.create_user(
                username=instance.email,
                email=instance.email,
                password='mmdt@Welcome', #default password
                first_name=first_name,
                last_name=last_name,
                is_active=True,  # User is active by default
            )
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Update profile with subscriber request info
        profile.subscriber_request = instance
        
        # If cohort not set, use cohort from subscriber request
        if not profile.current_cohort and instance.cohort:
            profile.current_cohort = instance.cohort
        
        # Set expiry date from subscriber request if available
        if instance.expiry_date and not profile.expiry_date:
            profile.expiry_date = instance.expiry_date
        
        profile.save()


@receiver(pre_save, sender=UserProfile)
def track_renewal_approval_change(sender, instance, **kwargs):
    """Track if renewal_approved is changing from False to True."""
    if instance.pk:
        try:
            old_instance = UserProfile.objects.get(pk=instance.pk)
            instance._renewal_was_approved = old_instance.renewal_approved
        except UserProfile.DoesNotExist:
            instance._renewal_was_approved = False
    else:
        instance._renewal_was_approved = False


@receiver(post_save, sender=UserProfile)
def handle_renewal_approval(sender, instance, **kwargs):
    """
    When renewal_approved changes from False to True:
    1. Calculate new expiry_date based on current expiry and renewal_plan
       - 6month: next April 30 or October 31 (6 months out)
       - annual: next April 30 or October 31 (12 months out)
    2. Update expiry_date (only April 30 or October 31 allowed)
    3. Set expired=False
    4. Reset renewal_requested=False
    5. Reactivate user if needed
    
    Note: current_cohort is NOT updated - it represents the user's registration cohort.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    was_approved = getattr(instance, '_renewal_was_approved', False)
    
    # Only process if renewal_approved just changed to True
    if instance.renewal_approved and not was_approved:
        # Always reset renewal_requested when approved
        update_fields = {
            'renewal_requested': False,
            'renewal_approved_at': timezone.now(),
        }
        
        if instance.renewal_plan:
            # Calculate new expiry date based on current expiry
            new_expiry = instance.calculate_renewal_expiry_date()
            
            if new_expiry:
                update_fields.update({
                    'expiry_date': new_expiry,
                    'expired': False,
                })
                logger.info(
                    "Renewal approved for user_id=%s: new_expiry=%s, plan=%s",
                    instance.user.pk, new_expiry.strftime('%Y-%m-%d'), instance.renewal_plan
                )
            else:
                # No expiry date - log error (admin validation should prevent this)
                logger.error(
                    "Cannot approve renewal: No current expiry_date for user_id=%s, plan=%s. "
                    "Please set expiry date first.",
                    instance.user.pk, instance.renewal_plan
                )
        
        # Use update() to avoid triggering signals again
        UserProfile.objects.filter(pk=instance.pk).update(**update_fields)
        
        # Refresh instance from DB
        instance.refresh_from_db()
        
        # Reactivate user if needed (only if expiry was updated)
        if 'expired' in update_fields and not instance.user.is_active:
            instance.user.is_active = True
            instance.user.save(update_fields=['is_active'])

