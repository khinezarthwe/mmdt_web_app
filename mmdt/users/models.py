from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with expiration tracking."""
    
    PLAN_CHOICES = [
        ('6month', '6-Month Plan'),
        ('annual', 'Annual Plan'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    expired = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True, blank=True)
    current_cohort = models.ForeignKey(
        'blog.Cohort',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_members',
        help_text="User's current active cohort"
    )
    subscriber_request = models.ForeignKey(
        'blog.SubscriberRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profiles',
        help_text="Associated approved subscriber request"
    )
    
    # Renewal fields
    renewal_requested = models.BooleanField(default=False, help_text="User has requested membership renewal")
    renewal_plan = models.CharField(max_length=10, choices=PLAN_CHOICES, null=True, blank=True, help_text="Selected plan for renewal")
    renewal_approved = models.BooleanField(default=False, help_text="Admin has approved the renewal")
    renewal_approved_at = models.DateTimeField(null=True, blank=True, help_text="When the renewal was approved")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {'Expired' if self.expired else 'Active'}"

    def check_expiry(self):
        """Check if user should be expired based on expiry_date."""
        if self.expiry_date and timezone.now() >= self.expiry_date:
            return True
        return False
    
    @property
    def telegram_username(self):
        """Get telegram username from associated subscriber request."""
        if self.subscriber_request:
            return self.subscriber_request.telegram_username
        return None

    def calculate_renewal_expiry_date(self):
        """
        Calculate new expiry date for renewal based on current expiry and plan.
        
        Rules:
        - 6month: Add 6 months, snap to next April 30 or October 31
        - annual: Add 12 months, snap to next April 30 or October 31
        - Expiry dates can only be April 30 or October 31
        
        Returns:
            datetime or None if no current expiry_date
        """
        from datetime import datetime
        
        if not self.expiry_date or not self.renewal_plan:
            return None
        
        current_expiry = self.expiry_date
        
        # Determine the next valid expiry date based on plan
        # Valid dates: April 30 and October 31
        if self.renewal_plan == '6month':
            # 6 months: April 30 → October 31, October 31 → April 30 (next year)
            if current_expiry.month <= 4 or (current_expiry.month == 4 and current_expiry.day <= 30):
                # Current expiry is around April or before → next is October 31 same year
                new_expiry = current_expiry.replace(month=10, day=31, hour=23, minute=59, second=59)
            else:
                # Current expiry is after April → next is April 30 next year
                new_expiry = current_expiry.replace(year=current_expiry.year + 1, month=4, day=30, hour=23, minute=59, second=59)
        else:
            # 12 months (annual): April 30 → April 30 (next year), October 31 → October 31 (next year)
            if current_expiry.month <= 4 or (current_expiry.month == 4 and current_expiry.day <= 30):
                # Current expiry is around April → next is April 30 next year
                new_expiry = current_expiry.replace(year=current_expiry.year + 1, month=4, day=30, hour=23, minute=59, second=59)
            else:
                # Current expiry is around October → next is October 31 next year
                new_expiry = current_expiry.replace(year=current_expiry.year + 1, month=10, day=31, hour=23, minute=59, second=59)
        
        # Make timezone aware if needed
        if timezone.is_naive(new_expiry):
            new_expiry = timezone.make_aware(new_expiry)
        
        return new_expiry

    def clean(self):
        """Validate renewal approval has valid expiry date."""
        super().clean()
        
        # Check if renewal_approved is being set to True
        if self.renewal_approved and self.renewal_plan:
            # Check if this is a new approval (not already approved)
            if self.pk:
                try:
                    old_instance = UserProfile.objects.get(pk=self.pk)
                    was_approved = old_instance.renewal_approved
                except UserProfile.DoesNotExist:
                    was_approved = False
            else:
                was_approved = False
            
            # Only validate when changing from False to True
            if not was_approved:
                if not self.expiry_date:
                    raise ValidationError({
                        'renewal_approved': (
                            "Cannot approve renewal: User has no current expiry date. "
                            "Please set an expiry date first."
                        )
                    })

    def save(self, *args, **kwargs):
        """Override save to automatically handle expiration."""
        if self.expiry_date:
            if timezone.now() >= self.expiry_date:
                self.expired = True
            elif timezone.now() < self.expiry_date and self.expired:
                self.expired = False

        super().save(*args, **kwargs)

        if self.expired and self.user.is_active:
            self.user.is_active = False
            self.user.save(update_fields=['is_active'])
        elif not self.expired and not self.user.is_active:
            self.user.is_active = True
            self.user.save(update_fields=['is_active'])

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

