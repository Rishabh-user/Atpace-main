from django.db import models
from django.conf import settings
import uuid
from apps.community.models import WeeklyLearningJournals
from apps.content.models import Channel, ChannelGroup, ChannelGroupContent
from apps.mentor.models import mentorCalendar
from apps.survey_questions.models import Survey
from apps.test_series.models import TestSeries
from apps.users.models import Collabarate
from apps.utils.models import ModelActiveDelete, Timestamps
import jsonfield
from apps.users.models import Company

from ravinsight.constants import Question_Type, template_choice

# Create your models here.


class FeedbackTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    template_for = models.CharField(max_length=100, choices=template_choice)
    cover_image = models.ImageField(upload_to="feedback/", null=True)
    short_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_draft = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="feedback_template_updated_by")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-created_at',)

class FeedbackTemplateQuerstion(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    feedback_template = models.ForeignKey(FeedbackTemplate, on_delete=models.CASCADE, related_name="feedback_template")
    title = models.TextField()
    type = models.CharField(max_length=100, choices=Question_Type)
    is_required = models.BooleanField(default=False)
    option_list = jsonfield.JSONField(blank=True, null=True)
    correct_answer = models.TextField(blank=True, null=True)
    start_rating_scale = models.IntegerField(default=0)
    end_rating_scale = models.IntegerField(default=5)
    start_rating_name = models.CharField(max_length=100)
    end_rating_name = models.CharField(max_length=100, blank=True, null=True)
    is_multichoice = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True) 
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)
    is_draft = models.BooleanField(default=False)
    display_order = models.IntegerField(default=1)
    image = models.ImageField(upload_to='feedbackQuestion/images/', blank=True, null=True)

class JourneyFeedback(ModelActiveDelete):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    feedback_template = models.ForeignKey(FeedbackTemplate, on_delete=models.CASCADE, related_name="journey_feedback_template")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=128, null=True)
    data_id = models.CharField(max_length=128, null=True)
    data_title = models.CharField(max_length=128, null=True)
    is_active = models.BooleanField(default=True) 
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="journey_feedback_updated_by")

class UserFeedback(ModelActiveDelete, Timestamps):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    feedback_template = models.ForeignKey(FeedbackTemplate, on_delete=models.CASCADE, related_name="user_feedback_template", null=True, blank=True)
    user = models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)
    journey_feedback = models.ForeignKey(JourneyFeedback, on_delete=models.CASCADE, related_name="journey_feedback", null=True, blank=True)
    is_private = models.BooleanField(default=False)
    is_name_private = models.BooleanField(default=False)
    feedback_for_user = models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, related_name="feedback_for_user", null=True, blank=True)
    template_for_id = models.CharField(max_length=128, null=True)
    template_for = models.CharField(max_length=128, null=True)

class feedbackAnswer(Timestamps):
    choice = (
        ("Assessment", "Assessment"),
        ("CourseCompletion", "CourseCompletion"),
        ("GroupCall", "GroupCall"),
        ("LiveCall", "LiveCall"),
        ("OneToOne", "OneToOne"),
        ("SkillCompletion", "SkillCompletion"),
        ("MicroSkill", "MicroSkill"),
        ("Survey", "Survey"),
        ("MentoringJournals", "MentoringJournals"),
        ("Mentor", "Mentor Profile"),
        ("Mentee", "Mentee Profile"),
    )
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    journey_template = models.ForeignKey(FeedbackTemplate, on_delete=models.CASCADE, related_name="answer_feedback_template")
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    question = models.ForeignKey(FeedbackTemplateQuerstion, on_delete=models.CASCADE, null=True, blank=True)
    answer = models.CharField(max_length=128, null=True)
    user_feedback = models.ForeignKey(UserFeedback, on_delete=models.CASCADE, related_name="user_feedback_template", null=True, blank=True)
    feedback_for = models.CharField(max_length=100, choices=choice)
    feedback_for_id = models.CharField(max_length=128, null=True)