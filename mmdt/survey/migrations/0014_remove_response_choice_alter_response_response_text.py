# Generated by Django 4.2.4 on 2024-05-19 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0013_responsechoice_response_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='response',
            name='choice',
        ),
        migrations.AlterField(
            model_name='response',
            name='response_text',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
