import uuid
from django.conf import settings
from apps.users.models import Company, UserEarnedPoints
from apps.utils.models import Timestamps
from django.db import models
from apps.content.models import Channel
from datetime import datetime
from apps.users.models import User


# Create your models here.

Badges_For = (
    ("User", "User"),
    ("Mentor", "Mentor"),
)


class PointsTable(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=100, blank=True, null=True)
    points = models.IntegerField(default=0)
    comment = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-created_at',)


class BadgeDetails(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    image = models.ImageField(upload_to='leaderboard/badges/')
    label = models.ForeignKey(PointsTable, on_delete=models.CASCADE, null=True)
    points_required = models.IntegerField(default=0)
    badge_for = models.CharField(max_length=10, choices=Badges_For, default="User")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)


class UserBadgeDetails(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_badge = models.ForeignKey(BadgeDetails, on_delete=models.CASCADE, null=True)
    points_earned = models.IntegerField(default=0)
    badge_acquired = models.BooleanField(default="False")
    badge_revoked = models.BooleanField(default="False")

    class Meta:
        ordering = ('-created_at',)


class UserPoints(Timestamps):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    label = models.ForeignKey(PointsTable, on_delete=models.CASCADE, null=True)
    point = models.BigIntegerField(default=0)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        try:
            UserEarnedPoints.objects.get(user=self.user)
            print("self.point", self.point)
            self.user.user_earned_points.modify_point(self.point)

        except UserEarnedPoints.DoesNotExist:
            print("self.pointexcept", self.point)
            UserEarnedPoints.objects.create(user=self.user, total_points=self.point)
        super(UserPoints, self).save(*args, **kwargs)


Goals_For = (
    ("User", "User"),
    ("Mentor", "Mentor"),
)
level = (
    ("High", "High"),
    ("Medium", "Medium"),
    ("Low", "Low")
)
Goal_type = (
    ("System Driven", "System Driven"),
    ("User Driven", "User Driven"),
    ("Mentorship", "Mentorship")
)

goal_frequency = (
    ("Hourly", "Hourly"),
    ("Daily", "Daily"),
    ("Weekly", "Weekly"),
    ("Monthly", "Monthly")
)


class SystemDrivenGoal(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    heading = models.CharField(max_length=255)
    description = models.TextField()
    goal_for = models.CharField(max_length=10, choices=Goals_For, default="User")
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True)
    content = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    difficulty_level = models.CharField(max_length=10, choices=level, default="Medium")
    priority_level = models.CharField(max_length=10, choices=level, default="Medium")
    frequency = models.CharField(max_length=15, choices=goal_frequency, default="Daily")
    on_complete_points = models.IntegerField(default=0)
    on_complete_badges = models.ForeignKey(BadgeDetails, on_delete=models.CASCADE, null=True)
    on_complete_gifts = models.CharField(max_length=255, blank=True, null=True)
    goal_type = models.CharField(max_length=15, choices=Goal_type, default="User Driven")
    complete_till = models.DateTimeField(default=datetime.now, blank=True)
    goal_remainder = models.DateTimeField(default=datetime.now, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default="True")
    is_deleted = models.BooleanField(default="False")


status = (
    ("None", "None"),
    ("Accepted", "Accepted"),
    ("Completed", "Completed"),
    ("Rejected", "Rejected"),
    ("Failed", "Failed"),
    ("Skipped", "Skipped"),
    ("ApprovedByMentor", "ApprovedByMentor"),
    ("RejectedByMentor", "RejectedByMentor"),
    ("RequestForApprove", "RequestForApprove"),
    ("Started", "Started"),
    ("25%_done", "25%_done"),
    ("75%_done", "75%_done"),
    ("50%_done", "50%_done"),

)


class UserAssignedGoal(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    goal = models.ForeignKey(SystemDrivenGoal, on_delete=models.CASCADE)
    status = models.CharField(max_length=25, choices=status)
    progress = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)


category = (
    ("Gain Clarity", "Gain Clarity"),
    ("Learn", "Learn"),
    ("Health", "Health"),
    ("Follow Through", "Follow Through")
)
duration = (
    ("Mins", "Mins"),
    ("Times", "Times")
)


class MentorshipGoalComment(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name="comment_created_by", null=True, blank=True)
    comment = models.TextField()
    mentor_reply = models.TextField()

    class Meta:
        ordering = ('-created_at',)


class UserDrivenGoal(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   null=True, related_name="goal_created_by")
    heading = models.CharField(max_length=255)
    description = models.TextField()
    learners = models.ManyToManyField(User, blank=True, related_name="assign_to")
    duration_number = models.CharField(max_length=255, blank=True, null=True)
    duration_time = models.CharField(max_length=10, choices=duration, default="Mins")
    category = models.CharField(max_length=255, choices=category, default="Learn")
    difficulty_level = models.CharField(max_length=10, choices=level, default="Medium")
    priority_level = models.CharField(max_length=10, choices=level, default="Medium")
    frequency = models.CharField(max_length=15, choices=goal_frequency, default="Daily")
    goal_type = models.CharField(max_length=15, choices=Goal_type, default="User Driven")
    complete_till = models.DateTimeField(default=datetime.now, blank=True)
    goal_remainder = models.DateTimeField(default=datetime.now, blank=True)
    progress_percentage = models.IntegerField(default=0)
    comment = models.ManyToManyField(MentorshipGoalComment, blank=True, related_name="goal_comment")
    approve_request = models.ManyToManyField(User, blank=True, related_name="goal_approve")
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)


class UserGoalLog(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    goal = models.ForeignKey(UserDrivenGoal, on_delete=models.CASCADE)
    status = models.CharField(max_length=25, choices=status)
    progress_percentage = models.IntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True,
                                   related_name="goal_log_created_by")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True,
                                   related_name="goal_log_updated_by")

    class Meta:
        ordering = ('-created_at',)


class StreakPoints(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    duration_in_days = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    comment = models.TextField(blank=True)
    is_active = models.BooleanField(default="True")
    is_deleted = models.BooleanField(default="False")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)


class UserStreakCount(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    streak_count = models.IntegerField(default=1)
    streak_count_start_date = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        ordering = ('-created_at',)


class UserStreak(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_streak_done = models.BooleanField(default="False")
    streak_done_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)


class UserStreakHistory(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    streak = models.IntegerField(default=1)
    start_date = models.DateTimeField(blank=True)
    end_date = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        ordering = ('-created_at',)


class UserEngagement(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    login_time = models.DateTimeField(blank=True)
    logout_time = models.DateTimeField(default=datetime.now, blank=True)
    engagement_time = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('-created_at',)


class AutoApproveGoal(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    is_auto_approve = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="is_auto_approve_created_by", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="is_auto_approve_updated_by", null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
