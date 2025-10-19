"""
URL configuration for mmdt project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ADD THIS LINE FOR THE API ---
    # This includes all the routes from your new 'api' app (e.g., /api/auth/token/, /api/users/me/, etc.)
    path('api/', include('api.urls')),
    # --- END OF ADDITION ---

    path('accounts/', include('allauth.urls')),
    path('', include('blog.urls')),
    path('polls/', include('polls.urls', namespace='polls')),
    path('survey/', include('survey.urls', namespace='survey')),
    path('surveys/', include('djf_surveys.urls')),
    path('summernote/', include('django_summernote.urls'))
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

    