from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from .models import Question, Choice


class PollHomePage:
    def index(request):
        latest_question_list = Question.objects.order_by('-pub_date')[:5]
        for question in latest_question_list:
            question.choices = question.choice_set.all()
            question.voted = request.GET.get('voted') == 'true'
        user_has_voted = request.GET.get('voted') == 'true'
        context = {'latest_question_list': latest_question_list, 'user_has_voted': user_has_voted}
        return render(request, 'polls/index.html', context)

    def vote(request):
        questions = Question.objects.order_by('-pub_date')[:5]
        try:
            for question in questions:
                if not question.is_enabled:
                    #If the question is disabled, raise an error to prevent voting on that question
                    raise ValueError(f'Voting is disabled for question "{question.question_text}".')

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



