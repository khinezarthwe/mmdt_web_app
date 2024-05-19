from django import forms
from .models import Question
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

def create_survey_form(survey, user_survey_response, current_page_questions):
    responses = user_survey_response.responses.all() if user_survey_response else []
    response_by_question = {}
    for r in responses:
        if r.question_id not in response_by_question:
            response_by_question[r.question_id] = []
        response_by_question[r.question_id].append(r)
    class SurveyForm(forms.Form):
        def __init__(self, *args, **kwargs):
            super(SurveyForm, self).__init__(*args, **kwargs)
            for question in current_page_questions:
                field_name = f'question_{question.id}'
                existing_response = response_by_question.get(question.id, [None])[0]
                if question.question_type == Question.TEXT:
                    initial_value = existing_response.response_text if existing_response else None
                    self.fields[field_name] = forms.CharField(
                        label=question.question_text, required=not question.optional, initial=initial_value)
                elif question.question_type == Question.MULTIPLE_CHOICE:
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    initial_value = existing_response.choices.first().id if existing_response else None
                    self.fields[field_name] = forms.ChoiceField(choices=choices, label=question.question_text, widget=forms.RadioSelect, required=not question.optional, initial=initial_value)
                elif question.question_type == Question.CHECKBOX:
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    initial_values = [c.id for c in existing_response.choices.all()]
                    self.fields[field_name] = forms.MultipleChoiceField(choices=choices, label=question.question_text, widget=forms.CheckboxSelectMultiple, required=not question.optional, initial=initial_values)
                elif question.question_type == Question.LONG_TEXT:
                    initial_value = existing_response.response_text if existing_response else None
                    self.fields[field_name] = forms.CharField(widget=forms.Textarea, label=question.question_text, required=not question.optional, initial=initial_value)
                elif question.question_type == Question.DROPDOWN:
                    initial_value = existing_response.choices.first().id if existing_response else None
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    self.fields[field_name] = forms.ChoiceField(choices=choices, label=question.question_text, required=not question.optional, initial=initial_value)
                elif question.question_type == Question.SLIDING_SCALE:
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    initial_value = existing_response.choices.first().id if existing_response else None
                    self.fields[field_name] = forms.IntegerField(label=question.question_text, widget=forms.NumberInput(attrs={'type': 'range'}), required=not question.optional, initial=initial_value)
    return SurveyForm
