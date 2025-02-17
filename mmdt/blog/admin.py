from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django_summernote.admin import SummernoteModelAdmin

from .models import Post, Comment
from .models import SubscriberRequest


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active'),
        }),
    )


# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


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
    list_display = ['name', 'email', 'country', 'plan', 'status', 'created_at', 'updated_at', 'expiry_date']
    list_filter = ['status', 'free_waiver', 'created_at', 'updated_at', 'expiry_date']
    search_fields = ['name', 'email', 'country', 'status']
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        queryset.update(status='approved')
    approve_requests.short_description = "Approve selected requests"

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected')
    reject_requests.short_description = "Reject selected requests"
