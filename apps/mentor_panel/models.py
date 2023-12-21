from django.db import models
from apps.utils.models import ModelActiveDelete, Timestamps
import uuid
from apps.users.models import Company, Mentor, User
from ravinsight.constants import certification_level, contact_preferences, location_types, employment_types
# Create your models here.

class MentoringTypes(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mentoring_type_created_by")

    class Meta:
        ordering = ('-created_at',)
        
    def __str__(self):
        return self.name


class TargetAudience(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="target_audience_created_by")

    class Meta:
        ordering = ('-created_at',)
        
    def __str__(self):
        return self.name

class MentorMarketPlace(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Mentor, on_delete=models.CASCADE, null=True, blank=True)
    mentoring_style = models.TextField()
    mentoring_types = models.ManyToManyField(MentoringTypes)
    target_audience = models.ManyToManyField(TargetAudience)
    languages = models.TextField()
    total_experience = models.FloatField(default=0)
    contact_preferences = models.CharField(max_length=100, choices=contact_preferences, default='Email')
    partner_badge = models.ForeignKey(Company, on_delete=models.CASCADE)
    keep_contact_details_private = models.BooleanField(default=False)
    location = models.TextField()
    expertise = models.TextField()

    
    class Meta:
        ordering = ('-created_at',)
        
    def __str__(self):
        return f"{self.user.get_full_name()}"

class WorkExperience(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    market_place = models.ForeignKey(MentorMarketPlace, on_delete=models.CASCADE, related_name="user_experience", null=True, blank=True)
    company = models.CharField(max_length=128)
    designation = models.CharField(max_length=128)
    start_date = models.DateField()
    currently_working = models.BooleanField(default=False)
    end_date = models.DateField(null=True, blank=True) 
    location = models.CharField(max_length=20, null=True, blank=True)
    location_type = models.CharField(max_length=20, choices=location_types, default='Beginner')
    employment_type = models.CharField(max_length=20, choices=employment_types, default='Beginner')
    description = models.TextField()

    class Meta:
        ordering = ('-created_at',)
        
    def __str__(self):
        return f"{self.user.get_full_name()}"


class MentorMarketPlaceCertificates(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market_place = models.ForeignKey(MentorMarketPlace, on_delete=models.CASCADE, related_name="user_certificate", null=True, blank=True)
    user = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    certificate = models.FileField(upload_to='mentor/merketplace/certificates')
    certification_level = models.CharField(max_length=20, choices=certification_level, default='Beginner')
    generated_date = models.DateField()
    is_expiration_date = models.BooleanField(default=False)
    valid_upto = models.DateField(null=True, blank=True)
    description = models.TextField()
    class Meta:
        ordering = ('-created_at',)
        
    def __str__(self):
        return f"{self.user.get_full_name()}"
    
class MentorMarketPlaceEducation(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market_place = models.ForeignKey(MentorMarketPlace, on_delete=models.CASCADE, related_name="user_education", null=True, blank=True)
    user = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    program = models.CharField(max_length=128)
    major = models.CharField(max_length=30)
    university = models.CharField(max_length=128)
    location = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField()
    is_ongoing = models.BooleanField(default=False)
    excellence = models.CharField(max_length=30)
    description = models.CharField(max_length=128)
    