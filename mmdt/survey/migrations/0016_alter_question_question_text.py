# Generated by Django 4.2.4 on 2024-07-11 01:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0015_survey_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_text',
            field=models.CharField(max_length=1000),
        ),
    ]