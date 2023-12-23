from django.urls import path

from . import views

app_name = "polls"
urlpatterns = [
    path("", views.PollHomePage.index, name="index"),
    path('vote/', views.PollHomePage.vote, name='vote'),
]
