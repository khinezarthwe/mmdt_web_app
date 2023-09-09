from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic import TemplateView

from .forms import CommentForm
from .models import Post

class Home(TemplateView):
    template_name = 'index.html'

class PostList(generic.ListView):
    def post_list(request):
        object_list = Post.objects.filter(status=1).order_by('-created_on')
        paginator = Paginator(object_list, 3)
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
