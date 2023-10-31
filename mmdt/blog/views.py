import pickle

import numpy as np
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views import generic
from django.views.generic import TemplateView

from .forms import CommentForm
from .forms import FeedbackAnalyzerForm
from .models import Post


class Home(TemplateView):
    template_name = 'index.html'


class AboutUs(TemplateView):
    template_name = 'about.html'


class OurProject(TemplateView):
    template_name = 'index.html'


class StProject(TemplateView):
    template_name = 'st_project.html'



class PostList(generic.ListView):
    def post_list(request):
        object_list = Post.objects.filter(status=1).order_by('-created_on')
        paginator = Paginator(object_list, 6)
        if request.method == 'GET':
            page = request.GET.get('page')
        try:
            post_list = paginator.page(page)
        except PageNotAnInteger:
            post_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range deliver last page of results
            post_list = paginator.page(paginator.num_pages)
        return render(request,
                      'post_list.html',
                      {'page': page,
                       'post_list': post_list})


class PostDetail(generic.DetailView):
    def post_detail(request, slug):
        post = get_object_or_404(Post, slug=slug)
        if post:
            post.view_count += 1
            post.save()
        comments = post.comments.filter(active=True)
        new_comment = None    # Comment posted
        if request.method == 'POST':
            comment_form = CommentForm(data=request.POST)
            if comment_form.is_valid():
                # Create Comment object but don't save to database yet
                new_comment = comment_form.save(commit=False)
                # Assign the current post to the comment
                new_comment.post = post
                # Save the comment to the database
                new_comment.save()
        else:
            comment_form = CommentForm()
        return render(request, 'post_detail.html', {'post': post,
                                               'comments': comments,
                                               'new_comment': new_comment,
                                               'comment_form': comment_form})


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

