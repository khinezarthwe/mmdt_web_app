from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from . import views

app_name = "polls"
urlpatterns = [
    path("", views.PollHomePage.index, name="index"),
    path('vote/', views.PollHomePage.vote, name='vote'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='polls/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
