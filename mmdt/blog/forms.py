from django import forms
from django.forms import ModelForm
from .models import Comment


class CommentForm(ModelForm):
    """Form for adding comments to a post."""
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body')


class FeedbackAnalyzerForm(forms.Form):
    """Form for analyzing feedback."""
    feedback = forms.CharField(
        label="Enter your feedback",
        max_length=3000,
        widget=forms.Textarea(attrs={'id': 'input-inbox'})
    )
