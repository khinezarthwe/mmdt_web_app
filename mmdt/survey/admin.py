from django.contrib import admin
from .models import SurveyForm, SurveyQuestion, Response

# Define an inline admin interface for SurveyQuestion
class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion # Link to the SurveyQuestion model
    extra = 1 # Provide 1 extra blank form when creating a new SurveyForm by default

# Define the admin interface for SurveyForm
class SurveyFormAdmin(admin.ModelAdmin):
    inlines = [SurveyQuestionInline] # Include the inline admin interface for SurveyQuestion

# Define the admin interface for Response
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'text') # Display the 'question' and 'text' fields in the Response list view

# Register the admin interfaces with the admin site
admin.site.register(SurveyForm, SurveyFormAdmin)
admin.site.register(SurveyQuestion)
admin.site.register(Response, ResponseAdmin)