from .models import Comment
from django.forms import ModelForm
# https://docs.djangoproject.com/en/4.2/topics/forms/modelforms/ https://pypi.org/project/crispy-bootstrap4/


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body')
