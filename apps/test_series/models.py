from django.db import models
from ravinsight.constants import Question_Type, skill_level
from apps.utils.models import Timestamps
from django.conf import settings

import jsonfield
import uuid 
# Create your models here.


class TestSeries(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    cover_image = models.ImageField(upload_to="assessment/", null= True)
    short_description = models.TextField(blank=True)
    auto_check = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    feedback_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-created_at',)


class TestQuestion(Timestamps):
    survey = models.ForeignKey(TestSeries, on_delete=models.CASCADE, related_name="test_series")
    title = models.TextField()
    type = models.CharField(max_length=100, choices=Question_Type)
    skill_level = models.CharField(max_length=200, choices=skill_level)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    option_list = jsonfield.JSONField(blank=True, null=True)
    correct_answer = models.TextField(blank=True, null=True)
    grid_row = jsonfield.JSONField(blank=True, null=True)
    grid_coloum = jsonfield.JSONField(blank=True, null=True)
    display_order = models.IntegerField(default=1)
    marks = models.IntegerField()
    image = models.ImageField(upload_to='testQuestion/images/', blank=True, null=True)

    def __str__(self):
        return self.title


class TestOptions(Timestamps):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="options")
    option = models.CharField(max_length=255)
    marks = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    correct_option = models.BooleanField(default=False)






