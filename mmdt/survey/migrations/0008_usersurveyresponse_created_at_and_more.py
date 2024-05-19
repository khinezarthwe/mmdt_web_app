# Generated by Django 4.2.4 on 2024-05-06 07:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("survey", "0007_remove_response_question_response_choice_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersurveyresponse",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AddField(
            model_name="usersurveyresponse",
            name="is_draft",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="usersurveyresponse",
            name="updated_at",
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name="response",
            name="user_survey_response",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="responses",
                to="survey.usersurveyresponse",
            ),
        ),
        migrations.AlterField(
            model_name="usersurveyresponse",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]