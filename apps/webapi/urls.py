from django.urls import path, include
from apps.webapi.views import (AssessmentAttemptViewSet, AssessmentCSV, ExportJourney, SurveyCSV, UserViewSet, SurveyAttemptViewSet,
                               UserJourneyViewSet, AllJourney, AllAssessment, AllSurvey,
                               JourneyPathway, APITest, TestAssessmentMarks, activeUserCSV, matchAllAssessment, matchAllSurveys, userinfo, OrderContent,
                               UserToLearner, update_journey, update_last_modified, all_user_download_data, update_question_type, change_course_type
                               )
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

app_name = 'api'
urlpatterns = [
    path('', include(router.urls), name="users"),
    path('assessment/', AssessmentAttemptViewSet.as_view()),
    path('survey/', SurveyAttemptViewSet.as_view()),
    path('user-journey/', UserJourneyViewSet.as_view()),
    path('all-assessment/', AllAssessment.as_view()),
    path('all-survey/', AllSurvey.as_view()),
    path('all-journey/', AllJourney.as_view()),
    path('journey-pathway/<slug:username>', JourneyPathway.as_view()),
    path('api-test', APITest.as_view()),
    path('marks-test/', TestAssessmentMarks.as_view()),
    # path('rtoken/', TokenRefresh.as_view(), ),
    path('user-info/', userinfo.as_view()),
    path('export_csv/<str:journey_type>', ExportJourney, name="journey_data"),
    path('export-assessment-csv/<uuid:attempt_id>/', AssessmentCSV, name="assessment_csv"),
    path('export-all-assessment-csv/', matchAllAssessment, name="all_assessment_csv"),
    path('export-all-survey-csv/', matchAllSurveys, name="all_survey_csv"),
    path('export-survey-csv/<uuid:attempt_id>/', SurveyCSV, name="survey_csv"),
    path('export-active-user-csv/<str:active_status>/', activeUserCSV, name="active_user_csv"),
    path('order-content/', OrderContent.as_view(), name="order_content"),
    path('appusertolearner/', UserToLearner.as_view(), name="app_user_to_learner"),
    # path('order-group-content/', OrderGroupContent.as_view(), name="order_group_content"),
    # path('check-group/', Checkgroup.as_view())
    path('update-coupan',update_journey,name="update_journey"),
    # path('deactivate-user/', deactivate_user, name="deactivate_user"),

    # path('download-data', download_data,  name="download_data"),
    path('all-user-data/<str:user_type>/<uuid:journey_id>/<uuid:company_id>/<uuid:user_id>/', all_user_download_data.as_view(),  name="all_user_download_data"),
    path('update-last-modified/', update_last_modified, name="update_last_modified"),
    path('update_question_type/', update_question_type, name="update_question_type"),
    path('change_course_type/', change_course_type, name="change_course_type")

]
