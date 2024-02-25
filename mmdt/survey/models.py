import datetime
from django.contrib import admin
from django.db import models
from django.utils import timezone

class SurveyForm(models.Model):
    form_name = models.CharField(max_length=255, default = 'DefaultFormName')
    form_id = models.AutoField(primary_key=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.form_name

class SurveyQuestion(models.Model):
    question_name = models.CharField(max_length=255)
    pub_date = models.DateTimeField("date published")
    is_enabled = models.BooleanField(default=True)
    survey_group = models.ForeignKey(SurveyForm, on_delete=models.CASCADE, related_name='questions', null=True)

    def __str__(self):
        return self.question_name
    
    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

class Response(models.Model):
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text
