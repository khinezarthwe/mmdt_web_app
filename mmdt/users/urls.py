from django.urls import path
from . import views
from django.conf.urls import include

app_name = "users"

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('accounts/', include("django.contrib.auth.urls")),
]
