from django.urls import path

from . import views
from .views import AboutUs, OurProject, StProject

urlpatterns = [
    path('', views.PostList.post_list, name='home'),
    path('blog/<slug:slug>/', views.PostDetail.post_detail, name='post_detail'),
    path('blog/', views.PostList.post_list, name='post_list'),
    path('st_project/', StProject.as_view(), name='st_projects'),
    path('our_project/', OurProject.as_view(), name='our_projects'),
    path('about/', AboutUs.as_view(), name='about'),
]
