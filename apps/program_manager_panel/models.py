from datetime import timedelta
import uuid
from django.db import models
from django.db.models import F
from django.conf import settings
from apps.content.models import Channel
from apps.users.models import Company, Learner
from apps.utils.models import ModelActiveDelete, Timestamps
from apps.community.models import LearningJournals
from apps.community.models import WeeklyLearningJournals
from ravinsight.constants import period_type, recurring_choices, task_status_choices
# Create your models here.


class Subscription(Timestamps, ModelActiveDelete):
    subs_type = (
        ("Free", "Free"),
        ("Scaleup", "Scaleup"),
        # ("Premium", "Premium"),
        ("Enterprise", "Enterprise"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    terms_conditions = models.TextField()
    price = models.IntegerField(default=1)
    currency = models.CharField(default="USD", max_length=10)
    duration = models.IntegerField(default=1)
    trial_duration = models.IntegerField(default=0)
    is_paid = models.BooleanField(default=False)
    duration_type = models.CharField(max_length=50, choices=period_type, default="Month")
    is_trial = models.BooleanField(default=False)
    trial_period = models.CharField(max_length=50, choices=period_type, default="Month")
    sub_type = models.CharField(max_length=50, choices=subs_type, default="Free")
    on_offer = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} - {self.sub_type}"

    class Meta:
        ordering = ('-created_at',)


class SubscriptionOffer(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    terms_conditions = models.TextField()
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    is_discount = models.BooleanField(default=False)
    discount_percentage = models.IntegerField(default=0)
    discount_price = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)
    duration_type = models.CharField(max_length=50, choices=period_type, default="Days")
    final_price = models.IntegerField(default=0)
    currency = models.CharField(default="USD", max_length=10)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title}"

    def subs_price(self, discount_percentage, subscription):
        print(f"final_price  {discount_percentage} price {subscription.price}")
        final_price = (((100-discount_percentage)/100)*subscription.price)
        print("final_price ", final_price)
        self.final_price = final_price
        self.save()

    def final_prices(self, discount_price, subscription):
        print("discount_price ", discount_price)
        self.final_price = subscription.price - round(discount_price)
        self.save()

    def durations(self, end_date, start_date):
        self.duration = (end_date - start_date).days
        self.save()

    class Meta:
        ordering = ('-created_at',)


class SubcribedUser(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    is_subscribed = models.BooleanField(default=False)
    offer_applied = models.BooleanField(default=False)
    subscription_offer = models.ForeignKey(SubscriptionOffer, on_delete=models.CASCADE, blank=True, null=True)
    is_cancel = models.BooleanField(default=False)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    canceling_reason = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.subscription.title}"

    def subscription_end_time(self, start_date, duration, duration_type):
        if duration_type == 'Days':
            days = duration
        elif duration_type in ['Month', 'Months']:
            days = duration * 30
        elif duration_type in ['Year', 'Years']:
            days = duration * 365
        self.end_date = start_date + timedelta(days=days)
        self.save()

    class Meta:
        ordering = ('-created_at',)


class MentorMenteeRatio(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True)
    user_subscription = models.ForeignKey(SubcribedUser, on_delete=models.CASCADE, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True)
    max_mentor = models.IntegerField(default=0)
    max_learner = models.IntegerField(default=0)
    learners_per_mentor = models.IntegerField(default=0)
    max_member = models.IntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    def max_member_count(self, max_mentor, max_learner):
        self.max_member = max_mentor + max_learner
        self.save()

    # def __str__(self):
    #     return f"{self.subscription.title}"

    class Meta:
        ordering = ('-created_at',)


class MentorMenteeTrack(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentor")
    company = models.ManyToManyField(Company)
    journey = models.ManyToManyField(Channel)
    mentee = models.ManyToManyField(Learner)
    company_count = models.IntegerField(default=0)
    journey_count = models.IntegerField(default=0)
    mentee_count = models.IntegerField(default=0)
    mentee_ratio = models.ForeignKey(MentorMenteeRatio, on_delete=models.CASCADE)

    def max_company_count(self, company):
        self.company_count = F('company_count') + company.objects.count()
        self.save()

    def max_journey_count(self, journey):
        self.journey_count = F('journey_count') + journey.objects.count()
        self.save()

    def max_mentee_count(self, mentee):
        self.mentee_count = F('mentee_count') + mentee.objects.count()
        self.save()

    def __str__(self):
        return f"{self.mentor.first_name} {self.mentor.last_name}"

    class Meta:
        ordering = ('-created_at',)


class MessageScheduler(Timestamps, ModelActiveDelete):
    receiver_choices = (
        ("Mentee", "Mentee"),
        ("Mentor", "Mentor"),
        ("Program_Manager","Program_Manager"),
        ("Both", "Both")
    )
    day_choices = (
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thrusday", "Thrusday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday")
    )
    platform_choices = (
        ("Whatsapp","Whatsapp"),
        ("Mail","Mail"),
        ("Chat","Chat")
    )
    scheduler_type = (
        ("Reminder_to_Journnal","Reminder_to_Journnal"),
        ("Program_Team_Weekly","Program_Team_Weekly")
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    day = models.CharField(max_length=50, choices=day_choices, default="Friday")
    time = models.TimeField()
    start_date = models.DateField(auto_now=True)
    end_date = models.DateField(blank=True, null=True)
    receiver = models.CharField(max_length=50, choices=receiver_choices, default="Mentee")
    receiver_platform = models.CharField(max_length=50, choices=platform_choices, default="Mail")
    scheduler_type = models.CharField(max_length=50, choices=scheduler_type, default="Reminder_to_Journnal")
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, blank=True, null=True)
    journal = models.ForeignKey(WeeklyLearningJournals, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField()
    button_action = models.URLField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="scheduler_created_by")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="scheduler_updated_by", blank=True, null=True)


    class Meta:
        ordering = ('-created_at',)


class ReminderToJournal(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(LearningJournals, on_delete=models.CASCADE )
    class Meta:
        ordering = ('-created_at',)

class ProgramTeamWeekly(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    microskill_percentage = models.CharField(max_length=250, blank=True, null=True)
    learning_percentage = models.CharField(max_length=250, blank=True, null=True)
    microskill_percentage = models.CharField(max_length=250, blank=True, null=True)
    no_activity_users = models.CharField(max_length=250, blank=True, null=True)
    class Meta:
        ordering = ('-created_at',)


class MessageSchedulerHistory(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_scheduler = models.ForeignKey(MessageScheduler, on_delete=models.CASCADE)
    receivers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    program_team_weekly = models.ForeignKey(ProgramTeamWeekly, on_delete=models.CASCADE)
    reminder_to_journal = models.ForeignKey(ReminderToJournal, on_delete=models.CASCADE)
    class Meta:
        ordering = ('-created_at',)

class ProgramManagerTask(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    description = models.TextField(max_length=100)
    is_recurring = models.BooleanField(default=False)
    task_type = models.CharField(max_length=128, choices=recurring_choices)
    meta_key = models.CharField(max_length=128)
    meta_value = models.CharField(max_length=128)
    recurring_times = models.CharField(max_length=128, choices=recurring_choices)
    set_remainder = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now=False, auto_now_add=False)
    due_time = models.DateTimeField(auto_now=False, auto_now_add=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="task_created_by")
    
class TaskRemainder(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(ProgramManagerTask, on_delete=models.CASCADE)
    remainder_time = models.CharField(max_length=128, choices=recurring_choices)
    remainder_before = models.IntegerField(default=1) #currently using
    
class AssignTaskToUser(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(ProgramManagerTask, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_assigned_to")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_assigned_by")
    is_assigned = models.BooleanField(default=True)
    is_revoked = models.BooleanField(default=False)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_revoked_by", null=True, blank=True)
    task_status = models.CharField(max_length=128, choices=task_status_choices, default="Not Started")
    status_updated_on = models.DateTimeField(auto_now=True)
    comment = models.TextField(blank=True, null=True)