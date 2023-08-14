from . import views
from django.urls import path

urlpatterns = [
    path('', views.PostList.post_list, name='home'),
    path('blog/<slug:slug>/', views.PostDetail.post_detail, name='post_detail')
]
