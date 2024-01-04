from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from .models import Question, Choice


class PollHomePage:
    def index(request):
        # Retrieve all questions from the database
        all_questions = Question.objects.order_by('-pub_date')

        # Pagination
        paginator = Paginator(all_questions, 5)  # Show 5 questions per page
        page = request.GET.get('page')

        try:
            latest_question_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            latest_question_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver the last page.
            latest_question_list = paginator.page(paginator.num_pages)

        for question in latest_question_list:
            question.choices = question.choice_set.all()
            question.voted = request.GET.get('voted') == 'true'

        user_has_voted = request.GET.get('voted') == 'true'
        context = {
            'latest_question_list': latest_question_list,
            'user_has_voted': user_has_voted,
        }
        return render(request, 'polls/index.html', context)

    def vote(request):
        questions = Question.objects.order_by('-pub_date')[:5]
        try:
            for question in questions:
                selected_choice_id = request.POST.get(
                    f'question_{question.id}')
                if not selected_choice_id:
                    raise ValueError(
                        f'No choice selected for question "{question.question_text}".')

                selected_choice = question.choice_set.get(
                    pk=selected_choice_id)
                selected_choice.votes += 1
                selected_choice.save()

            if 'vote_again' in request.POST:
                return HttpResponseRedirect(reverse('polls:index'))

            return HttpResponseRedirect(reverse('polls:index') + "?voted=true")
        except (KeyError, Choice.DoesNotExist, ValueError) as e:
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse('polls:index'))
