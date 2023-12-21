from django.db import models
from .SettingReference import *
from apps.users.models import Learner, Mentor, Company
from apps.mentor.models import AssignMentorToUser
from apps.atpace_community.models import *
import uuid


class Attempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    DataPoint = models.ForeignKey(DataPoint, on_delete=models.CASCADE)
    WayOfLearn = models.ForeignKey(WayOfLearn, on_delete=models.CASCADE)
    Competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    NumberOfAttempt = models.IntegerField()

    def __str__(self):
        return str(self.id)


class IndividualAttemptWiseDPScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    DataPoint = models.ForeignKey(DataPoint, on_delete=models.CASCADE)
    Competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    AttemptWiseDataPointScore = models.IntegerField()
    AttemptType = models.CharField(max_length=200)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class DPWiseLearnerScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    DataPoint = models.ForeignKey(DataPoint, on_delete=models.CASCADE)
    WayOfLearnCourseCode = models.ForeignKey(WayOfLearnWiseCourseCode, on_delete=models.CASCADE)
    DPWiseLearnerScore = models.IntegerField()

    def __str__(self):
        return str(self.id)


class CourseCodeWiseLearnerScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    WayOfLearnCourseCode = models.ForeignKey(WayOfLearnWiseCourseCode, on_delete=models.CASCADE)
    CourseCodeWiseLearnerScore = models.IntegerField()

    def __str__(self):
        return str(self.id)


class WayOfLearnWiseLearnerScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    WayOfLearnWiseLearnerScore = models.IntegerField()

    def __str__(self):
        return str(self.id)


class CourseCodeWiseLearnerAssestmentScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    WayOfLearnCourseCode = models.ForeignKey(WayOfLearnWiseCourseCode, on_delete=models.CASCADE)
    CourseCodeWiseAssestmentScore = models.IntegerField()

    def __str__(self):
        return str(self.id)


class CompetencyWiseLearnerScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    Journey = models.ForeignKey(Channel, on_delete=models.CASCADE)
    EngagementScore = models.IntegerField()
    LearningScore = models.IntegerField()
    TotalScore = models.IntegerField()
    EngagementPercent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    LearningPercent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    TotalScorePercent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class AttemptWiseDPSubmissionData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Attempt = models.OneToOneField(IndividualAttemptWiseDPScore, on_delete=models.CASCADE)
    SubmittedFile = models.FileField(upload_to="files/")
    SubmittedTime = models.DateTimeField(auto_now_add=True)
    UpdatedTime = models.DateTimeField(auto_now_add=True)
    IsVerified = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class AttemptWiseDPLSKData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Post = models.OneToOneField(Post, on_delete=models.CASCADE)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

class NoActivityMenteeData(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Learner, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=255)
    no_calls = models.IntegerField(default=0)
    total_calls = models.IntegerField(default=0)
    no_quest = models.IntegerField(default=0)
    total_quest = models.IntegerField(default=0)
    no_journals = models.IntegerField(default=0)
    total_journals = models.IntegerField(default=0)
    all_post = models.IntegerField(default=0)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.user_name

    
class NoActivityMentorData(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=255)
    no_calls = models.IntegerField(default=0)
    total_calls = models.IntegerField(default=0)
    no_quest = models.IntegerField(default=0)
    total_quest = models.IntegerField(default=0)
    no_journals = models.IntegerField(default=0)
    total_journals = models.IntegerField(default=0)
    all_post = models.IntegerField(default=0)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.user_name
    
class NoActivityPairData(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    pair = models.ForeignKey(AssignMentorToUser, on_delete=models.CASCADE)
    mentor = models.ForeignKey(NoActivityMentorData, on_delete=models.CASCADE, null=True)
    learner = models.ForeignKey(NoActivityMenteeData, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Pair: {self.pair.mentor.get_full_name()} - {self.pair.user.get_full_name()}"

    class Meta:
        ordering = ('-created_at',)