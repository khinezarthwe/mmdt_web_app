from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UserSession(models.Model):
    """
    Track active user sessions across devices for JWT token management.

    This model enables multi-device support by storing session information
    for each device/client that authenticates with the system.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    refresh_token_jti = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text='JWT Token ID (jti) from refresh token'
    )
    access_token_jti = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='JWT Token ID (jti) from access token'
    )

    # Device/Client information
    client_type = models.CharField(
        max_length=50,
        default='unknown',
        help_text='Type of client: telegram_bot, website, mobile, etc.'
    )
    device_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Human-readable device name'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the client'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text='User agent string from HTTP headers'
    )

    # Telegram-specific fields
    telegram_user_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='Telegram user ID for bot authentication'
    )
    telegram_username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Telegram username'
    )

    # Session metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text='When this session expires'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this session is currently active'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['refresh_token_jti']),
            models.Index(fields=['telegram_user_id']),
        ]
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'

    def __str__(self):
        return f"{self.user.username} - {self.client_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def is_expired(self):
        """Check if the session has expired."""
        return timezone.now() > self.expires_at

    def revoke(self):
        """Revoke this session."""
        self.is_active = False
        self.save(update_fields=['is_active', 'last_activity'])


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

