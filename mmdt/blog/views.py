import pickle
import numpy as np
from django.views import generic
from django.views.generic import TemplateView
from .forms import CommentForm, FeedbackAnalyzerForm
from .models import Post
from .forms import CommentForm
from django.shortcuts import render

class Home(TemplateView):
    template_name = 'index.html'


class AboutUs(TemplateView):
    template_name = 'about.html'


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
        return Post.objects.filter(status=1).order_by('-created_on')


class PostDetailView(generic.View):
    template_name = 'post_detail.html'

    def get(self, request, slug):
        post = Post.objects.get(slug=slug)
        comments = post.comments.filter(active=True)
        comment_form = CommentForm()
        return render(request, self.template_name, {'post': post, 'comments': comments, 'comment_form': comment_form})

    def post(self, request, slug):
        post = Post.objects.get(slug=slug)
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()

        comments = post.comments.filter(active=True)
        return render(request, self.template_name, {'post': post, 'comments': comments, 'comment_form': comment_form})

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
