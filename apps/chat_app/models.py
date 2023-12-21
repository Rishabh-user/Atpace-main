from datetime import datetime
from distutils.command.upload import upload
from django.db import models
import uuid
from apps.users.models import User


# Create your models here.
type = (
    ('OneToOne', 'OneToOne'),
    ('OneToMany', 'OneToMany')
)


class Room(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=type, default="OneToOne")
    group_name = models.CharField(max_length=255, null=True, blank=True)
    members = models.ManyToManyField(User, related_name="members", blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    max_members = models.IntegerField(default=100)
    group_image = models.ImageField(upload_to='group_image/', default="static/dist/img/group.png", null=True)
    group_admin = models.ManyToManyField(User, related_name="group_admin", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                                   blank=True, related_name="group_created_by")
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                                   blank=True, related_name="group_deleted_by")
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="room_from_user", null=True, blank=True)
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="room_to_user", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, null=True)
    create_at = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ('-updated_at',)

    def __str__(self) -> str:
        return f"{self.name} - {self.type}"


class Chat(models.Model):
    CHOICES = (
        ("TEXT", "TEXT"),
        ("IMAGE", "IMAGE"),
        ("PDF", "PDF"),
        ("VIDEO", "VIDEO")
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=255, choices=type, default="OneToOne")
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="from_user")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="to_user", null=True, blank=True)
    message = models.TextField(max_length=1000)
    msg_type = models.CharField(max_length=10, choices=CHOICES, default="TEXT")
    file = models.FileField(upload_to='chat/files', null=True, blank=True)
    file_name = models.CharField(max_length=128, null=True, blank=True)
    image = models.ImageField(upload_to='chat/images', null=True, blank=True)
    timestamp = models.DateTimeField(default=datetime.now)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    # group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.to_user} - {self.timestamp}"


# icon = models.ImageField()
# description = models.TextField(max_length=255)
# user_id = models.IntegerField()
# from_user = models.CharField(max_length=255)
# message = models.CharField(max_length=1000)
# msg_type = models.CharField(max_length=255)
# file = models.FileField(upload_to ='')
# timestamp  = models.DateTimeField(auto_now=True)
