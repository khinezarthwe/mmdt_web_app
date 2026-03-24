"""
URL configuration for the API app.
"""
from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.schemas import get_schema_view

from .schema import CustomSchemaGenerator
from .views import (
    AdminTokenView,
    SwaggerUIView,
    UserDetailByEmailView,
    UserDetailByTelegramView,
    UserRenewalRequestView,
)

app_name = 'api'

urlpatterns = [
    path('auth/token', AdminTokenView.as_view(), name='auth-token'),
    path('users', UserDetailByEmailView.as_view(), name='user-by-email'),
    path('users/telegram', UserDetailByTelegramView.as_view(), name='user-by-telegram'),
    path('user/request_renew', UserRenewalRequestView.as_view(), name='user-renewal'),
    path('docs/', SwaggerUIView.as_view(), name='swagger-ui'),
    path(
        'schema/',
        get_schema_view(
            title='MMDT API',
            description='OpenAPI schema for token and user endpoints.',
            version='1.0.0',
            public=True,
            permission_classes=[AllowAny],
            generator_class=CustomSchemaGenerator,
        ),
        name='openapi-schema',
    ),
]
