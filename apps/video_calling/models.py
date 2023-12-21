from django.db import models
import uuid
from apps.users.models import User
# Create your models here.

class RoomProperties(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime = models.DateTimeField(auto_now=False, auto_now_add=False)
    enable_new_call_ui = models.BooleanField(default='True')
    enable_prejoin_ui = models.BooleanField(null=True)
    enable_knocking = models.BooleanField(default='False')
    enable_screenshare = models.BooleanField(default='True')
    enable_video_processing_ui = models.BooleanField(default='True')
    enable_chat = models.BooleanField(default='False')
    start_video_off = models.BooleanField(default='False')
    start_audio_off = models.BooleanField(default='False')
    owner_only_broadcast = models.BooleanField(default='False')
    is_owner = models.BooleanField(default='False')
    
    def __str__(self):
        return str(self.id)
    
class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    Participants = models.ManyToManyField(User, related_name="participants_users", default=None)
    api_created = models.BooleanField(default=True)
    privacy = models.CharField(max_length=50, default="public")
    token = models.CharField(max_length=200, blank=True)
    url = models.URLField(blank=False)
    created_at = models.CharField(max_length=100)
    properties = models.ForeignKey(RoomProperties, on_delete=models.CASCADE, null=False)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return str(self.name)