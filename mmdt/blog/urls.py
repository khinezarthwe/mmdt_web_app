from django.urls import path

from .views import AboutUs, OurProject, StProject, PlayGround, OurInstructors, PostDetailView, PostListView, PostListOnlySubscriberView, \
    subscriber_request, subscriber_request_success

urlpatterns = [
    path('', PostListView.as_view(), name='home'),
    path('blog/', PostListOnlySubscriberView.as_view(), name='post_list_only_subscriber'),
    path('blog/<slug:slug>/', PostDetailView.as_view(), name='post_detail'),
    path('st_project/', StProject.as_view(), name='st_projects'),
    path('our_instructors/', OurInstructors.as_view(), name='our_instructors'),
    path('our_project/', OurProject.as_view(), name='our_projects'),
    path('about/', AboutUs.as_view(), name='about'),
    # path('subscriber/', SubscriberInfo.as_view(), name='subscriber'),
    path('our_playground/', PlayGround.as_view(), name='our_playground'),
    path('subscriber-request/', subscriber_request, name='subscriber_request'),
    path('subscriber-request/success/', subscriber_request_success, name='subscriber_request_success')

]
