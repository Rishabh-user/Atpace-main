from django.db import models
import uuid
from apps.content.models import Channel
from ravinsight.constants import Pool_Choice
from apps.utils.models import Industry, Tags, Timestamps
from apps.users.models import Collabarate, Company, Learner, Mentor, User


# Create your models here.


class Pool(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="poll_journey")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="poll_company", blank=True, null=True)
    description = models.TextField(blank=True)
    name = models.CharField(max_length=255)
    pool_by = models.CharField(max_length=30, choices=Pool_Choice, default="ALL")
    tags = models.ManyToManyField(Tags, blank=True)
    industry = models.ManyToManyField(Industry, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.CharField(max_length=30)


class PoolMentor(Timestamps):
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name="all_pools")
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)


CALLTYPE = (
    ("Does not repeat", "Does not repeat"),
    ("Daily", "Daily"),
    ("Weekly", "Weekly"),
    ("Monthly", "Monthly"),
)

SLOTSTATUS = (
    ("Booked", "Booked"),
    ("Available", "Available")
)
CALLSTATUS = (
    ('Upcoming', 'Upcoming'),
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
)


class mentorCalendar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    url_title = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=200, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True)
    participants = models.ManyToManyField(User, related_name="participants_list", default=None)
    start_time = models.DateTimeField(blank=True)
    end_time = models.DateTimeField(blank=True)
    url = models.TextField(blank=True)
    reminder = models.IntegerField(null=True, default=0)
    call_type = models.CharField(max_length=50, choices=CALLTYPE, default="Does not repeat")
    slot_status = models.CharField(max_length=50, choices=SLOTSTATUS, default="Available")
    status = models.CharField(max_length=20, choices=CALLSTATUS, default="Upcoming")
    bookmark = models.BooleanField(default=False)
    is_cancel = models.BooleanField(default=False)
    created_by = models.CharField(max_length=100, blank=True)
    created_by_id = models.CharField(max_length=100, blank=True)
    cancel_by = models.CharField(max_length=100, blank=True)
    cancel_by_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class BookmarkMentor(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="bookmark_mentor")
    user = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="bookmark_user")
    is_favourite = models.BooleanField(default=False)


class AssignMentorToUser(Timestamps):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="assign_mentor")
    user = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="assign_user")
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, )
    assign_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assign_by", null=True, blank=True)
    revoked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devoked_by", null=True, blank=True)
    is_assign = models.BooleanField(default=True)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['mentor', 'user', 'journey']),
            models.Index(fields=['user', 'journey']),
            models.Index(fields=['user', 'is_assign'])
        ]

    def __str__(self):
        return f"{self.mentor.email} - {self.journey.title}"
    
class MenteeSummary(Timestamps):
    mentee = models.ForeignKey(Learner, on_delete=models.CASCADE)
    summary = models.TextField()
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)

class MentorSummary(Timestamps):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    summary = models.TextField()
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)

class AllMeetingDetails(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor_meeting = models.ForeignKey(mentorCalendar, on_delete=models.CASCADE, null=True)
    collaborate_meeting = models.ForeignKey(Collabarate, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=50)
    start_time = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    ongoing = models.BooleanField(default=False)
    max_participants = models.IntegerField()

    def __str__(self):
        return self.title[:-5]

    class Meta:
        ordering = ['-created_at']


class MeetingParticipants(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AllMeetingDetails, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=50)
    join_time = models.IntegerField()
    duration = models.IntegerField()

    def __str__(self):
        return self.user_name

    class Meta:
        ordering = ['-created_at']

class DyteAuthToken(Timestamps):
    # user_id = models.CharField(max_length=50, null=False)
    user_name = models.CharField(max_length=50, null=False)
    email = models.CharField(max_length=50, null=False)
    authToken = models.CharField(max_length=1024, null=False)
    preset = models.CharField(max_length=50, null=False)
    preset_id = models.CharField(max_length=50, null=False)
    meeting_id = models.CharField(max_length=50, null=False)
    participant_id = models.CharField(max_length=50, null=False)
    call_type = models.CharField(max_length=16, null=False, default="unknown call")
    
class DyteMeetDetails(Timestamps):
    event = models.CharField(max_length=25, null=False)

    meet_id = models.CharField(max_length=30, null=False)
    session_id = models.CharField(max_length=30, null=False)
    meet_title = models.CharField(max_length=25, null=False)
    roomName = models.CharField(max_length=30, null=False)
    meet_status = models.CharField(max_length=20, null=False)
    meet_created_at = models.CharField(max_length=25, null=False) 
    meet_started_at = models.CharField(max_length=30, null=False)
    organizer_id = models.CharField(max_length=25, null=False)
    organizer_name = models.CharField(max_length=25, null=False)

    peer_id = models.CharField(max_length=25, null=False)
    user_name = models.CharField(max_length=30, null=False)
    user_custom_id = models.CharField(max_length=35, null=False)
    client_specific_id = models.CharField(max_length=30, null=False)
    left_at = models.CharField(max_length=25, null=False)
    joined_at = models.CharField(max_length=25, null=False)
