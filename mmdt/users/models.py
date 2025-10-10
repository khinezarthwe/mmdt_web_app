from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with expiration tracking."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    expired = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {'Expired' if self.expired else 'Active'}"

    def check_expiry(self):
        """Check if user should be expired based on expiry_date."""
        if self.expiry_date and timezone.now() >= self.expiry_date:
            return True
        return False

    def save(self, *args, **kwargs):
        """Override save to automatically handle expiration."""
        # Auto-set expired status based on expiry_date
        if self.expiry_date:
            if timezone.now() >= self.expiry_date:
                self.expired = True
            # Only auto-reactivate if expiry_date is in the future
            elif timezone.now() < self.expiry_date and self.expired:
                self.expired = False
        
        super().save(*args, **kwargs)
        
        # Update user's active status based on expired flag
        if self.expired and self.user.is_active:
            self.user.is_active = False
            self.user.save(update_fields=['is_active'])
        elif not self.expired and not self.user.is_active:
            # Reactivate user if they're no longer expired
            self.user.is_active = True
            self.user.save(update_fields=['is_active'])

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

