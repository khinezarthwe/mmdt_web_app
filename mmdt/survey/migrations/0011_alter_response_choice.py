# Generated by Django 4.2.4 on 2024-05-12 04:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("survey", "0010_usersurveyresponse_guest_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="response",
            name="choice",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="responses",
                to="survey.choice",
            ),
        ),
    ]