from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with expiration tracking."""
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {'Expired' if self.expired else 'Active'}"

    def check_expiry(self):
        """Check if user should be expired based on expiry_date."""
        if self.expiry_date and timezone.now() >= self.expiry_date:
            return True
        return False

    def get_active_membership(self):
        """Get the user's active cohort membership."""
        from blog.models import CohortMembership
        return CohortMembership.objects.filter(
            user=self.user,
            is_active=True,
            expiry_date__gt=timezone.now()
        ).order_by('-expiry_date').first()

    def save(self, *args, **kwargs):
        """Override save to automatically handle expiration."""
        active_membership = self.get_active_membership()

        if active_membership:
            self.expiry_date = active_membership.expiry_date
            self.current_cohort = active_membership.cohort
            self.expired = False
        else:
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

