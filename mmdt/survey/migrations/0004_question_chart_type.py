# Generated by Django 4.2.4 on 2024-03-26 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_alter_question_pub_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='chart_type',
            field=models.CharField(blank=True, choices=[('PC', 'Pie Chart'), ('BC', 'Bar Chart')], default='PC', max_length=2, null=True),
        ),
    ]
