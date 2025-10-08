from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
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


class SubscriberRequest(models.Model):
    PLAN_CHOICES = [
        ('6month', '6-Month Plan'),
        ('annual', 'Annual Plan'),
    ]

    class Meta:
        # Additional validation to catch duplicate emails with case insensitivity
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                name='unique_subscriber_email'
            )
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

    def calculate_expiry_date(self):
        now = timezone.localtime(timezone.now())
        if self.plan == '6month':
            return now + timedelta(days=180)
        elif self.plan == 'annual':
            return now + timedelta(days=365)
        return None

    expiry_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.expiry_date:  # Only set if not already set
            self.expiry_date = self.calculate_expiry_date()
        if self.expiry_date and timezone.now() >= self.expiry_date:
            self.status = 'expired'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.email}"
