from django import forms
from django.forms import ModelForm

from .models import Comment


# https://docs.djangoproject.com/en/4.2/topics/forms/modelforms/ https://pypi.org/project/crispy-bootstrap4/

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body')


class FeedbackAnalyzerForm(forms.Form):
    feedback = forms.CharField(
        label="Enter your feedback",
        max_length=3000,
        widget=forms.Textarea(attrs={'id': 'input-inbox'})
    )
