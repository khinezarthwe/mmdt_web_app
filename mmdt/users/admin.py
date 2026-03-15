from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    """Standalone admin for UserProfile."""
    list_display = ('user', 'current_cohort', 'subscriber_request', 'get_telegram_username', 'expired', 'expiry_date', 'renewal_requested', 'renewal_plan', 'renewal_approved', 'created_at', 'updated_at')
    list_filter = ('expired', 'renewal_requested', 'renewal_approved', 'renewal_plan', 'current_cohort', 'subscriber_request', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'current_cohort__name', 'current_cohort__cohort_id', 'subscriber_request__email', 'subscriber_request__name', 'subscriber_request__telegram_username')
    readonly_fields = ('created_at', 'updated_at', 'get_telegram_username', 'renewal_approved_at')
    autocomplete_fields = ['current_cohort', 'subscriber_request']
    actions = ['approve_renewal_requests']
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'get_telegram_username')
        }),
        ('Subscription Status', {
            'fields': ('expired', 'expiry_date', 'current_cohort', 'subscriber_request')
        }),
        ('Renewal Request', {
            'fields': ('renewal_requested', 'renewal_plan', 'renewal_approved', 'renewal_approved_at'),
            'description': 'Check renewal_approved to approve the renewal request. This will automatically update expiry_date.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_telegram_username(self, obj):
        """Display telegram username from subscriber request."""
        return obj.telegram_username or '-'
    get_telegram_username.short_description = 'Telegram Username'
    
    def approve_renewal_requests(self, request, queryset):
        """Approve selected renewal requests. Signal handles expiry update automatically."""
        count = 0
        for profile in queryset.filter(renewal_requested=True, renewal_approved=False):
            if profile.renewal_plan:
                profile.renewal_approved = True
                profile.save()  # Signal handles expiry_date, cohort, etc.
                count += 1
        
        self.message_user(request, f'{count} renewal request(s) approved and expiry dates updated.')
    approve_renewal_requests.short_description = "Approve selected renewal requests"


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('expired', 'expiry_date', 'current_cohort', 'subscriber_request', 'get_telegram_username', 'renewal_requested', 'renewal_plan', 'renewal_approved', 'renewal_approved_at', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'get_telegram_username', 'renewal_approved_at')
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
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_expired_status', 'get_renewal_status', 'get_current_cohort', 'get_telegram_username')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__expired', 'profile__renewal_requested', 'profile__renewal_approved', 'profile__current_cohort', 'profile__subscriber_request')
    actions = ['mark_users_as_expired', 'mark_users_as_active', 'approve_renewal_requests']
    
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
    
    def get_renewal_status(self, obj):
        """Display renewal request status from profile."""
        if hasattr(obj, 'profile'):
            if obj.profile.renewal_requested:
                return "Pending"
            elif obj.profile.renewal_approved:
                return "Approved"
        return "-"
    get_renewal_status.short_description = 'Renewal'
    
    def approve_renewal_requests(self, request, queryset):
        """Approve renewal requests for selected users. Signal handles expiry update automatically."""
        count = 0
        for user in queryset:
            if hasattr(user, 'profile') and user.profile.renewal_requested and not user.profile.renewal_approved:
                if user.profile.renewal_plan:
                    user.profile.renewal_approved = True
                    user.profile.save()  # Signal handles expiry_date, cohort, etc.
                    count += 1
        
        self.message_user(request, f'{count} renewal request(s) approved and expiry dates updated.')
    approve_renewal_requests.short_description = "Approve renewal requests for selected users"


# Register UserProfile admin
admin.site.register(UserProfile, UserProfileAdmin)

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

