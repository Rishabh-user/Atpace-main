from django.urls import path
from .views import (AssessmentInstruction, CreateTest,
                    TestList,
                    AddQuestion,
                    update_question,
                    delete_question,
                    TestSeriesForm,
                    SubmitTest,
                    UserAssessmentAttempt,
                    EditTest,
                    AlloteChannel,
                    AssessmentChannel,
                    UpdateQOrder,
                    CopyQuestion,
                    QuestionId,
                    CheckAssessment,
                    CopyAssessment
                    )

app_name = 'test_series'
urlpatterns = [
    path('create/', CreateTest.as_view(), name="create-test"),
    path('list/', TestList.as_view(), name="test-list"),
    path('copy-assessment/', CopyAssessment.as_view(), name="copy_assessment"),
    path('edit/<uuid:pk>/', EditTest.as_view(), name="assessment-edit"),
    path('add-question/<uuid:survey>/', AddQuestion.as_view(), name="add_questions"),
    path('update-question/', update_question, name="update-question"),
    path('delete-question/<uuid:survey_id>/<int:pk>/', delete_question, name="delete-question"),
    path('assessment-instruction/<uuid:channel>/<uuid:pk>/', AssessmentInstruction.as_view(), name="assessment_instruction"),
    path('assessment/<uuid:channel>/<uuid:pk>/', TestSeriesForm.as_view(), name="test_series_form"),
    path('submit-test/', SubmitTest.as_view(), name="submit_test"),
    path('user-assessment/', UserAssessmentAttempt.as_view(), name="user_test_attempt"),
    path('allote-channel/', AlloteChannel.as_view(), name="addtest_to_channel"),
    path('channel/<uuid:pk>/', AssessmentChannel.as_view(), name="assessment_channel"),
    path('copy-question/', CopyQuestion.as_view(), name="copy_question"),
    path('update-question-order/', UpdateQOrder.as_view(), name='update-q-order'),
    path('question/', QuestionId.as_view(), name="single_question"),
    path('check/<uuid:assessment>/', CheckAssessment.as_view(), name="check_assessment"),
]
