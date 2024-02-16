import datetime

from django.contrib import admin
from django.db import models
from django.utils import timezone

class ActiveGroup(models.Model):
    group_id = models.IntegerField(primary_key=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Group {self.group_id}"

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    is_enabled = models.BooleanField(default=True)
    image = models.ImageField(upload_to="images/poll_images", blank=True, null=True) # New field for image upload 
    poll_group = models.ForeignKey(ActiveGroup, on_delete=models.CASCADE, related_name='questions', null=True)


    def __str__(self):
        return self.question_text

    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text
