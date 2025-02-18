import pickle

import numpy as np
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views import generic
from django.views.generic import TemplateView

from .forms import CommentForm, FeedbackAnalyzerForm
from .forms import SubscriberRequestForm
from .models import Post


class Home(TemplateView):
    template_name = 'index.html'


class AboutUs(TemplateView):
    template_name = 'about.html'


class SubscriberInfo(TemplateView):
    template_name = 'subscriber.html'


class OurProject(TemplateView):
    template_name = 'index.html'


class StProject(TemplateView):
    template_name = 'st_project.html'


class PostListView(generic.ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'post_list'
    paginate_by = 6

    def get_queryset(self):
        return Post.objects.filter(status=1, subscribers_only=False).order_by('-created_on')


class PostListOnlySubscriberView(LoginRequiredMixin, generic.ListView):
    model = Post
    template_name = 'post_list_only_subscriber.html'
    context_object_name = 'post_list_only_subscriber'
    paginate_by = 6

    def get_queryset(self):
        return Post.objects.filter(status=1, subscribers_only=True).order_by('-created_on')


def subscriptions_upgrade(request):
    return render(request, 'subscriptions_upgrade.html')


class PostDetailView(generic.DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(self.get_queryset())

        # Check for subscriber-only content
        if self.object.subscribers_only and not request.user.is_authenticated:
            return render(request, 'subscriptions_upgrade.html')

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        post = super().get_object()
        post.view_count += 1
        post.save()
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.filter(active=True)
        if 'comment_form' not in context:
            context['comment_form'] = CommentForm()
        return context


class PlayGround(generic.FormView):
    template_name = 'playground/feedback_analyzer.html'
    form_class = FeedbackAnalyzerForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cls = self.load_classifier()

    @staticmethod
    def load_classifier():
        try:
            input_file = 'ml_models/model_C=1.0.bin'
            with open(input_file, 'rb') as f_in:
                cls = pickle.load(f_in)
            return cls
        except FileNotFoundError:
            return None

    def status(self, df):
        if self.cls is not None:
            y_class = self.cls.predict([df])
            y_pred_prob = self.cls.predict_proba([df])
            return y_class, y_pred_prob
        else:
            return None, None

    def form_valid(self, form):
        input_feedback = form.cleaned_data['feedback']
        y_class, confidence = self.status(input_feedback)
        result = y_class[0].title() if y_class else 0.0
        confidence = np.round(confidence[0][0], 3) if confidence is not None else "We can't estimate it"
        return self.render_to_response(self.get_context_data(form=form, result=result, confidence=confidence))


def subscriber_request_success(request):
    return render(request, 'subscriber_request_success.html')


def subscriber_request(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = SubscriberRequestForm()

    if request.method == 'POST':
        form = SubscriberRequestForm(request.POST)
        if form.is_valid():

            subscriber = form.save()
            user_subject = 'Thank you for your subscription request'
            html_message = render_to_string('emails/user_confirmation.html', {
                'name': subscriber.name,
                'plan': subscriber.get_plan_display(),
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject=user_subject,
                message=plain_message,  # plain text version
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[subscriber.email],
                html_message=html_message,  # HTML version
                fail_silently=False,
            )

            messages.success(request, 'Your subscriber request has been submitted successfully.')
            return redirect('subscriber_request_success')

    return render(request, 'subscriber.html', {'form': form})
