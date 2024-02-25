from django.shortcuts import render
from .models import SurveyForm

class SurveyPage:
    def index(request):
        survey_forms = SurveyForm.objects.all()
        return render(request, 'survey/index.html', {'survey_forms': survey_forms})