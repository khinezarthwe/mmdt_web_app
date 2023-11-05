from django.urls import path
from .views import AboutUs, OurProject, StProject, PlayGround, PostDetailView, PostListView

urlpatterns = [
    path('', PostListView.as_view(), name='home'),
    path('blog/', PostListView.as_view(), name='post_list'),
    path('blog/<slug:slug>/', PostDetailView.as_view(), name='post_detail'),
    path('st_project/', StProject.as_view(), name='st_projects'),
    path('our_project/', OurProject.as_view(), name='our_projects'),
    path('about/', AboutUs.as_view(), name='about'),
    path('our_playground/', PlayGround.as_view(), name='our_playground'),
]
