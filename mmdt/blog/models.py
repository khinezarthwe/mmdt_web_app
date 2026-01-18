from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

STATUS = (
    (0, "Draft"),
    (1, "Publish")
)


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=STATUS, default=0)
    image = models.ImageField(upload_to='images', null=True, blank=True)
    view_count = models.IntegerField(default=0, null=True, blank=True)
    subscribers_only = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return 'Comment {} by {}'.format(self.body, self.name)


class Cohort(models.Model):
    cohort_id = models.CharField(max_length=20, primary_key=True, help_text="Format: YYYY_MM (e.g., 2025_01)")
    name = models.CharField(max_length=200, help_text="Display name (e.g., 'January 2025 Cohort')")
    reg_start_date = models.DateTimeField(help_text="Registration window start date")
    reg_end_date = models.DateTimeField(help_text="Registration window end date")
    exp_date_6 = models.DateTimeField(help_text="Expiry date for 6-month plan")
    exp_date_12 = models.DateTimeField(help_text="Expiry date for 12-month plan")
    is_active = models.BooleanField(default=True, help_text="Is this cohort accepting registrations?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reg_start_date']
        verbose_name = 'Cohort'
        verbose_name_plural = 'Cohorts'

    def __str__(self):
        return f"{self.cohort_id} - {self.name}"

    def is_registration_open(self):
        now = timezone.now()
        return self.is_active and self.reg_start_date <= now <= self.reg_end_date

    def get_expiry_for_plan(self, plan):
        return self.exp_date_6 if plan == '6month' else self.exp_date_12

    @classmethod
    def get_active_cohort(cls, submission_date=None):
        if submission_date is None:
            submission_date = timezone.now()
        return cls.objects.filter(
            is_active=True,
            reg_start_date__lte=submission_date,
            reg_end_date__gte=submission_date
        ).first()


class SubscriberRequest(models.Model):
    PLAN_CHOICES = [
        ('6month', '6-Month Plan'),
        ('annual', 'Annual Plan'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    mmdt_email = models.EmailField(blank=True, null=True)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    job_title = models.CharField(max_length=200, blank=True, null=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)
    free_waiver = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ], default='pending')
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='6month')
    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='subscriber_requests',
        help_text="Auto-assigned based on submission date"
    )

    def calculate_expiry_date(self):
        if self.cohort:
            return self.cohort.get_expiry_for_plan(self.plan)
        else:
            now = timezone.localtime(timezone.now())
            if self.plan == '6month':
                return now + timedelta(days=180)
            elif self.plan == 'annual':
                return now + timedelta(days=365)
        return None

    expiry_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.cohort and not self.pk:
            self.cohort = Cohort.get_active_cohort(self.created_at or timezone.now())
            if not self.cohort:
                raise ValidationError("No active cohort registration window is currently open.")

        if not self.expiry_date:
            self.expiry_date = self.calculate_expiry_date()

        if self.expiry_date and timezone.now() >= self.expiry_date:
            self.status = 'expired'

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscriber Request'
        verbose_name_plural = 'Subscriber Requests'

    def __str__(self):
        return f"{self.name} - {self.email}"
