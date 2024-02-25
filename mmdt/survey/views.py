from django.shortcuts import render, redirect
from .models import SurveyForm, Response
from django.core.paginator import Paginator

class SurveyPage:
    def index(request):
        # Check if the request method is POST (indicating form submission)
        if request.method == "POST":
            # Iterate through the POST data and create a Response object for each response
            for key, value in request.POST.items():
                # Check if the key starts with 'response_' to identify survey responses
                if key.startswith('response_'):
                    # Extract the question ID from the key
                    question_id = key.split('_')[1]
                    text = value # The actual response text
                    # If the response text is not empty, create a new Response object
                    if text:
                        Response.objects.create(question_id=question_id, text=text)
            # Redirect to the survey page
            return redirect('/survey')
        # Fetch active survey forms and prefetch related questions
        active_forms = SurveyForm.objects.filter(is_active=True).prefetch_related('questions')
        # Pagination or future use
        paginator = Paginator(active_forms, 5)

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {'page_obj': page_obj}
        return render(request, 'survey/index.html', context)