from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    registration_required = models.BooleanField(default=False)
    is_result_released = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def is_current(self):
        # Returns True if the survey is currently active based on its start and end dates.
        now = timezone.now()
        return self.start_date <= now and (self.end_date is None or now <= self.end_date)

class UserSurveyResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    guest_id=models.CharField(max_length=255, null=True, blank=True)
    is_draft = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, null=True)
    updated_at = models.DateTimeField(default=timezone.now, null=True)

    def user_display(self):
        return self.user.username if self.user else 'Anonymous' + ' (' + self.guest_id or '' + ')'

    @staticmethod
    def find_or_create_draft_guest(guest_id, survey):
        user_survey_response = UserSurveyResponse.objects.filter(guest_id=guest_id, survey=survey, is_draft=True).first()
        if user_survey_response is None:
            user_survey_response = UserSurveyResponse.objects.create(guest_id=guest_id, survey=survey, is_draft=True)
        return user_survey_response

    @staticmethod
    def find_or_create_draft_user(user, survey):
        user_survey_response = UserSurveyResponse.objects.filter(user=user, survey=survey, is_draft=True).first()
        if user_survey_response is None:
            user_survey_response = UserSurveyResponse.objects.create(user=user, survey=survey, is_draft=True)
        return user_survey_response

class Question(models.Model):
    TEXT = 'T'
    MULTIPLE_CHOICE = 'MC'
    CHECKBOX = 'CB'
    LONG_TEXT = 'LT'
    DROPDOWN = 'DD'
    SLIDING_SCALE = 'SS'
    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (CHECKBOX, 'Check Box'),
        (TEXT, 'Text'),
        (LONG_TEXT, 'Long Text'),
        (DROPDOWN, 'Drop-down'),
        (SLIDING_SCALE, 'Sliding Scale')
    ]
    CHART_TYPES = [
        ('PC', 'Pie Chart'),
        ('BC', 'Bar Chart')
    ]
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published', null=True, default=timezone.now)
    is_enabled = models.BooleanField(default=True)
    question_type = models.CharField(max_length=255, choices=QUESTION_TYPES, default=TEXT)
    chart_type = models.CharField(max_length=2, choices=CHART_TYPES, default='PC', null=True, blank=True)

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=255)

    def __str__(self):
        return self.choice_text


class Response(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, related_name='responses', null=True, blank=True)
    user_survey_response = models.ForeignKey(UserSurveyResponse, on_delete=models.CASCADE, related_name='responses')
    response_text = models.TextField()

    def __str__(self):
        return f"Response to {self.question.question_text}: {self.response_text}"
