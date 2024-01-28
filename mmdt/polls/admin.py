from django.contrib import admin

from .models import Question, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently", "is_enabled"]
    list_filter = ["pub_date", "is_enabled"]
    search_fields = ["question_text"]

    actions = ['enable_questions', 'disable_questions']

    def enable_questions(self, request, queryset):
        queryset.update(is_enabled=True)

    def disable_questions(self, request, queryset):
        queryset.update(is_enabled=False)

    enable_questions.short_description = "Enable selected questions"
    disable_questions.short_description = "Disable selected questions"

admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)


