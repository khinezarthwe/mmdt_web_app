import datetime
from django.contrib import admin
from django.db import models
from django.utils import timezone

class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
    def is_current(self):
        # Returns True if the survey is currently active based on its start and end dates.
        now = timezone.now()
        return self.start_date <= now and (self.end_date is None or now <= self.end_date)

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
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published', null=True, default=timezone.now)
    is_enabled = models.BooleanField(default=True)
    question_type = models.CharField(max_length=255, choices=QUESTION_TYPES, default=TEXT)

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=255)

    def __str__(self):
        return self.choice_text
    
class Response(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    response_text = models.TextField()

    def __str__(self):
        return f"Response to {self.question.question_text}: {self.response_text}"
    