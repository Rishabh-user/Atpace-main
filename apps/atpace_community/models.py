import random
import string
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from apps.content.models import Channel
from apps.utils.models import Timestamps
from apps.users.models import Collabarate
from ravinsight.constants import Privacy_types, types, report_types
import uuid
from random import randint
# Create your models here.


class SpaceGroups(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    cover_image = models.ImageField(upload_to='atpace_community/cover_images/')
    slug = models.SlugField(max_length=255, unique=True)
    privacy = models.CharField(max_length=20, choices=Privacy_types, default="Private", db_index=True)
    is_hidden = models.BooleanField(default=True)
    hidden_from_non_members = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    update_by = models.CharField(max_length=255, null=True)
    deleted_by = models.CharField(max_length=255, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=['is_active', 'is_delete'])]
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if SpaceGroups.objects.filter(title__icontains=self.title).exists():
            rand_number = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
            self.slug = f"{slugify(self.title)}-{rand_number}"
        else:
            self.slug = slugify(self.title)
        super(SpaceGroups, self).save(*args, **kwargs)


class Spaces(Timestamps):
    space_type = (
        ("Post", "Post"),
        ("Event", "Event"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space_group = models.ForeignKey(SpaceGroups, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, db_index=True)
    description = models.TextField(max_length=500)
    cover_image = models.ImageField(upload_to='atpace_community/cover_images/')
    add_member_from_group = models.BooleanField(default=False)
    icon = models.ImageField(upload_to="upload_to='atpace_community/icons/", null=True)
    slug = models.SlugField(max_length=255, unique=True)
    space_type = models.CharField(max_length=50, choices=space_type, default="Post")
    privacy = models.CharField(max_length=20, choices=Privacy_types, default="Private", db_index=True)
    telegram_id = models.CharField(max_length=100, null=True)
    telegram_channel = models.CharField(max_length=256, null=True)
    is_hidden = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    hidden_from_non_members = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    is_telegram = models.BooleanField(default=False)
    update_by = models.CharField(max_length=255, null=True)
    deleted_by = models.CharField(max_length=255, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'is_delete']),
            models.Index(fields=['is_active', 'is_delete', 'is_hidden', 'space_group', 'hidden_from_non_members'])
        ]
        ordering = ('-created_at',)

    def __str__(self):
        return str(self.title)

    def save(self, *args, **kwargs):
        if Spaces.objects.filter(title__icontains=self.title).exists():
            rand_number = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
            self.slug = f"{slugify(self.title)}-{rand_number}"
        else:
            self.slug = slugify(self.title)
        super(Spaces, self).save(*args, **kwargs)


class SpaceJourney(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journey = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name="journry_space")
    space = models.ForeignKey(Spaces, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.journey.title)


class SpaceMembers(Timestamps):
    user_types = (
        ("Admin", "Admin"),
        ("Moderator", "Moderator"),
        ("Member", "Member"),
    )
    status_types = (
        ("Accept", "Accept"),
        ("Pending", "Pending"),
        ("Reject", "Reject"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=50, choices=user_types, default="Member")
    space = models.ForeignKey(Spaces, on_delete=models.CASCADE)
    space_group = models.ForeignKey(SpaceGroups, on_delete=models.CASCADE)
    is_joined = models.BooleanField(default=False)
    email = models.EmailField(max_length=254)
    is_invited = models.BooleanField(default=False)
    invitation_status = models.CharField(max_length=50, choices=status_types, default="Pending")
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    update_by = models.CharField(max_length=255, null=True)
    deleted_by = models.CharField(max_length=255, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'space', 'is_joined', 'is_active', 'is_delete']),
            models.Index(fields=['user', 'space_group', 'is_joined', 'is_active', 'is_delete']),
            models.Index(fields=['user', 'space_group', 'is_joined', 'is_active', 'is_delete', 'space']),
            models.Index(fields=['user', 'is_active', 'is_delete']),
            models.Index(fields=['space_group', 'is_joined', 'is_active', 'is_delete']),

        ]
        ordering = ('-created_at',)

    def __str__(self):
        return self.user.username


class CommunityTags(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    alernate_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Post(Timestamps):
    post_types = (
        ("Post", "Post"),
        ("Article", "Article"),
        ("Discussion", "Discussion"),
        ("KeyPoints", "KeyPoints"),
        ("AskQuestions", "AskQuestions"),
        ("WeeklyJournal", "WeeklyJournal"),
        ("Event", "Event")
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    Body = models.TextField()
    cover_image = models.ImageField(upload_to='atpace_community/cover_images/')
    tags = models.ManyToManyField(CommunityTags, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    post_type = models.CharField(max_length=50, choices=post_types, default="Post")
    is_comments_enabled = models.BooleanField(default=True)
    is_liking_enabled = models.BooleanField(default=True)
    is_archieve = models.BooleanField(default=False)
    inappropriate_content = models.BooleanField(default=False)
    space = models.ForeignKey(Spaces, on_delete=models.CASCADE, db_index=True)
    space_group = models.ForeignKey(SpaceGroups, on_delete=models.CASCADE)
    notify_space_members = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    update_by = models.CharField(max_length=255, null=True)
    deleted_by = models.CharField(max_length=255, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bg_image = models.FileField(upload_to='uploads/event/', default="https://assets.dyte.io/backgrounds/bg_0.jpg")
    class Meta:
        indexes = [
            models.Index(fields=['space', 'is_active', 'is_delete']),
            models.Index(fields=['is_active', 'is_delete']),
            models.Index(fields=['created_at']),
            models.Index(fields=['post_type', 'space']),
            models.Index(fields=['space_group', 'space']),
            models.Index(fields=['post_type', 'is_active', 'is_delete', 'space']),
            models.Index(fields=['created_by', 'space', 'is_active', 'is_delete'])

        ]
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if Post.objects.filter(title__icontains=self.title).exists():
            rand_number = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
            self.slug = f"{slugify(self.title)}-{rand_number}"
        else:
            self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)


class Comment(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Body = models.TextField(max_length=500)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    parent_id = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    cover_image = models.ImageField(upload_to='atpace_community/cover_images/')
    inappropriate_content = models.BooleanField(default=False)
    comment_for = models.CharField(max_length=50, choices=types, default="Post")
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    update_by = models.CharField(max_length=255, null=True)
    deleted_by = models.CharField(max_length=255, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['parent_id', 'is_active', 'is_delete']),
            models.Index(fields=['post', 'parent_id', 'comment_for', 'is_active', 'is_delete']),
        ]
        ordering = ('-created_at',)

    def __str__(self):
        return self.post.title


class Attachments(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    image_upload = models.ImageField(upload_to='atpace_community/images/')
    file_upload = models.FileField(upload_to='atpace_community/files/')
    upload_for = models.CharField(max_length=50, choices=types, default="Post")

    class Meta:
        indexes = [
            models.Index(fields=['post', 'upload_for']),
        ]


class likes(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_like = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    like_for = models.CharField(max_length=50, choices=types, default="Post")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['comment', 'is_like', 'created_by']),
            models.Index(fields=['post', 'is_like', 'created_by']),
            models.Index(fields=['comment', 'is_like']),
            models.Index(fields=['post', 'is_like']),
        ]


class Follow(Timestamps):
    follow_types = (
        ("Post", "Post"),
        ("User", "User"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    is_follow = models.BooleanField(default=False)
    follow_to = models.CharField(max_length=50, choices=follow_types, default="Post")
    followed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follow_by")


class SavedPost(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    is_saved = models.BooleanField(default=True)
    saved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_by")
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_by")

    class Meta:
        indexes = [
            models.Index(fields=['saved_by', 'is_saved', 'post', 'is_active', 'is_delete']),
        ]
        ordering = ('-created_at',)


class NotificationSettings(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    commented_your_post = models.BooleanField(default=False)
    liked_your_post = models.BooleanField(default=False)
    post_shared_by_someone = models.BooleanField(default=False)
    post_shared_by_you = models.BooleanField(default=False)
    followed_your_post = models.BooleanField(default=False)
    receive_message = models.BooleanField(default=False)
    get_email_notification = models.BooleanField(default=False)
    get_email_notification_new_community_post = models.BooleanField(default=False)


class Report(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    post_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reporter")
    is_report = models.BooleanField(default=False)
    report_type = models.CharField(max_length=100, choices=report_types, default=None)
    comment = models.TextField(max_length=1000)
    
    class Meta:
        ordering = ('-created_at',)


class Search(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    search_key = models.TextField(max_length=500)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="search_by", blank=True, null=True)

    def __str__(self):
        return self.search_key


class MemberInvitation(Timestamps):
    select = (
        ("Accept", "Accept"),
        ("Pending", "Pending"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invite_email = models.EmailField(max_length=254)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inviter")
    invite_by_id = models.CharField(max_length=50)
    status = models.BooleanField(default=False)
    string = models.CharField(max_length=50)
    invite_status = models.CharField(max_length=50, choices=select, default="Pending")


class Event(Timestamps):
    location = (
        ("URl (Zoom, YouTube Live)", "URl (Zoom, YouTube Live)"),
        ("In person", "In person"),
        ("TBD", "TBD")
    )
    frequency = (
        ("Does Not Repeat", "Does Not Repeat"),
        ("Repeat everyday", "Repeat everyday")
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, db_index=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, choices=location, default="URl (Zoom, YouTube Live)")
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="event_attendees", default=None)
    members_joined = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="members_joined", default=None)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_host")
    frequency = models.CharField(max_length=255, choices=frequency, default="Does Not Repeat")
    is_tbd = models.BooleanField(default=False)
    event_url = models.TextField()
    is_location_hidden = models.BooleanField(default=False)
    is_email_notification = models.BooleanField(default=False)
    is_in_app_notification = models.BooleanField(default=False)
    is_email_remainder = models.BooleanField(default=False)
    is_in_app_remainder = models.BooleanField(default=False)
    is_customize_msg = models.BooleanField(default=False)
    add_to_collabarate = models.BooleanField(default=False)
    collabarate_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.post_id.title

    class Meta:
        indexes = [
            models.Index(fields=['post_id']),
        ]
        ordering = ('-created_at',)
        
class UserPinnedPost(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pinned_by")
    space = models.ForeignKey(Spaces, on_delete=models.CASCADE, related_name="pinned_space", null=True)
    space_group = models.ForeignKey(SpaceGroups, on_delete=models.CASCADE, related_name="pinned_space_group", null=True, blank=True)
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return self.post.title

    class Meta:
        indexes = [
            models.Index(fields=['post', 'space']),
        ]
        ordering = ('-created_at',)

class ContentToReview(Timestamps):
    types = (
        ("Post", "Post"),
        ("Comment", "Comment"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    space = models.ForeignKey(Spaces, on_delete=models.CASCADE, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True)
    posted_on = models.CharField(max_length=20, choices=types, default="Post")
    is_reviewed = models.BooleanField(default=False)
    post_on_community = models.BooleanField(default=False)
    profanity_words = models.TextField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviewed_by", null=True)

    def __str__(self):
        return self.post.title

    class Meta:
        ordering = ('-created_at',)