# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0012_cohort_subscriberrequest_cohort"),
        ("users", "0003_userprofile_current_cohort"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="subscriber_request",
            field=models.ForeignKey(
                blank=True,
                help_text="Associated approved subscriber request",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="user_profiles",
                to="blog.subscriberrequest",
            ),
        ),
    ]
