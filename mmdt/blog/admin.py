from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from .models import Post, Comment


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
