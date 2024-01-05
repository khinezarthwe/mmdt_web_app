from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from .models import Question, Choice


class PollHomePage:
    def index(request):
        questions = Question.objects.order_by('-pub_date').all()
        paginator = Paginator(questions, 2)
        page_number = request.GET.get("page")
        try:
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)
        except EmptyPage:
            page_obj = paginator.get_page(paginator.num_pages)
        # latest_question_list = Question.objects.order_by('-pub_date')[:5]
        for question in questions:
            question.choices = question.choice_set.all()
            question.voted = request.GET.get('voted') == 'true'
        user_has_voted = request.GET.get('voted') == 'true'
        context = {
            'questions': page_obj, 
            'user_has_voted': user_has_voted,
            'paginator': paginator,
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



