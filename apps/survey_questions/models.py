from django.db import models
from django.conf import settings
from apps.test_series.models import Question_Type
from apps.utils.models import Timestamps
import jsonfield
import uuid


# Create your models here.
class Survey(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    cover_image = models.ImageField(upload_to="survey/", null= True)
    short_description = models.TextField(blank=True)
    feedback_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="survey_created_by")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-created_at',)


class Question(Timestamps):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="survey")
    title = models.TextField()
    type = models.CharField(max_length=100, choices=Question_Type)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    option_list = jsonfield.JSONField(blank=True, null=True)
    correct_answer = models.TextField(blank=True, null=True)
    grid_row = jsonfield.JSONField(blank=True, null=True)
    grid_coloum = jsonfield.JSONField(blank=True, null=True)
    start_rating_scale = models.IntegerField(default=0)
    end_rating_scale = models.IntegerField(default=5)
    start_rating_name = models.CharField(max_length=100)
    end_rating_name = models.CharField(max_length=100, blank=True, null=True)
    display_order = models.IntegerField(default=1)
    image = models.ImageField(upload_to='surveyQuestion/images/', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('-created_at',)


class Options(Timestamps):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    option = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)


class Answer(Timestamps):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_question")
    answer = models.TextField()


class SurveyLabel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.label


class SurveyAttempt(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_check = models.BooleanField(default=False)
    checked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="survey_checked_by", blank=True, null=True)
    checked_on = models.DateTimeField(blank=True, null=True)
    user_skill = models.ForeignKey(SurveyLabel, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)


class UserAnswer(Timestamps):
    survey_attempt = models.ForeignKey(SurveyAttempt, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_question")
    response = models.TextField()
    upload_file = models.FileField(upload_to='survey/', null=True, blank=True, verbose_name="")
    total_marks = models.IntegerField(default=0)

    class Meta:
        ordering = ('-created_at',)
