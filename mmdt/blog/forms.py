from django import forms
from django.core.exceptions import ValidationError
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
        self.fields['mmdt_email'].widget.attrs['placeholder'] = \
            'your mmdt mail (if you have joined the mmdt before)'
        self.fields['country'].widget.attrs['placeholder'] = 'Current residing country'
        self.fields['city'].widget.attrs['placeholder'] = 'Current residing city'
        self.fields['job_title'].widget.attrs['placeholder'] = 'Job Title'
        self.fields['message'].widget.attrs['placeholder'] = \
            'If you are applying for a fee waiver, please write your message here.'
        self.fields['plan'].widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        if SubscriberRequest.objects.filter(email__iexact=email).exists():
            raise ValidationError("A subscription request with this email already exists.")
        return email

    class Meta:
        model = SubscriberRequest
        fields = [
            'name', 'email', 'mmdt_email', 'country', 'city',
            'job_title', 'free_waiver', 'plan', 'message',
        ]
