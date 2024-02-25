from django.contrib import admin
from .models import SurveyForm, SurveyQuestion, Response

class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1

class SurveyFormAdmin(admin.ModelAdmin):
    inlines = [SurveyQuestionInline]

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'text')

admin.site.register(SurveyForm, SurveyFormAdmin)
admin.site.register(SurveyQuestion)
admin.site.register(Response, ResponseAdmin)