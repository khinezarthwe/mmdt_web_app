from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Question, Choice


class PollHomePage:
    def index(request):
        # latest_question_list = Question.objects.order_by('-pub_date')[:5]
        latest_question_list = Question.objects.all().order_by('-pub_date')

        try:
            page = request.GET.get('page')
            page = int(page)
        except:
            page = 1

        polls_per_page = 5
        paginator = Paginator(latest_question_list, polls_per_page)
        latest_question_list = paginator.page(page)
        request.session['current_polls_page'] = page

        for question in latest_question_list:
            question.choices = question.choice_set.all()
            question.voted = request.GET.get('voted') == 'true'
        user_has_voted = request.GET.get('voted') == 'true'
        context = {'latest_question_list': latest_question_list, 'user_has_voted': user_has_voted, 'paginated_by': 5, 'is_paginated': True}
        return render(request, 'polls/index.html', context)

    def vote(request):

        page = request.session.get('current_polls_page')
        current_page = f"?page={page}"

        if page == 1:
            params = "?voted=true"
        else:
            params = f"?voted=true&&page={page}"

        try:
            if 'vote_again' in request.POST:
                return HttpResponseRedirect(reverse('polls:index') + current_page)
        except:
            pass

        # questions = Question.objects.order_by('-pub_date')[:5]
        questions = Question.objects.all().order_by('-pub_date')

        polls_per_page = 5
        paginator = Paginator(questions, polls_per_page)
        questions = paginator.page(page)

        try:
            for question in questions:
                selected_choice_id = request.POST.get(f'question_{question.id}')
                if not selected_choice_id:
                    # If no choice was selected for a question, raise an error
                    raise ValueError(f'No choice selected for question "{question.question_text}".')

                selected_choice = question.choice_set.get(pk=selected_choice_id)
                selected_choice.votes += 1
                selected_choice.save()
            # Redirect with 'voted' flag with current page after successful voting
            return HttpResponseRedirect(reverse('polls:index') + params)

        except (KeyError, Choice.DoesNotExist, ValueError) as e:
            # Display an error message and redirect back to the index page
            messages.error(request, str(e))
            print("\n\n I worked----- \n\n")
            return HttpResponseRedirect(reverse('polls:index') + current_page)



