# Generated by Django 4.2.4 on 2024-05-19 02:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0012_question_optional'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResponseChoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='survey.choice')),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='survey.response')),
            ],
        ),
        migrations.AddField(
            model_name='response',
            name='choices',
            field=models.ManyToManyField(blank=True, through='survey.ResponseChoice', to='survey.choice'),
        ),
    ]
