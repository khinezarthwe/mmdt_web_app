from django.shortcuts import render, redirect, get_object_or_404
from .models import Survey, Response, Question
from .forms import create_survey_form

class SurveyPage:
    def index(request):
        surveys = Survey.objects.filter(is_active=True)
        return render(request, 'survey/index.html', {'surveys': surveys})

    def survey_detail(request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        SurveyForm = create_survey_form(survey)
        
        if request.method == "POST":
            form = SurveyForm(request.POST)
            if form.is_valid():
                for question in survey.questions.all():
                    response_text = form.cleaned_data.get(f'question_{question.id}')
                    if response_text:
                        Response.objects.create(question=question, response_text=response_text)
                return redirect('survey:index')
        else:
            form = SurveyForm()
        return render(request, 'survey/survey_detail.html', {'survey': survey, 'form': form})