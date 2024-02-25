# Add URL patterns in your urls.py
from django.urls import path
from . import views
app_name = "survey"
urlpatterns = [
    path("", views.SurveyPage.index, name='index'),
]