from django.db import models
import uuid

from apps.content.models import Channel
from apps.users.models import User


# Create your models here.

class Competency(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Journey = models.ForeignKey(Channel, on_delete=models.CASCADE)
    CompetencyName = models.CharField(max_length=200)
    Purpose = models.TextField(blank=True, null=True)
    IndustryBenchmarkPercent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    IsActive = models.BooleanField(default='False')
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="CompetencyCreatedBy")
    UpdatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="CompetencyUpdatedBy")

    def __str__(self):
        return str(self.CompetencyName)


class WayOfLearn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Competency = models.ManyToManyField(Competency, through='CompetencyWayOfLearn')
    WayOfLearnName = models.CharField(max_length=200)
    WayOfLearnScore = models.IntegerField(default=0)
    IndustryBenchmarkPercent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    IsActive = models.BooleanField(default='False')
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="WOfLearnCreatedBy")
    UpdatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="WOfLearnUpdatedBy")

    def __str__(self):
        return str(self.WayOfLearnName)


class BaseScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Label = models.CharField(max_length=20)
    BaseValue = models.IntegerField()
    IsActive = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class Weightage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Label = models.CharField(max_length=20)
    WeightageValue = models.IntegerField()
    IsActive = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class DataPoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    WayOfLearn = models.ForeignKey(WayOfLearn, on_delete=models.CASCADE)
    DataPointName = models.CharField(max_length=74)
    Weightage = models.ForeignKey(Weightage, on_delete=models.CASCADE)
    BaseScore = models.ForeignKey(BaseScore, on_delete=models.CASCADE)
    MaxNumberOfInstances = models.IntegerField()
    DataPointScore = models.IntegerField()
    IsActive = models.BooleanField(default='False')
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="DPCreatedBy")
    UpdatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="DPUpdatedBy")

    def __str__(self):
        return str(self.id)


class CompetencyWayOfLearn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    WayOfLearn = models.ForeignKey(WayOfLearn, on_delete=models.CASCADE)
    NumberOfWayOfLearn = models.IntegerField()
    DataPointScore = models.IntegerField()
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="CWOLCreatedBy")
    UpdatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="CWOLUpdatedBy")

    def __str__(self):
        return str(self.id)


class WayOfLearnWiseCourseCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    WayOfLearn = models.ForeignKey(WayOfLearn, on_delete=models.CASCADE)
    CourseCode = models.CharField(max_length=200)

    def __str__(self):
        return str(self.id)


class CourseCodePattern(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CourseCode = models.ForeignKey(WayOfLearnWiseCourseCode, on_delete=models.CASCADE)
    TopicsToBeCover = models.CharField(max_length=200)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="PatternCreatedBy")
    UpdatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="PatternUpdatedBy")

    def __str__(self):
        return str(self.id)


class CompetencyParamsReferenceScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Competency = models.OneToOneField(Competency, on_delete=models.CASCADE)
    EngagementReferenceScore = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    LearningReferenceScore = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    TotalReferenceScore = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.id)
