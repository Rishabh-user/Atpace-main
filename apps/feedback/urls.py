from django.urls import path
from .views import CreateFeedbackTemplate, FeedbackTemplateList, EditFeedbackTemplate, delete_feedback_template, AddTemplateQuerstion, update_template_question, \
    CopyTemplateQuerstion, UpdateQuestionOrder, TemplateQuerstionId, delete_template_question, AddJourneyToFeedback, journey_content, FeedbackForm,FeedbackFormPost, FeedbackResponse, FeedbackResponseDetails
from .api import FeedbackList
app_name = "feedback"
urlpatterns = [
    path('create-feedback-template/', CreateFeedbackTemplate.as_view(), name="create_feedback_template"),
    path('feedback-template-list/', FeedbackTemplateList.as_view(), name="feedback_template_list"),
    path('edit-feedback-template/<uuid:template_id>/', EditFeedbackTemplate.as_view(), name="edit_feedback_template"),
    path('delete-feedback-template/', delete_feedback_template, name="delete_feedback_template"),
    path('add-template-question/<uuid:template_id>/', AddTemplateQuerstion.as_view(), name="add_template_question"),
    path('update-template-question/', update_template_question, name="update_template_question"),
    path('copy-template-question/', CopyTemplateQuerstion.as_view(), name="copy_template_question"),
    path('update-template-question-order/', UpdateQuestionOrder.as_view(), name="update_template_question_order"),
    path('template-question/', TemplateQuerstionId.as_view(), name="template_question"),
    path('delete-template-question/<uuid:template_id>/<uuid:pk>/', delete_template_question, name="delete_template_question"),
    path('feedback-form/<str:template_for>/<uuid:template_for_id>/', FeedbackForm.as_view(), name="feedback_form"),
    path('feedback-form/', FeedbackForm.as_view(), name="feedback_form"),
    path('feedback-form-post/<uuid:meet_id>', FeedbackFormPost.as_view(), name="feedback_form"),
    path('add-journey-to-feedback/', AddJourneyToFeedback.as_view(), name="add_journey_to_feedback"),
    path('journey-content/', journey_content, name="journey_content"),
    path('feedback-response/', FeedbackResponse.as_view(), name="feedback_response"),
    path('feedback-list/<uuid:user_id>/<str:type>/', FeedbackList.as_view(), name="feedback_list"),
    path('feedback-response-detail/<uuid:template_id>', FeedbackResponseDetails.as_view(), name="feedback_response_detail"),
]