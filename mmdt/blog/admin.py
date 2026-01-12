from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from .models import Post, Comment, SubscriberRequest, Cohort


class PostAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',)
    list_display = ('title', 'slug', 'status', 'created_on')
    list_filter = ("status",)
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'body', 'post', 'created_on', 'active')
    list_filter = ('active', 'created_on')
    search_fields = ('name', 'email', 'body')
    actions = ['toggle_comments_active']
    
    # Custom action to toggle active status of comments if there is any inappropriate comments
    def toggle_comments_active(self, request, queryset):
        for comment in queryset:
            comment.active = not comment.active
            comment.save()
    toggle_comments_active.short_description = 'Toggle active status of selected comments'


admin.site.register(Post, PostAdmin)


@admin.register(SubscriberRequest)
class SubscriberRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'telegram_username', 'country', 'plan', 'cohort', 'status', 'created_at', 'updated_at', 'expiry_date', 'mmdt_email']
    list_filter = ['status', 'free_waiver', 'plan', 'cohort', 'created_at', 'updated_at', 'expiry_date']
    search_fields = ['name', 'email', 'telegram_username', 'country', 'status', 'cohort__cohort_id']
    readonly_fields = ['cohort', 'created_at', 'updated_at', 'expiry_date']
    actions = ['approve_requests', 'reject_requests']

    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'mmdt_email', 'telegram_username', 'job_title')
        }),
        ('Location', {
            'fields': ('country', 'city')
        }),
        ('Subscription Details', {
            'fields': ('plan', 'cohort', 'expiry_date', 'free_waiver')
        }),
        ('Status', {
            'fields': ('status', 'message')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def approve_requests(self, request, queryset):
        queryset.update(status='approved')
    approve_requests.short_description = "Approve selected requests"

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected')
    reject_requests.short_description = "Reject selected requests"


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = [
        'cohort_id', 'name', 'reg_start_date', 'reg_end_date',
        'exp_date_6', 'exp_date_12', 'is_active', 'registration_status'
    ]
    list_filter = ['is_active', 'reg_start_date', 'reg_end_date']
    search_fields = ['cohort_id', 'name']
    date_hierarchy = 'reg_start_date'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('cohort_id', 'name', 'is_active')
        }),
        ('Registration Window', {
            'fields': ('reg_start_date', 'reg_end_date')
        }),
        ('Expiry Dates', {
            'fields': ('exp_date_6', 'exp_date_12'),
            'description': 'Set expiry dates for 6-month and 12-month plans'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def registration_status(self, obj):
        if obj.is_registration_open():
            return "Open"
        return "Closed"
    registration_status.short_description = 'Registration Status'

    actions = ['open_registration', 'close_registration']

    def open_registration(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} cohort(s) opened for registration.')
    open_registration.short_description = "Open registration for selected cohorts"

    def close_registration(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} cohort(s) closed for registration.')
    close_registration.short_description = "Close registration for selected cohorts"
