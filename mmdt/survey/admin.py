import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Survey, Question, Choice, Response

class ChoiceInLine(admin.TabularInline):
    model = Choice
    extra = 1

class QuestionInLine(admin.TabularInline):
    model = Question
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInLine]
    fieldsets = [(None, {'fields': ['survey', 'question_text', 'question_type', 'pub_date', 'is_enabled']}),]

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # Exclude choices for question types 'T' (Text) and 'LT' (Long Text)
            if obj and obj.question_type in ['T', 'LT'] and isinstance(inline, ChoiceInLine):
                continue
            yield inline.get_formset(request, obj), inline

class SurveyAdmin(admin.ModelAdmin):
    inlines = [QuestionInLine]
    fieldsets = [
        (None, {'fields': ['title', 'description', 'start_date', 'end_date', 'is_active']})
    ]

def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="survey_results.csv"'
    writer = csv.writer(response)
    writer.writerow(['Question', 'Response Text'])
    for obj in queryset:
        writer.writerow([obj.question.question_text, obj.response_text])
    return response

export_to_csv.short_description = 'Export Selected Responses to CSV'

class ResponseAdmin(admin.ModelAdmin):
    list_display = ['question', 'response_text']
    search_fields = ['question__question_text', 'response_text']
    actions = [export_to_csv]

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'question_type', 'question',]
    search_fields = ['question__question_text', 'choice_text']
    list_filter = ['question__question_type']

    def question_type(self, instance):
        return instance.question.question_type

    question_type.short_description = 'Question Type'

admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Response, ResponseAdmin)
