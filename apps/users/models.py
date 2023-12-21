
import uuid
import datetime
import jsonfield
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F
from django.db.models.deletion import CASCADE
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField
from ravinsight.constants import Privacy_types, gender
from apps.utils.models import Industry, Tags, Timestamps
# Create your models here.

# SECTION : Address


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=250)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50, null=True, blank=True)
    zip_code = models.IntegerField(null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


# SECTION : Company


class Company(Address):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    logo = models.ImageField(upload_to='company/company_logo/', null=True, blank=True)
    banner = models.ImageField(upload_to='company/company_banner/', null=True, blank=True)
    color_theme = models.CharField(max_length=50, null=True, blank=True)
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# SECTION: User Types


class UserTypes(models.Model):
    class Types(models.TextChoices):
        ADMIN = "Admin"
        APP_USER = "Learner"
        MENTOR = "Mentor"
        PROGRAM_MANAGER = "ProgramManager"  # ProgramManager
        CREATOR = "Creator"

    type = models.CharField(("Type"), max_length=50, choices=Types.choices, default=Types.APP_USER)

    def __str__(self):
        return self.type


# SECTION : Super User

marketplace_status = (
    ("Pending","Pending"),
    ("In Review","In Review"),
    ("Approved","Approved"),
    ("Rejected","Rejected"),
    ("Live","Live"),
    ("None","None")
)

class User(AbstractUser, Address):
    # User types
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    userType = models.ManyToManyField(UserTypes, default=UserTypes.Types.APP_USER)
    company = models.ManyToManyField(Company, related_name="company")
    profile_heading = models.CharField(max_length=255, blank=True)
    private_profile = models.BooleanField(default=False)
    about_us = models.CharField(max_length=255, blank=True)
    phone = PhoneNumberField(null=True, blank=True, unique=True, db_index=True)
    gender = models.CharField(max_length=20, choices=gender, blank=True)
    age = models.CharField(max_length=100, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    current_status = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=100, blank=True)
    expertize = models.ManyToManyField(Tags, blank=True)
    industry = models.ManyToManyField(Industry, blank=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    twitter_profile = models.URLField(blank=True, null=True)
    instagram_profile = models.URLField(blank=True, null=True)
    facebook_profile = models.URLField(blank=True, null=True)
    favourite_way_to_learn = models.CharField(max_length=255, blank=True)
    interested_topic = models.CharField(max_length=200, blank=True)
    upscaling_reason = models.CharField(max_length=200, blank=True)
    time_spend = models.CharField(max_length=200, blank=True)
    prefer_not_say = models.BooleanField(blank=True, null=True)
    timespend = models.FloatField(default=0)
    is_whatsapp_enable = models.BooleanField(default=False)
    is_term_and_conditions_apply = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_social_login = models.BooleanField(default=False)
    facebook_account_id = models.CharField(max_length=255, blank=True, null=True)
    google_account_id = models.CharField(max_length=255,
                                         blank=True, null=True)
    social_login_type = models.CharField(max_length=255, blank=True)
    pdpa_statement = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='user_avtar/', default="static/dist/img/avatar.png", null=True)
    coupon_code = models.CharField(max_length=20, blank=True)
    is_archive = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=20, blank=True)
    user_status = models.BooleanField(default=False)
    token = models.CharField(max_length=255, null=True)
    is_lite_signup = models.BooleanField(default=False)
    date_modified = models.DateTimeField(null=True)
    profile_assest_enable = models.BooleanField(default=True)
    is_email_private = models.BooleanField(default=False)
    is_phone_private = models.BooleanField(default=False)
    is_linkedin_private = models.BooleanField(default=False)
    admin_publish_on_marketplace = models.BooleanField(default=False) #Admin or Program Manager allow mentor profile to pushlish on marketplace
    mentor_publish_on_marketplace = models.BooleanField(default=False) #Mentor request for publish on marketplace
    marketplace_status = models.CharField(choices=marketplace_status, default="None", max_length=15)
    is_guest = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"

    class Meta:
        ordering = ('-date_modified',)
        indexes = [models.Index(fields=['email'])]
        indexes = [models.Index(fields=['is_active', 'is_superuser', 'is_staff'])]
    # user Defined 1
    # user Defined 2
    # user Defined 3

# SECTION : Admin User


class UserEarnedPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_earned_points")
    total_points = models.BigIntegerField(default=0)

    def modify_point(self, points):
        self.total_points = F('total_points') + points
        self.save()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)


class FirebaseDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firebase_token = models.TextField(max_length=255)
    device_id = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.username} - {self.device_id}"


class AdminUserManager(BaseUserManager):

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(userType__type=UserTypes.Types.ADMIN)


class AdminUser(User):
    """
        Learner is the user who actually uses the application.
    """
    objects = AdminUserManager()

    class Meta:
        proxy = True

    def __str__(self):
        return self.username


# SECTION : App User


class LearnerManager(BaseUserManager):

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(userType__type=UserTypes.Types.APP_USER)


class Learner(User):
    """
        Learner is the user who actually uses the application.
    """

    objects = LearnerManager()

    class Meta:
        proxy = True

    def __str__(self):

        return self.username


@receiver(post_save, sender=Learner)
def add_user_type(sender, instance, **kwargs):
    instance.userType.add(UserTypes.objects.get(type=UserTypes.Types.APP_USER))


# SECTION : Mentor User


class MentorManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(userType__type=UserTypes.Types.MENTOR)


class Mentor(User):
    """
        Mentor is the user who monitor the activity of assigned user.
    """

    objects = MentorManager()

    class Meta:
        proxy = True

    def __str__(self):
        return self.username


# SECTION : ProgramManager User


class ProgramManagerManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(userType__type=UserTypes.Types.PROGRAM_MANAGER)


class ProgramManager(User):
    """
        Who are responsible to create and manage content.
    """

    objects = ProgramManagerManager()

    class Meta:
        proxy = True

    def __str__(self):
        return self.username


class CreatorManager(BaseUserManager):

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(userType__type=UserTypes.Types.CREATOR)


class CreatorUser(User):
    """
        Learner is the user who actually uses the application.
    """
    objects = CreatorManager()

    class Meta:
        proxy = True

    def __str__(self):
        return self.username


# SECTION : App User


# SECTION : CSV File Model

class CSVFile(models.Model):
    """
        Represent a csv-file model.
    """
    file = models.FileField(upload_to="mentee_activity_rasa/")


class UserCompany(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True, )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_company")


class UserRoles(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ProficiencyLevel(models.Model):
    level = models.CharField(max_length=100)
    start = models.IntegerField(default=0)
    end = models.IntegerField(default=10)


class ProfileAssestQuestion(models.Model):
    class Types(models.TextChoices):
        LEARNER = "Learner"
        MENTOR = "Mentor"
        PROGRAM_MANAGER = "ProgramManager"

    option_type = (
        ("Options", "Options"),
        ("Text", "Text")
    )

    question = models.TextField()
    journey = models.CharField(max_length=255, blank=True, null=True)
    options = jsonfield.JSONField(blank=True, null=True)
    question_type = models.CharField(max_length=100, choices=option_type, default="Options")
    question_for = models.CharField(max_length=100, choices=Types.choices)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    is_multichoice = models.BooleanField(default=False)
    display_order = models.IntegerField(default=1)

    class Meta:
        ordering = ('display_order',)


class UserProfileAssest(Timestamps):
    Type = (
        ("Learner", "Learner"),
        ("Mentor", "Mentor"),
        ("ProgramManager", "ProgramManager")
    )

    user = models.ForeignKey(User, on_delete=CASCADE, related_name="user_profile_assest")
    assest_question = models.ForeignKey(ProfileAssestQuestion, on_delete=CASCADE)
    response = models.TextField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    question_for = models.CharField(max_length=100, choices=Type, blank=True)

    def __str__(self):
        return self.user.email


# class UserDeviceDetails(models.Model):
#     ip_address = models.CharField(max_length=50, null=True)
#     device_type = models.CharField(max_length=50)
#     device_type_family = models.CharField(max_length=50)
#     device_type_brand = models.CharField(max_length=50, null=True)
#     device_type_model = models.CharField(max_length=50, null=True)
#     browser_type_family = models.CharField(max_length=50)
#     browser_version = models.CharField(max_length=50)
#     os_type = models.CharField(max_length=50)
#     os_version = models.CharField(max_length=50)


# class InstructorModel(Timestamps):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     first_name = models.CharField(max_length=100)
#     avator_name = models.CharField(max_length=100)
#     heading = models.CharField(max_length=100)
#     about_us = models.TextField()
#     avator = models.ImageField()

class Coupon(Timestamps):
    Type = (
        ("Discount", "Discount"),
        ("Journey", "Journey")
    )
    name = models.CharField(max_length=100, default="")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField(auto_now=False, auto_now_add=False)
    valid_to = models.DateTimeField(auto_now=False, auto_now_add=False)
    type = models.CharField(max_length=10, choices=Type, default="Journey")
    journey = models.CharField(max_length=100, blank=True)
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    is_active = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.code


class CouponApply(Timestamps):
    code = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_coupan")
    applied = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Collabarate(Timestamps):
    Type = (
        ("LiveStreaming", "LiveStreaming"),
        ("GroupStreaming", "GroupStreaming")
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=128, unique=True, blank=False)
    url_title = models.CharField(max_length=200, blank=True)
    journey = models.CharField(max_length=200, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    description = models.CharField(max_length=200, blank=True)
    custom_url = models.TextField()
    speaker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Stream_Speaker")
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=Type, default="GroupStreaming")
    participants = models.ManyToManyField(User, related_name="participant_users", default=None)
    token = models.TextField()
    record_Video = models.FileField()
    is_active = models.BooleanField(default=True)
    is_cancel = models.BooleanField(default=False)
    recording = models.BooleanField(default=False)
    add_to_community = models.BooleanField(default=False)
    space_name = models.CharField(max_length=200, blank=True, null=True)
    cancel_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cancel_by_user", null=True,)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    custom_background = models.FileField(upload_to='uploads/collabarate/', default="https://assets.dyte.io/backgrounds/bg_0.jpg")


    def __str__(self):
        return f"{self.title} {self.type}"

# class MeetingDetail(Timestamps):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     title = models.CharField(max_length=50, unique=True, blank=False)
#     start_time = models.CharField(max_length=50)
#     duration = models.CharField(max_length=50)
#     ongoing = models.BooleanField(default=False)


class ContactProgramTeam(Timestamps):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    issue = models.TextField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)


class ContactProgramTeamImages(Timestamps):
    contact_program = models.ForeignKey(ContactProgramTeam, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='contact/program_manager/issues/', null=True, blank=True)


class TelegramUserData(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    telegram_group = models.CharField(max_length=128)
    telegram_channel = models.CharField(max_length=128)
    user_id = models.CharField(max_length=128)
    username = models.CharField(max_length=128)
    title = models.CharField(max_length=256)
    chat_type = models.CharField(max_length=256)
    description = models.TextField()
    file = models.FileField()
    url_link = models.BooleanField(default=False)
    message_id = models.IntegerField(default=0)
    is_program_manger = models.BooleanField(default=False)
    is_command = models.BooleanField(default=False)
    is_posted = models.BooleanField(default=False)
    is_acitve = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('-created_at',)
        
    def __str__(self):
        return f"{self.user_id} - {self.username}"


class UserEmailChangeRecord(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    old_email = models.CharField(max_length=25)
    current_email = models.CharField(max_length=25)

    class Meta:
        ordering = ('-created_at',)
        
    def __str__(self):
        return self.user.username
    
class UserPhoneChangeRecord(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    old_phone = models.CharField(max_length=25)
    current_phone = models.CharField(max_length=25)

    class Meta:
        ordering = ('-created_at',)
        
    def __str__(self):
        return self.user.username

class SaveRasaManagerFiles(Timestamps):
    csv_file = models.FileField(upload_to="acitivity/")
    