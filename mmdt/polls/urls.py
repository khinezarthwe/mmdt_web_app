from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from . import views

app_name = "polls"
urlpatterns = [
    path("", views.PollHomePage.index, name="index"),
    path('vote/', views.PollHomePage.vote, name='vote'),
    path('login/', LoginView.as_view(template_name='polls/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('all_results/', views.PollHomePage.all_results, name='all_results'),
    path('release_results/<int:group_id>/', views.release_results, name='release_results'),
]
