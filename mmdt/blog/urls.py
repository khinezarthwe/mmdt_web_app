from django.urls import path

from . import views
from .views import Home, AboutUs, ContactUs

urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('blog/<slug:slug>/', views.PostDetail.post_detail, name='post_detail'),
    path('blog/', views.PostList.post_list, name='post_list'),
    path('about/', AboutUs.as_view(), name='about'),
    path('contact/', ContactUs.as_view(), name='contact')
]
