from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from .models import Question, Choice
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



class PollHomePage:
    def index(request):
        latest_question_list = Question.objects.order_by('-pub_date')[:5]

        questions = Question.objects.all()

        paginator = Paginator(questions, 5)
        page = request.GET.get('page', 1)

        try:
            page_obj = paginator.page(page)

        except PageNotAnInteger:
            page_obj = paginator.page(1)

        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
          

        for question in latest_question_list:
            question.choices = question.choice_set.all()
            question.voted = request.GET.get('voted') == 'true'

        user_has_voted = request.GET.get('voted') == 'true'

        context = {
            'latest_question_list': latest_question_list, 
            'user_has_voted': user_has_voted,
            "page": page,
            "page_obj": page_obj,
            }
        return render(request, 'polls/index.html', context)

    def vote(request):
        questions = Question.objects.order_by('-pub_date')[:5]
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



