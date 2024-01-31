from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from .models import Question, Choice
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class PollHomePage:
    def index(request):
        # Get all polls, not just the latest 5
        all_questions = Question.objects.order_by('-pub_date')
        
        # Set the number of polls to display per page
        polls_per_page = 5
        paginator = Paginator(all_questions, polls_per_page)

        # Get the current page number from the request's GET parameters
        page = request.GET.get('page')

        try:
            latest_question_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            latest_question_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page of results.
            latest_question_list = paginator.page(paginator.num_pages)

        for question in latest_question_list:
            question.choices = question.choice_set.all()
            question.voted = request.GET.get('voted') == 'true'

        user_has_voted = request.GET.get('voted') == 'true'
        context = {'latest_question_list': latest_question_list, 'user_has_voted': user_has_voted}
        return render(request, 'polls/index.html', context)

    def vote(request):
        questions = Question.objects.filter(is_enabled=True).order_by('-pub_date')[:5]
        try:
            for question in questions:
                selected_choice_id = request.POST.get(f'question_{question.id}')
                if not selected_choice_id:
                    # If no choice was selected for a question, raise an error
                    raise ValueError(f'No choice selected for question "{question.question_text}".')

                selected_choice = question.choice_set.get(pk=selected_choice_id)
                selected_choice.votes += 1
                selected_choice.save()
            if 'vote_again' in request.POST:
                return HttpResponseRedirect(reverse('polls:index'))
            # Redirect with 'voted' flag after successful voting
            return HttpResponseRedirect(reverse('polls:index') + "?voted=true")

        except (KeyError, Choice.DoesNotExist, ValueError) as e:
            # Display an error message and redirect back to the index page
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse('polls:index'))



