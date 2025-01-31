from django import forms
from django.forms import ModelForm

from .models import Comment
from .models import SubscriberRequest


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


class SubscriberRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = 'Name'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['country'].widget.attrs['placeholder'] = 'Current residing country'
        self.fields['city'].widget.attrs['placeholder'] = 'Current residing city'
        self.fields['job_title'].widget.attrs['placeholder'] = 'Job Title'
        self.fields['message'].widget.attrs['placeholder'] = 'Enter your message'

    class Meta:
        model = SubscriberRequest
        fields = [
            'name', 'email', 'country', 'city',
            'job_title', 'looking_for_job',
            'free_waiver', 'message'
        ]
