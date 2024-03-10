from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Survey, Response, Question, Choice
from .forms import create_survey_form
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class SurveyPage:
    def index(request):
        surveys = Survey.objects.filter(is_active=True)
        return render(request, 'survey/index.html', {'surveys': surveys})

    def survey_detail(request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        questions = survey.questions.all().order_by('pub_date')

        questions_per_page = 5
        paginator = Paginator(questions, questions_per_page)
        page = request.GET.get('page')

        try:
            current_page_questions = paginator.page(page)
        except PageNotAnInteger:
            current_page_questions = paginator.page(1)
        except EmptyPage:
            current_page_questions = paginator.page(paginator.num_pages)

        SurveyForm = create_survey_form(survey)
        
        if request.method == "POST":
            form = SurveyForm(request.POST)
            if form.is_valid():
                action = request.POST.get('action', 'submit')
                responses = request.session.get('survey_responses', {})
                
                for question in current_page_questions:
                    response_text = form.cleaned_data.get(f'question_{question.id}')
                    if response_text is not None:
                        responses[f'question_{question.id}'] = response_text

                request.session['survey_responses'] = responses
                
                if action == 'next' and current_page_questions.has_next():
                    next_page_number = current_page_questions.next_page_number()
                    redirect_url = reverse('survey:survey_detail', args=[survey_id]) + f'?page={next_page_number}'
                    return HttpResponseRedirect(redirect_url)
                elif action == 'previous' and current_page_questions.has_previous():
                    prev_page_number = current_page_questions.previous_page_number()
                    redirect_url = reverse('survey:survey_detail', args=[survey_id]) + f'?page={prev_page_number}'
                    return HttpResponseRedirect(redirect_url)
                elif action == 'submit' and not current_page_questions.has_next():
                    # Process all responses from the session
                    for question_id, response_text in responses.items():
                        question_id_num = int(question_id.split('_')[-1])
                        question = get_object_or_404(Question, id=question_id_num)
                        Response.objects.create(
                            question=question,
                            response_text=response_text
                        )
                    
                    messages.success(request, 'Survey submitted successfully!')
                    del request.session['survey_responses']
                    return redirect('survey:index')
        else:
            form = SurveyForm(initial=request.session.get('survey_responses', {}))

        context = {
            'survey': survey,
            'form': form,
            'current_page_questions': current_page_questions,
        }
        return render(request, 'survey/survey_detail.html', context)