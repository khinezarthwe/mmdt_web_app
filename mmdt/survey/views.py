from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from .forms import create_survey_form
from .models import Question, Response, Survey
from django.contrib import messages

class SurveyPage:
    def index(request):
        surveys = Survey.objects.filter(is_active=True)
        return render(request, 'survey/index.html', {'surveys': surveys})

    def survey_detail(request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        questions = survey.questions.all().order_by('pub_date')
        print("Request and survey_id", request, survey_id)

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
        form = create_survey_form(current_page_questions)
        session_key = f'survey_{survey_id}_responses'
        # print ("session data on GET request:", request.session.get(session_key))
        if not request.session[session_key]:
            request.session[session_key]= {}
        if request.method == 'POST':
            print("Form is being submitted...")
            for key, data in request.POST.items():
                if key.startswith("question"):
                    request.session[session_key].update({key: request.POST.getlist(key)})
            print("Session data on POST request", request.session[session_key])
            if current_page_questions.has_next():
                next_page = current_page_questions.next_page_number()
                print("Redirecting to next page:", next_page)
                
                for question_id, responses in request.session[session_key].items():
                    question = get_object_or_404(Question, pk=question_id.split("_")[1])
                    for response_text in responses:
                        Response.objects.create(question=question, response_text=response_text)
                    return HttpResponseRedirect(f'?page={next_page}')
            # please continue for save data to db when user click submit, you already have all response data in request.session[session_key]
            # please clear the session data after form save the data to database
            else:
                if 'submit_form' in request.POST:
                    try:
                        with transaction.atomic():
                            print("Saving responses to the database")
                            for question_id, responses in request.session[session_key].items():
                                question = get_object_or_404(Question, pk=question_id.split("_")[1])
                                for response_text in responses:
                                    Response.objects.create(question=question, response_text=response_text)
                    except Exception as e:
                        print("Error occured while saving responses:", e)
                        messages.error(request, "Error while saving responses")
                        return HttpResponseRedirect(request.path)
                    else:
                        print("Responses saved successfully.")
                        messages.success(request, "Saved Responses")
                        del request.session[session_key]
                        return HttpResponseRedirect('/')
                else:
                    print("Not submitting the whole form")
        context = {
            'survey': survey,
            'form': form,
            'current_page_questions': current_page_questions,
        }
        return render(request, 'survey/survey_detail.html', context)

        # responses = request.session.get(session_key, {})
        #
        # initial_data = {}
        # for question in current_page_questions:
        #     if f'question_{question.id}' in responses:
        #         initial_data[f'question_{question.id}'] = responses[f'question_{question.id}']
        #
        # # SurveyForm = create_survey_form(survey)
        # if request.method == "POST":
        #     form = create_survey_form(survey)(request.POST)
        #     if form.is_valid():
        #
        #         for question in current_page_questions:
        #             response_text = form.cleaned_data.get(f'question_{question.id}')
        #             if response_text:
        #                 responses[f'question_{question.id}'] = response_text
        #
        #         request.session[session_key] = responses
        #
        #         if current_page_questions.has_next():
        #             next_page = current_page_questions.next_page_number()
        #             return HttpResponseRedirect(f'?page={next_page}')
        #         else:
        #             for question_id, response_text in responses.items():
        #                 question_id = int(question_id.split('_')[1])
        #                 question = Question.objects.get(id=question_id)
        #                 if question.question_type == Question.CHECKBOX:
        #                     # For checkbox questions, response_text is a list
        #                     choices = Choice.objects.filter(id__in=response_text)
        #                     response_text = ", ".join(choice.choice_text for choice in choices)
        #                 elif question.question_type == Question.MULTIPLE_CHOICE:
        #                     # For Multiple Choice questions, response_text is the selected choice ID
        #                     choice_id = int(response_text)
        #                     selected_choice = get_object_or_404(Choice, id=choice_id)
        #                     response_text = selected_choice.choice_text
        #
        #                 elif question.question_type == Question.SLIDING_SCALE:
        #                     selected_index = int(response_text)
        #                     # Ensure the index is within the range of available choices
        #                     choices = question.choices.all()
        #                     if 0 <= selected_index < len(choices):
        #                         selected_choice = choices[selected_index]
        #                         response_text = {selected_choice.value}
        #
        #                 elif question.question_type == Question.DROPDOWN:
        #                     # For drop-down questions, response_text is the selected choice text
        #                     choice = get_object_or_404(Choice, id=response_text)
        #                     response_text = choice.choice_text
        #                 # Create Response object
        #                 Response.objects.create(question=question, response_text=response_text)
        #         del request.session[session_key]
        #         # Display success message
        #         messages.success(request, 'Survey submitted successfully!')
        #         return redirect('survey:index')
        # else:
        #     form = create_survey_form(survey)(initial=initial_data)
