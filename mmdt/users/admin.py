from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    """Standalone admin for UserProfile."""
    list_display = ('user', 'current_cohort', 'subscriber_request', 'get_telegram_username', 'expired', 'expiry_date', 'created_at', 'updated_at')
    list_filter = ('expired', 'current_cohort', 'subscriber_request', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'current_cohort__name', 'current_cohort__cohort_id', 'subscriber_request__email', 'subscriber_request__name', 'subscriber_request__telegram_username')
    readonly_fields = ('created_at', 'updated_at', 'get_telegram_username')
    fields = ('user', 'expired', 'expiry_date', 'current_cohort', 'subscriber_request', 'get_telegram_username', 'created_at', 'updated_at')
    autocomplete_fields = ['current_cohort', 'subscriber_request']
    
    def get_telegram_username(self, obj):
        """Display telegram username from subscriber request."""
        return obj.telegram_username or '-'
    get_telegram_username.short_description = 'Telegram Username'


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('expired', 'expiry_date', 'current_cohort', 'subscriber_request', 'get_telegram_username', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'get_telegram_username')
    autocomplete_fields = ['current_cohort', 'subscriber_request']
    
    def get_telegram_username(self, obj):
        """Display telegram username from subscriber request."""
        if obj and obj.subscriber_request:
            return obj.subscriber_request.telegram_username or '-'
        return '-'
    get_telegram_username.short_description = 'Telegram Username'


class CustomUserAdmin(UserAdmin):
    """Custom User admin with UserProfile inline."""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_expired_status', 'get_current_cohort', 'get_telegram_username')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__expired', 'profile__current_cohort', 'profile__subscriber_request')
    actions = ['mark_users_as_expired', 'mark_users_as_active']
    
    def get_expired_status(self, obj):
        """Display expired status from profile."""
        if hasattr(obj, 'profile'):
            return obj.profile.expired
        return None
    get_expired_status.short_description = 'Expired'
    get_expired_status.boolean = True
    
    def get_current_cohort(self, obj):
        """Display current cohort from profile."""
        if hasattr(obj, 'profile') and obj.profile.current_cohort:
            return obj.profile.current_cohort.name
        return '-'
    get_current_cohort.short_description = 'Current Cohort'
    
    def get_telegram_username(self, obj):
        """Display telegram username from subscriber request."""
        if hasattr(obj, 'profile') and obj.profile.subscriber_request:
            return obj.profile.subscriber_request.telegram_username or '-'
        return '-'
    get_telegram_username.short_description = 'Telegram'
    
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


# Register UserProfile admin
admin.site.register(UserProfile, UserProfileAdmin)

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

