from .models import Survey, Response, Question, Choice,  UserSurveyResponse, ResponseChoice
import uuid
from collections import Counter

from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import create_survey_form
from .models import Survey, Response, Question, Choice, UserSurveyResponse, ResponseChoice


class SurveyPage:
    def index(request):
        surveys = Survey.objects.filter(is_active=True)
        submitted_successfully = request.session.pop('survey_submitted_successfully', False)
        # Get any messages passed from the view
        message_list = messages.get_messages(request)
        return render(request, 'survey/index.html', {'surveys': surveys, 'submitted_successfully': submitted_successfully, 'messages': message_list})

    def survey_detail(request, survey_slug):
        survey = get_object_or_404(Survey, slug=survey_slug)
        # Check if registration is required for this survey
        if request.method == "POST":
            if request.user.is_authenticated:
                user_survey_response = UserSurveyResponse.objects.filter(user=request.user, survey=survey).first()
            else:
                guest_id = request.session.get('guest_id', None)
                user_survey_response = UserSurveyResponse.objects.filter(guest_id=guest_id, survey=survey).first()

                if survey.registration_required:
                    # We will create response if surveys require to log in
                    messages.warning(request, f'You need to log in to participate in this survey.')
                    return redirect('survey:index')
            # Display success message
            if not user_survey_response.validate():
                messages.warning(request, 'Please answer all required questions before submitting the survey.')
                return redirect('survey:survey_detail', survey_slug=survey_slug)

            user_survey_response.is_draft = False
            user_survey_response.save()
            request.session['survey_submitted_successfully'] = True
            return redirect('survey:index')

        else:
            if survey.registration_required and not request.user.is_authenticated:
                messages.warning(request, f'You need to log in to participate in this survey.')
                return redirect('survey:index')
            guest_id = request.session.get('guest_id', None)
            if guest_id is None:
                guest_id = str(uuid.uuid4())
                request.session['guest_id'] = guest_id

            questions = survey.questions.all().order_by('pub_date')

            if request.user.is_authenticated:  # Check if the user is authenticated
                if UserSurveyResponse.objects.filter(user=request.user, survey=survey, is_draft=False).exists():
                    messages.warning(request, 'You have already responded to this survey.')
                    return redirect('survey:index')
                else:
                    user_survey_response = UserSurveyResponse.find_or_create_draft_user(request.user, survey)
            else:
                if UserSurveyResponse.objects.filter(guest_id=guest_id, survey=survey, is_draft=False).exists():
                    messages.warning(request, 'You have already responded to this survey.')
                    return redirect('survey:index')
                else:
                    user_survey_response = UserSurveyResponse.find_or_create_draft_guest(guest_id, survey)

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

            SurveyForm = create_survey_form(survey, user_survey_response, current_page_questions)
            form = SurveyForm()
            context = {
                'survey': survey,
                'form': form,
                'current_page_questions': current_page_questions,
            }
            return render(request, 'survey/survey_detail.html', context)

    def save_survey_response(request, survey_slug, question_id):
        survey = get_object_or_404(Survey, slug=survey_slug)
        user = request.user if request.user.is_authenticated else None
        guest_id = request.session.get('guest_id', None)
        if user:
            user_survey_response = UserSurveyResponse.find_or_create_draft_user(user, survey)
        else:
            user_survey_response = UserSurveyResponse.find_or_create_draft_guest(guest_id, survey)

            # Or maybe just return a 404
            # return HttpResponseNotFound('UserSurveyResponse not found')

        question_type = request.POST.get('question_type')
        question = Question.objects.filter(id=question_id).first()
        if not question:
            return HttpResponse(400)

        if question_type == 'text':
            payload = request.POST.get('payload')
            response = Response.objects.filter(question=question, user_survey_response=user_survey_response).first()
            if not response:
                Response.objects.create(question=question, user_survey_response=user_survey_response,
                                        response_text=payload)
            else:
                Response.objects.filter(id=response.id).update(question=question,
                                                               user_survey_response=user_survey_response,
                                                               response_text=payload)

            return HttpResponse(200)
        elif question_type == 'multiple_options':
            payload = request.POST.getlist('payload[]')
            choice_ids = [int(item) for item in payload]
            choices = Choice.objects.filter(id__in=choice_ids)
            if len(choices) != len(choice_ids):
                return HttpResponse(400)

            response = Response.objects.filter(question=question, user_survey_response=user_survey_response).first()
            if not response:
                response = Response.objects.create(question=question, user_survey_response=user_survey_response)
                # Delete previous choices that are not in the new choices
            previous_choices = response.choices.all()
            previous_choice_ids = set(previous_choices.values_list('id', flat=True))
            new_choice_ids = set(choice_ids)

            choices_to_delete = previous_choice_ids - new_choice_ids
            if choices_to_delete:
                ResponseChoice.objects.filter(response=response, choice_id__in=choices_to_delete).delete()

            # Add new choices
            for choice in choices:
                ResponseChoice.find_or_create_response_choice(response, choice)

            return HttpResponse(200)
        else:
            choice_id = int(request.POST.get('payload'))
            choice = Choice.objects.filter(id=choice_id).first()
            if not choice:
                return HttpResponse(400)

            response = Response.objects.filter(question=question, user_survey_response=user_survey_response).first()
            if not response:
                response = Response.objects.create(question=question, user_survey_response=user_survey_response)
            response_choice = ResponseChoice.find_or_create_response_choice(response, choice)

            # Delete all other response choices if the question is a single choice question, filtered by user_id and guest_id
            if user:
                ResponseChoice.objects.filter(
                    response__question_id=question.id,
                    response__user_survey_response__user_id=user.id
                ).exclude(id=response_choice.id).delete()
                return HttpResponse(200)
            else:
                ResponseChoice.objects.filter(
                    response__question_id=question.id,
                    response__user_survey_response__guest_id=guest_id
                ).exclude(id=response_choice.id).delete()
                return HttpResponse(200)

    def all_results(request):
        # Fetch all surveys
        surveys = Survey.objects.filter(is_result_released=True)

        # Prepare data for charts for all surveys
        surveys_chart_data = []

        for survey in surveys:
            questions = survey.questions.prefetch_related('responses').all()

            questions_chart_data = []
            for question in questions:
                # Initialize chart data structure for each question
                chart_data = {'question_text': question.question_text, 'chart_type': question.chart_type, 'data': []}

                # Process only the questions that can be represented in charts
                if question.question_type in [Question.MULTIPLE_CHOICE, Question.CHECKBOX, Question.DROPDOWN]:
                    responses = [response.response_text for response in question.responses.all()]
                    # Count occurrences of each response
                    response_counts = Counter(responses)

                    # Prepare data for the chart
                    for choice in question.choices.all():
                        chart_data['data'].append({'label': choice.choice_text, 'value': response_counts.get(choice.choice_text, 0)})

                elif question.question_type in [Question.TEXT, Question.LONG_TEXT]:
                    responses = question.responses.all()
                    chart_data['text_responses'] = [response.response_text for response in responses]

                elif question.question_type == Question.SLIDING_SCALE:
                    average_response = question.responses.aggregate(Avg('response_text'))['response_text__avg']
                    if average_response is not None:
                        chart_data['chart_type'] = 'BC'
                        chart_data['data'] = [{'label': 'Average Scale', 'value': round(average_response, 2)}]

                # Add the prepared data for this question to the list for the current survey
                questions_chart_data.append(chart_data)

            # Add the survey and its questions chart data to the surveys chart data list
            surveys_chart_data.append({
                'survey_title': survey.title,
                'questions_chart_data': questions_chart_data
            })

        context = {
            'surveys_chart_data': surveys_chart_data,
        }

        return render(request, 'survey/all_results.html', context)
