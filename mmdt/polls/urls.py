from django.urls import path
from . import views

app_name = "polls"
urlpatterns = [
    path("", views.PollHomePage.index, name="index"),
    path('vote/', views.PollHomePage.vote, name='vote'),
    path('all_results/', views.PollHomePage.all_results, name='all_results'),
    path('release_results/<int:group_id>/', views.release_results, name='release_results'),
]
