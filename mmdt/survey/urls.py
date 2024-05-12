from django.urls import path, include
from . import views
app_name = "survey"
urlpatterns = [
    path("", views.SurveyPage.index, name='index'),
    path("surveys/<int:survey_id>/", views.SurveyPage.survey_detail, name='survey_detail'),
    path("surveys/<int:survey_id>/questions/<int:question_id>", views.SurveyPage.save_survey_response, name='save_survey_response'),
    path("all_results/", views.SurveyPage.all_results, name='all_results'),
    path('_nested_admin/', include('nested_admin.urls'))
]
