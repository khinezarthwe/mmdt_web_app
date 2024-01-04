# from django.contrib import admin

# from .models import Question, Choice


# class ChoiceInline(admin.TabularInline):
#     model = Choice
#     extra = 3


# class QuestionAdmin(admin.ModelAdmin):
#     fieldsets = [
#         (None, {"fields": ["question_text"]}),
#         ("Date information", {"fields": ["pub_date"]}),
#     ]
#     inlines = [ChoiceInline]
#     list_display = ["question_text", "pub_date", "was_published_recently"]
#     list_filter = ["pub_date"]
#     search_fields = ["question_text"]


# admin.site.register(Question, QuestionAdmin)
# admin.site.register(Choice)


from django.contrib import admin
from django.http import HttpResponse
import csv
# Import timezone module to use in the was_published_recently method
from django.utils import timezone

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
    list_display = ["question_text", "pub_date", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]
    # Register the custom action for the QuestionAdmin
    actions = ["export_poll_results"]

    # Define the custom action to export poll results to CSV
    def export_poll_results(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="poll_results.csv"'

        csv_writer = csv.writer(response)
        csv_writer.writerow(['Question Text', 'Choice Text', 'Votes'])

        for question in queryset:
            for choice in question.choice_set.all():
                csv_writer.writerow(
                    [question.question_text, choice.choice_text, choice.votes])

        return response

    export_poll_results.short_description = "Export selected poll results to CSV"


# Register the models with the updated admin configuration
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
