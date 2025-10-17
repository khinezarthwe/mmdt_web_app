from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""

    class Meta:
        model = UserProfile
        fields = ['expired', 'expiry_date', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with profile information."""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_active']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for User model including profile information."""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'is_staff', 'is_superuser', 'date_joined',
                  'last_login', 'profile']
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_active',
                            'is_staff', 'is_superuser']
