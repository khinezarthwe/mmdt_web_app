# Generated by Django 4.2.4 on 2024-05-19 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0011_alter_response_choice'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='optional',
            field=models.BooleanField(default=False),
        ),
    ]
