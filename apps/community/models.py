from django.conf import settings
from django.db import models
import jsonfield
from apps.content.models import Channel
from ravinsight.constants import RecordFor, RecordTypeStatus
from apps.utils.models import Timestamps
from ravinsight.constants import types
import uuid
# Create your models here.


class JourneySpace(models.Model):
    journey = models.OneToOneField(Channel, on_delete=models.CASCADE,
                                   related_name="journryspace")
    space_id = models.IntegerField(null=True, blank=True)
    community_id = models.IntegerField(null=True, blank=True)
    space_group_name = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=100)
    is_private = models.BooleanField(default=False)
    is_hidden_from_non_members = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    slug = models.CharField(max_length=255)
    space_group_id = models.IntegerField(null=True, blank=True)
    circle_url = models.URLField(max_length=255, default="")


class AddMemberToSpace(models.Model):
    space_id = models.IntegerField(null=True, blank=True)
    community_id = models.IntegerField(null=True, blank=True)
    email = models.EmailField(max_length=254)
    is_joined = models.BooleanField(default=True)


class UserCircleDetails(models.Model):
    circle_id = models.IntegerField(null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(max_length=254)


class CommunityPost(Timestamps):
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE,
                                related_name="journry_community_post", null=True)  # channel foreigen Key
    microskill_id = models.CharField(max_length=255, null=True)  # couser content Id
    post_id = models.IntegerField(null=True, blank=True)
    community_id = models.IntegerField(null=True, blank=True)
    space_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255)
    body = models.TextField()
    record_type = models.CharField(max_length=100, choices=RecordTypeStatus, default="LearningJournal")
    record_for = models.CharField(max_length=100, choices=RecordFor, default="Atpace")
    is_pinned = models.BooleanField(default=False)
    is_comments_enabled = models.BooleanField(default=True)
    is_liking_enabled = models.BooleanField(default=True)
    user_email = models.EmailField(max_length=254)
    skip_notifications = models.BooleanField(default=True)
    slug = models.CharField(max_length=255)
    internal_custom_html = models.TextField()
    is_truncation_disabled = models.BooleanField(default=True)
    hide_meta_info = models.BooleanField(default=True)
    circle_url = models.URLField(max_length=255, default="")
    user_name = models.CharField(max_length=255)


class CommunityPostComment(Timestamps):
    community_post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, null=True)
    comment_id = models.IntegerField(null=True, blank=True)
    post_id = models.IntegerField(null=True, blank=True)
    post_name = models.CharField(max_length=255)
    community_id = models.IntegerField(null=True, blank=True)
    space_id = models.IntegerField(null=True, blank=True)

    body = models.TextField()
    parent_comment_id = models.IntegerField(null=True, blank=True)
    user_email = models.EmailField(max_length=254)
    user_name = models.CharField(max_length=255)


class CicleDataDump(models.Model):
    type = models.CharField(max_length=100)
    data = jsonfield.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LearningJournals(Timestamps):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    user_type = models.CharField(max_length=255, null=True, blank=True)
    is_draft = models.BooleanField(default=False)
    microskill_id = models.CharField(max_length=255, null=True)  # couser content Id
    skill_data_id = models.CharField(max_length=255, null=True)
    learning_journal = models.TextField(blank=True, null=True)
    is_weekly_journal = models.BooleanField(default=False)
    weekely_journal_id = models.CharField(max_length=20, blank=True, null=True)
    journey_id = models.CharField(max_length=255, null=True)
    user_name = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return "User: %s name: %s" % (self.user_name, self.name)


class LearningJournalsComments(Timestamps):
    learning_journal = models.ForeignKey(LearningJournals, on_delete=models.CASCADE)
    user_email = models.EmailField(max_length=254)
    user_name = models.CharField(max_length=255)
    user_id = models.CharField(max_length=100)
    body = models.TextField()
    parent_comment_id = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)


class LearningJournalsAttachment(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(LearningJournals, on_delete=models.CASCADE, null=True, blank=True)
    image_upload = models.ImageField(upload_to='learning_journals/images/')
    file_upload = models.FileField(upload_to='learning_journals/files/')
    upload_for = models.CharField(max_length=50, choices=types, default="Post")


class WeeklyLearningJournals(Timestamps):
    name = models.CharField(max_length=255)
    journey_id = models.CharField(max_length=255, null=True)
    learning_journal = models.TextField(blank=True, null=True)
    created_by = models.CharField(max_length=100)


class WeeklyjournalsTemplate(Timestamps):
    title = models.CharField(max_length=100)
    learning_journal = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    feedback_required = models.BooleanField(default=False)
    created_by = models.CharField(max_length=100)


class CommunitySignupList(Timestamps):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    password = models.CharField(max_length=200, null=True, blank=True)
