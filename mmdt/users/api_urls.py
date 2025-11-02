"""
User API URL configuration.

Includes JWT authentication endpoints and user management endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import UserViewSet, UserSessionViewSet
from .api_auth import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    LogoutAllView,
)

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'sessions', UserSessionViewSet, basename='session')

# URL patterns
urlpatterns = [
    # JWT Authentication endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout/all/', LogoutAllView.as_view(), name='logout_all'),

    # ViewSet routes
    path('', include(router.urls)),
]
