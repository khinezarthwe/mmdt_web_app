from django import forms
from .models import Question
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

def create_survey_form(survey):
    class SurveyForm(forms.Form):
        def __init__(self, *args, **kwargs):
            super(SurveyForm, self).__init__(*args, **kwargs)
            for question in survey.questions.all():
                field_name = f'question_{question.id}'
                if question.question_type == Question.TEXT:
                    self.fields[field_name] = forms.CharField(label=question.question_text, required=False)
                elif question.question_type == Question.MULTIPLE_CHOICE:
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    self.fields[field_name] = forms.ChoiceField(choices=choices, label=question.question_text, widget=forms.RadioSelect, required=False)
                elif question.question_type == Question.CHECKBOX:
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    self.fields[field_name] = forms.MultipleChoiceField(choices=choices, label=question.question_text, widget=forms.CheckboxSelectMultiple, required=False)
                elif question.question_type == Question.LONG_TEXT:
                    self.fields[field_name] = forms.CharField(widget=forms.Textarea, label=question.question_text, required=False)
                elif question.question_type == Question.DROPDOWN:
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    self.fields[field_name] = forms.ChoiceField(choices=choices, label=question.question_text, required=False)
                elif question.question_type == Question.SLIDING_SCALE:
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    self.fields[field_name] = forms.IntegerField(label=question.question_text, widget=forms.NumberInput(attrs={'type': 'range'}), required=False)
    return SurveyForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
