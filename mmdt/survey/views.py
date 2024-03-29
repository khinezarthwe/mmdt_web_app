from django.shortcuts import render, redirect, get_object_or_404
from .models import Survey, Response, Question, Choice,  UserSurveyResponse
from .forms import create_survey_form
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json


class SurveyPage:
    def index(request):
        surveys = Survey.objects.filter(is_active=True)
        submitted_successfully = request.session.pop('survey_submitted_successfully', False)
        # Get any messages passed from the view
        message_list = messages.get_messages(request)
        return render(request, 'survey/index.html', {'surveys': surveys, 'submitted_successfully': submitted_successfully, 'messages': message_list})
    
    def survey_detail(request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        # Check if registration is required for this survey
        if survey.registration_required and not request.user.is_authenticated:
            messages.warning(request, f'You need to log in to participate in this survey.')
            return redirect('survey:index')
        questions = survey.questions.all().order_by('pub_date')

        if request.user.is_authenticated:  # Check if the user is authenticated
            if UserSurveyResponse.objects.filter(user=request.user, survey=survey).exists():
                messages.warning(request, 'You have already responded to this survey.')
                return redirect('survey:index')

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
            form_data = request.POST
            all_responses = form_data.get('all_responses')
            if all_responses:
                all_responses_dict = json.loads(all_responses)
           

                for field_name, response_text in all_responses_dict.items():
                    if field_name.startswith('question_'):
                        question_id = field_name.replace('question_', '')
                        try:
                            question = Question.objects.get(id=question_id)
                        except Question.DoesNotExist:
                            # Handle the case where the question doesn't exist
                            messages.error(request, f'Invalid question ID: {question_id}')
                            return redirect('survey:index')
                        
                        if isinstance(response_text, list) and question.question_type == Question.CHECKBOX:
                            # For checkbox questions, response_text is a list
                            for choice_id in response_text:
                                choice = get_object_or_404(Choice, id=choice_id)
                                Response.objects.create(question=question, response_text=choice.choice_text)
                        else:
                            
                            if response_text is not None:

                                if question.question_type == Question.MULTIPLE_CHOICE:
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
                                        response_text = selected_choice.choice_text

                                elif question.question_type == Question.DROPDOWN: 
                                    if response_text:
                                        choice = get_object_or_404(Choice, choice_text=response_text)
                                        response_text = choice.choice_text
                                    else:
                                        # Handle the default option, e.g., set response_text to a specific value
                                        response_text = "No answer selected"
                                # Create Response object
                                Response.objects.create(question=question, response_text=response_text)
            if survey.registration_required:
                # we will create response if surveys required to login
                UserSurveyResponse.objects.create(user=request.user, survey=survey)
            # Display success message
            request.session['survey_submitted_successfully'] = True
            return redirect('survey:index')
        else:
            form = SurveyForm()
        context = {
            'survey': survey,
            'form': form,
            'current_page_questions': current_page_questions,
        }
        return render(request, 'survey/survey_detail.html', context)
    