import csv
from django.http import HttpResponse
from django.contrib import admin

from .models import Question, Choice

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

def export_to_csv(modeladmin, request, queryset):
    """
    export_to_csv
    :param modeladmin: The ModelAdmin instance.
    :param request: The current request.
    :param queryset: The queryset containing selected poll results.
    :return: A CSV file response containing the poll results.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="poll_results.csv"'
    writer = csv.writer(response)

    # Write the headers to csv file
    writer.writerow(['Question', 'Choice', 'Votes'])

    # Write data
    for question in queryset:
        for choice in question.choice_set.all():
            writer.writerow([question.question_text, choice.choice_text, choice.votes])
    return response


export_to_csv.short_description = 'Export Selected Questions to CSV'


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text", "image"]}), # Added image field
        ("Date information", {"fields": ["pub_date", "is_enabled"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently", "is_enabled"]
    list_filter = ["pub_date", "is_enabled"]
    search_fields = ["question_text"]
    actions = [export_to_csv, 'enable_questions', 'disable_questions']

    def enable_questions(self, request, queryset):
        queryset.update(is_enabled=True)
    enable_questions.short_description = 'Enable selected questions'

    def disable_questions(self, request, queryset):
        queryset.update(is_enabled=False)
    disable_questions.short_description = 'Disable selected questions'

admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
