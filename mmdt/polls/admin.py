import csv
from django.http import HttpResponse
from django.contrib import admin

from .models import Question, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename="poll_results.csv"'
    writer = csv.writer(response)

    # Write the headers to csv file
    writer.writerow(['Question', 'Choice', 'Votes'])

    # Write data
    for question in queryset:
        for choice in question.choice_set.all():
            writer.writerow([question.question_text, choice.choice_text, choice.votes])
    return response

export_to_csv.short_description = "Export Selected Questions to CSV"


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]
    actions = [export_to_csv]

admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)


