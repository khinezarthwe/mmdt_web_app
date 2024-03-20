from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import Question, Choice, ActiveGroup
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def release_results(request, group_id):
    group = get_object_or_404(ActiveGroup, pk=group_id)
    group.is_results_released = True
    group.save()
    return HttpResponseRedirect(reverse('polls:all_results'))


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
        
        # Check if the user is an admin
        is_admin = request.user.is_staff

        # Check if results are released
        active_group = ActiveGroup.objects.filter(is_results_released=True).first()
        results_released = active_group is not None

        context = {
            'latest_question_list': latest_question_list,
            'user_has_voted': user_has_voted,
            'is_admin': is_admin,
            'results_released': results_released,
        }
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
        
    def all_results(request):
        # Fetch all questions with is_enabled=True for admins
        all_questions = Question.objects.filter(is_enabled=True).order_by('poll_group', '-pub_date')

        # If the user is not an admin, filter based on additional conditions
        if not request.user.is_staff:
            # Check if results are released
            active_group = ActiveGroup.objects.filter(is_results_released=True).first()
            if not active_group:
                return HttpResponseForbidden("Results are not released yet.")

            # Fetch questions related to the active group with additional conditions
            all_questions = all_questions.filter(
                poll_group__is_active=True
            )

        # If there are no questions meeting the conditions, return an appropriate response
        if not all_questions:
            return HttpResponseForbidden("No results available for the specified conditions.")

        # Check if the user is an admin
        is_admin = request.user.is_staff

        return render(request, 'polls/all_results.html', {'all_questions': all_questions, 'is_admin': is_admin})

