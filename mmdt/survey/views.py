from django.shortcuts import render, redirect, get_object_or_404
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
        # Set the number of questions to display per page
        questions_per_page = 5
        paginator = Paginator(questions, questions_per_page)
        # Get the current page number from the request's GET parameters
        page = request.GET.get('page')
        try:
            current_page_questions = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            current_page_questions = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page of results.
            current_page_questions = paginator.page(paginator.num_pages)
            
        SurveyForm = create_survey_form(survey)
        if request.method == "POST":
            form = SurveyForm(request.POST)
            if form.is_valid():
                for question in current_page_questions:
                    response_text = form.cleaned_data.get(f'question_{question.id}')
                    if response_text is not None:
                        if question.question_type == Question.CHECKBOX:
                            # For checkbox questions, response_text is a list
                            choices = Choice.objects.filter(id__in=response_text)
                            response_text = ", ".join(choice.choice_text for choice in choices)
                        elif question.question_type == Question.MULTIPLE_CHOICE:
                            # For Multiple Choice questions, response_text is the selected choice ID
                            choice_id = int(response_text)
                            selected_choice = get_object_or_404(Choice, id=choice_id)
                            response_text = selected_choice.choice_text

                        elif question.question_type == Question.SLIDING_SCALE:
                            selected_index = int(response_text)
                            # Ensure the index is within the range of available choices
                            choices = question.choices.all()
                            if 0 <= selected_index < len(choices):
                                selected_choice = choices[selected_index]
                                response_text = {selected_choice.value}

                        elif question.question_type == Question.DROPDOWN: 
                            # For drop-down questions, response_text is the selected choice text
                            choice = get_object_or_404(Choice, id=response_text)
                            response_text = choice.choice_text
                        # Create Response object
                        Response.objects.create(question=question, response_text=response_text)
                # Display success message
                messages.success(request, 'Survey submitted successfully!')
                return redirect('survey:index')
        else:
            form = SurveyForm()
        context = {
            'survey': survey,
            'form': form,
            'current_page_questions': current_page_questions,
        }
        return render(request, 'survey/survey_detail.html', context)