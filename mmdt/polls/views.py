from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from .models import Question, Choice, ActiveGroup
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage

from django.contrib.auth import login
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('polls:index')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'polls/register.html', {'form': form})


class PollHomePage:
    def index(request):
         # Retrieve questions for all active groups with is_enabled=True
        active_groups = ActiveGroup.objects.filter(is_active=True)
        all_questions = Question.objects.filter(is_enabled=True, poll_group__in=active_groups.values_list('group_id', flat=True)).order_by('poll_group', '-pub_date')       
       
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
        # Get the current page number from the request's GET parameters
        page = request.GET.get('page', 1)
        active_groups = ActiveGroup.objects.filter(is_active=True)
        # Retrieve questions for the current page
        questions = Question.objects.filter(is_enabled=True, poll_group__in=active_groups.values_list('group_id', flat=True)).order_by('poll_group', '-pub_date')  
        paginator = Paginator(questions, 5)
        
        try:
            current_page_questions = paginator.page(page)
        except (EmptyPage, InvalidPage):
            # If the page is out of range, deliver the last page of results.
            current_page_questions = paginator.page(paginator.num_pages)

        try:
            for question in current_page_questions:
                # Check if the question requires registration
                if question.poll_group and question.poll_group.registration_required and not request.user.is_authenticated:
                    messages.warning(request, f'You need to log in to vote for the questions!!')
                    return HttpResponseRedirect(reverse('polls:index') + f"?page={page}")
                
                # Proceed with normal logic
                selected_choice_id = request.POST.get(f'question_{question.id}')
                if not selected_choice_id:
                    raise ValueError(f'No choice selected for question "{question.question_text}".')

                selected_choice = question.choice_set.get(pk=selected_choice_id)
                selected_choice.votes += 1
                selected_choice.save()

            if 'vote_again' in request.POST:
                return HttpResponseRedirect(reverse('polls:index') + f"?page={page}")
            # Redirect with 'voted' flag after successful voting
            return HttpResponseRedirect(reverse('polls:index') + f"?voted=true&page={page}")

        except (KeyError, Choice.DoesNotExist, ValueError) as e:
            # Display an error message and redirect back to the index page
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse('polls:index') + f"?page={page}")
            