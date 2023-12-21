from django.db import models
from django.conf import settings
import uuid
from apps.atpace_community.models import Comment, Post
from apps.content.models import Channel, ProgramTeamAnnouncement
from apps.mentor.models import mentorCalendar
from apps.users.models import Collabarate
from apps.utils.models import Timestamps
# Create your models here.
class VonageApiHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_for = models.CharField(max_length=255, default="Community")
    message_type = models.CharField(max_length=50)
    message_channel = models.CharField(max_length=20, default="whatsapp")
    message_id = models.CharField(max_length=255)
    post_id = models.CharField(max_length=255)
    message_from = models.CharField(max_length=20) 
    message_to = models.CharField(max_length=20)
    message_status = models.CharField(max_length=20)
    message = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
class VonageWhatsappReport(Timestamps):
    channel_type = (
        ("WhatsApp", "WhatsApp"),
        ("Text", "Text"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_id = models.CharField(max_length=255)
    announcement = models.ForeignKey(ProgramTeamAnnouncement, on_delete=models.CASCADE, blank=True, null=True)
    from_user = models.CharField(max_length=128, blank=True)
    chat_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sender", null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mentor_cal = models.ForeignKey(mentorCalendar, on_delete=models.CASCADE, blank=True, null=True)
    collaborate = models.ForeignKey(Collabarate, on_delete=models.CASCADE, blank=True, null=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, blank=True, null=True)
    message_status = models.CharField(max_length=50, blank=True)
    send_message = models.CharField(max_length=256)
    chat_info = models.TextField()
    password = models.CharField(max_length=128)
    otp = models.CharField(max_length=128)
    reset_link = models.TextField()
    status = models.CharField(max_length=128)
    channel = models.CharField(max_length=50, choices=channel_type, default="WhatsApp")
    message_type = models.CharField(max_length=128)
    is_sent = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.message_type}"

    class Meta:
        ordering = ('-created_at',)