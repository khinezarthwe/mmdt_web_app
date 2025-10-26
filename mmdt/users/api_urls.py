from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import UserViewSet
from .api_auth import CustomAuthToken

# Create a router and register our viewset
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('auth/token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('', include(router.urls)),
]
