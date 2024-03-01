from django.contrib import admin
from .models import Survey, Question, Choice, Response

class ChoiceInLine(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionInLine(admin.TabularInline):
    model = Question
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInLine]
    fieldsets = [(None, {'fields': ['survey', 'question_text', 'question_type', 'pub_date', 'is_enabled']}),]

class SurveyAdmin(admin.ModelAdmin):
    inlines = [QuestionInLine]
    fieldsets = [
        (None, {'fields': ['title', 'description', 'start_date', 'end_date', 'is_active']})
    ]

class ResponseAdmin(admin.ModelAdmin):
    list_display = ['question', 'response_text']
    search_fields = ['question__question_text', 'response_text']

admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Response, ResponseAdmin)