from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserSession


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('expired', 'expiry_date', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


class CustomUserAdmin(UserAdmin):
    """Custom User admin with UserProfile inline."""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_expired_status')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__expired')
    actions = ['mark_users_as_expired', 'mark_users_as_active']
    
    def get_expired_status(self, obj):
        """Display expired status from profile."""
        if hasattr(obj, 'profile'):
            return obj.profile.expired
        return None
    get_expired_status.short_description = 'Expired'
    get_expired_status.boolean = True
    
    def mark_users_as_expired(self, request, queryset):
        """Mark selected users as expired and deactivate them."""
        count = 0
        for user in queryset:
            if hasattr(user, 'profile'):
                user.profile.expired = True
                user.profile.save()  # This will auto-deactivate via save() method
                count += 1
        self.message_user(request, f'{count} user(s) marked as expired and deactivated.')
    mark_users_as_expired.short_description = "Mark selected users as expired"
    
    def mark_users_as_active(self, request, queryset):
        """Mark selected users as active (not expired)."""
        count = 0
        for user in queryset:
            if hasattr(user, 'profile'):
                user.profile.expired = False
                user.profile.save()  # This will auto-activate via save() method
                count += 1
        self.message_user(request, f'{count} user(s) marked as active.')
    mark_users_as_active.short_description = "Mark selected users as active (not expired)"


# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserSession model."""
    list_display = (
        'user',
        'client_type',
        'device_name',
        'telegram_username',
        'is_active',
        'created_at',
        'expires_at',
        'ip_address'
    )
    list_filter = (
        'client_type',
        'is_active',
        'created_at',
        'expires_at'
    )
    search_fields = (
        'user__username',
        'user__email',
        'telegram_username',
        'device_name',
        'ip_address'
    )
    readonly_fields = (
        'refresh_token_jti',
        'access_token_jti',
        'created_at',
        'last_activity'
    )
    actions = ['revoke_sessions']

    def revoke_sessions(self, request, queryset):
        """Revoke selected sessions."""
        count = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f'{count} session(s) revoked successfully.')
    revoke_sessions.short_description = "Revoke selected sessions"

