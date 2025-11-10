"""
API v1 URL configuration.

This module contains all v1 API endpoints.
"""
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

app_name = 'api_v1'

urlpatterns = [
    # OpenAPI Schema
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='api_v1:schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='api_v1:schema'), name='redoc'),

    # Authentication endpoints
    path('auth/', include('users.api_urls')),
]
