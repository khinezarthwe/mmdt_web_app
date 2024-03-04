import csv
from django.http import HttpResponse
from django.contrib import admin

from .models import Question, Choice, ActiveGroup

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
        ("Date information", {"fields": ["pub_date", "is_enabled", "poll_group"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently", "is_enabled", "poll_group"]
    list_filter = ["pub_date", "is_enabled", "poll_group"]
    search_fields = ["question_text"]
    actions = [export_to_csv, 'enable_questions', 'disable_questions']

    def enable_questions(self, request, queryset):
        queryset.update(is_enabled=True)
    enable_questions.short_description = 'Enable selected questions'

    def disable_questions(self, request, queryset):
        queryset.update(is_enabled=False)
    disable_questions.short_description = 'Disable selected questions'

class ActiveGroupAdmin(admin.ModelAdmin):
    list_display = ['group_name', 'group_id', 'is_active', 'registration_required', 'is_results_released']
    list_filter = ["registration_required"]
    actions = ['activate_groups', 'deactivate_groups', 'registration_questions', 'guests_questions', 'results_released', 'results_not_released']

    def activate_groups(self, request, queryset):
        queryset.update(is_active=True)
    activate_groups.short_description = 'Activate selected groups'

    def deactivate_groups(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_groups.short_description = 'Deactivate selected groups'

    def registration_questions(self, request, queryset):
        queryset.update(registration_required=True)
    registration_questions.short_description = 'Registrations required selected questions'

    def guests_questions(self, request, queryset):
        queryset.update(registration_required=False)
    guests_questions.short_description = 'Registrations are not required selected questions'

    def results_released(self, request, queryset):
        queryset.update(is_results_released=True)
    results_released.short_description = "Released the results selected groups"
    
    def results_not_released(self, request, queryset):
        queryset.update(is_results_released=False)
    results_not_released.short_description = "Not released the results selected groups"

admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(ActiveGroup, ActiveGroupAdmin)
