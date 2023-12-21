from django.contrib import admin
from .models import FeedbackTemplate, FeedbackTemplateQuerstion, JourneyFeedback, UserFeedback, feedbackAnswer
# Register your models here.
admin.site.register(FeedbackTemplate)
admin.site.register(FeedbackTemplateQuerstion)
admin.site.register(JourneyFeedback)
admin.site.register(UserFeedback)
admin.site.register(feedbackAnswer)