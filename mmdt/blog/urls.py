from . import views
from django.urls import path
from .views import Home

urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('blog/<slug:slug>/', views.PostDetail.post_detail, name='post_detail'),
    path('blog/', views.PostList.post_list, name='post_list')
]
