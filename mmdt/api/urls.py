# /mmdt_web_app/api/urls.py

from django.urls import path
from .views import CustomAuthToken, CurrentUserView, UserDetailView

urlpatterns = [
    path('auth/token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('users/me/', CurrentUserView.as_view(), name='current_user_profile'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]
