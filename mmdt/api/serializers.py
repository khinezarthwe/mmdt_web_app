"""
Serializers for API request/response validation.
"""
from rest_framework import serializers

from blog.models import SubscriberRequest


class TokenRequestSerializer(serializers.Serializer):
    """Serializer for admin token request."""
    username = serializers.CharField(
        required=True,
        help_text="Admin username"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Admin password"
    )


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response."""
    access_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)
    token_type = serializers.CharField(read_only=True)


class UserDetailResponseSerializer(serializers.Serializer):
    """Serializer for user detail response."""
    email = serializers.EmailField(read_only=True)
    enddate = serializers.DateTimeField(read_only=True, allow_null=True)


class RenewalRequestSerializer(serializers.Serializer):
    """Serializer for renewal request."""
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        help_text="User's email address"
    )
    telegram_name = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="User's Telegram username"
    )
    plan = serializers.ChoiceField(
        choices=SubscriberRequest.PLAN_CHOICES,
        required=True,
        help_text="Subscription plan for renewal"
    )


class RenewalResponseSerializer(serializers.Serializer):
    """Serializer for renewal response."""
    status = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    upload_url = serializers.URLField(read_only=True, required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""
    status = serializers.CharField(read_only=True, default="error")
    message = serializers.CharField(read_only=True)
    detail = serializers.CharField(read_only=True, required=False)
