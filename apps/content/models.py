from statistics import mode
from django.db import models
from django.conf import settings
from django.db.models.deletion import CASCADE
from ravinsight.constants import (Channel_Level_Type,
                                  Channel_type,
                                  Content_Status,
                                  Content_Type, Activity_Type,
                                  UserCourseStatus,
                                  UserReadContentDataStatus)
from apps.utils.models import JourneyCategory, Timestamps
from apps.survey_questions.models import Survey, SurveyAttempt, SurveyLabel
from apps.test_series.models import TestSeries, TestQuestion
from apps.users.models import Company, ProfileAssestQuestion, UserRoles, ProgramManager
import jsonfield
from colorfield.fields import ColorField
import uuid
# Create your models here.

class Channel(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    short_description = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(JourneyCategory, on_delete=CASCADE, null=True, blank=True)
    description = models.TextField()
    color = ColorField(default='#FF0000')
    image = models.ImageField(upload_to='content/channel/')
    parent_id = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    channel_type = models.CharField(max_length=255, choices=Channel_type)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    channel_admin = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="channel_admin")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_by")
    survey = models.ForeignKey(Survey, related_name="channel_survey", on_delete=models.CASCADE, null=True, blank=True)
    test_series = models.ForeignKey(TestSeries, related_name="channel_test_series",
                                    on_delete=models.CASCADE, null=True, blank=True)
    what_we_learn = models.TextField(default="", help_text="Add comman after topic eg. first topic , second topic")
    tags = models.CharField(max_length=255, default="", help_text="Add comman after tag eg. atpace , growatpace")
    amount = models.IntegerField(default=0)
    enroll_validity = models.IntegerField(default=180)
    currency = models.CharField(default="USD", max_length=10)
    is_paid = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)
    is_mentor_enable = models.BooleanField(default=False)
    is_test_required = models.BooleanField(default=True)
    profle_assest_enable = models.BooleanField(default=True)
    program_team_1 = models.ForeignKey(ProgramManager, related_name="program_team_1",
                                       on_delete=models.CASCADE, null=True, blank=True)
    program_team_2 = models.ForeignKey(ProgramManager, related_name="program_team_2",
                                       on_delete=models.CASCADE, null=True, blank=True)
    program_team_email = models.EmailField(null=True, blank=True)
    closure_date = models.DateField(blank=True, null=True)
    is_community_required = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    pdpa_statement = models.BooleanField(default=False)
    is_lite_signup_enable = models.BooleanField(default=False)
    whatsapp_notification_required = models.BooleanField(default=True)
    telegram_notification_required = models.BooleanField(default=True)
    show_on_website = models.BooleanField(default=True)
    feedback_required = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [models.Index(fields=['is_active', 'parent_id', 'is_delete']),
                   models.Index(fields=['is_active', 'is_delete'])]
        ordering = ('-created_at',)

class journeyContentSetup(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)
    overview = models.CharField(max_length=255, blank=True, null=True,
                                help_text="For Course Overview")
    learn_label = models.CharField(max_length=255, blank=True, null=True, help_text="Change label for What we Learn")
    pdpa_description = models.TextField()
    pdpa_label = models.CharField(max_length=255, blank=True, null=True)
    is_delete = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video_url = models.TextField(default="")
    cta_button_title = models.CharField(max_length=255, blank=True, null=True)
    cta_button_action = models.CharField(max_length=255, blank=True, null=True)
    is_draft = models.BooleanField(default=True)

    def __str__(self):
        return self.journey.title

    class Meta:
        ordering = ('-created_at',)

class JourneyContentSetupOrdering(Timestamps):
    Choices = (
        ("overview", "overview"),
        ("learn_label", "learn_label"),
        ("pdpa_description", "pdpa_description"),
        ("pdpa_label", "pdpa_label"),
        ("video_url", "video_url"),
        ("cta_button_title", "cta_button_title"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_setup = models.ForeignKey(journeyContentSetup, on_delete=models.CASCADE, null=True, blank=True)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)
    type = models.CharField(max_length=255, choices=Choices)
    data = models.TextField(default="")
    cta_button_action = models.CharField(max_length=255, blank=True, null=True)
    display_order = models.IntegerField(default=1)
    default_order = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('default_order',)

    
class Content(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='content/', default="/static/dist/default/default-img.gif")
    description = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="content_admin")
    status = models.CharField(max_length=50, choices=Content_Status, default="Draft")
    Channel = models.ForeignKey(Channel, on_delete=models.CASCADE,
                                related_name="channelcontent", null=True, blank=True)
    test_series = models.ForeignKey(TestSeries, on_delete=models.CASCADE, null=True, blank=True)
    is_delete = models.BooleanField(default=False)
    display_order = models.IntegerField(default=1)

    # objects = IsDeleteManager()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('-created_at',)


class ContentChannels(Timestamps):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="content_channel")
    Channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    display_order = models.IntegerField(default=1)
    status = models.CharField(max_length=50, choices=Content_Status, default="Draft")


class ContentData(Timestamps):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="ContentData")
    title = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=Content_Type)
    activity_type = models.CharField(max_length=100, choices=Activity_Type, null=True)
    data = models.TextField(help_text="Description")
    link_data = jsonfield.JSONField(blank=True, null=True)
    file = models.FileField(upload_to='media/', null=True, verbose_name="")
    video = models.FileField(upload_to='media/', null=True, verbose_name="")
    url = models.CharField(max_length=255, null=True, blank=True)
    option_list = jsonfield.JSONField(blank=True, null=True)
    custom_answer = models.BooleanField(default=False)
    display_order = models.IntegerField(default=1)
    time = models.CharField(max_length=10, default="1")
    submit_duration = models.IntegerField(default=10)

    def __str__(self):
        return "content: %s title: %s" % (self.content, self.title)

class UserActivityData(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True)
    content_data = models.ForeignKey(ContentData, on_delete=models.CASCADE)
    is_review = models.BooleanField(default=False)
    upload_file = models.FileField(upload_to='UserActivity/')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_submitted_by")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_reviewed_by", null=True, blank=True)
    is_draft = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

class VideoSubtitles(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video_id = models.IntegerField(null=False, default=None)
    video_file = models.ForeignKey(ContentData, on_delete=models.CASCADE)
    lang_type = models.CharField(max_length=20, null=False,default="English")
    subtitle_file = models.FileField(upload_to=f"subtitles/", )
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)


class ContentDataOptions(Timestamps):
    content_data = models.ForeignKey(ContentData, on_delete=models.CASCADE, related_name="content_data_option")
    option = models.CharField(max_length=100)
    correct_answer = models.BooleanField(default=False)


class ContetnOptionSubmit(Timestamps):
    content_data = models.ForeignKey(ContentData, on_delete=models.CASCADE,
                                     related_name="content_data_option_response")
    option_id = models.IntegerField(blank=True, null=True)
    option = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class ChannelGroup(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True)
    is_restricted = models.BooleanField(default=False)
    channel_for = models.ForeignKey(SurveyLabel, on_delete=models.CASCADE, null=True, blank=True)
    start_mark = models.IntegerField(default=0, blank=True)
    end_marks = models.IntegerField(default=0, blank=True)
    post_assessment = models.ForeignKey(TestSeries, related_name="skill_post_assessment",
                                        on_delete=models.CASCADE, null=True, blank=True)

    is_delete = models.BooleanField(default=False)

    # objects = IsDeleteManager()

    def __str__(self):
        return "Level: %s Journey: %s" % (self.title, self.channel)

    class Meta:
        ordering = ('-created_at',)


class ChannelGroupContent(Timestamps):
    channel_group = models.ForeignKey(ChannelGroup, on_delete=models.CASCADE, related_name="channel_group_content")
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="channel_group_content_details")
    display_order = models.IntegerField(default=1)
    status = models.CharField(max_length=50, choices=Content_Status, default="Pending")
    is_delete = models.BooleanField(default=False)
    feedback_required = models.BooleanField(default=False)


class UserChannel(Timestamps):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_content")
    Channel = models.ForeignKey(Channel, on_delete=models.CASCADE,
                                related_name="user_channel", null=True, blank=True)
    status = models.CharField(max_length=50, default="Pending")
    is_removed = models.BooleanField(default=False)
    is_alloted = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    alloted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="journey_alloted_by", null=True)
    removed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="journey_removed_by", null=True)

    class Meta:

        ordering = ('-created_at',)
        unique_together = ('user', 'Channel',)


class TestAttempt(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True,
                                blank=True, related_name="test_attempt_channel")
    test = models.ForeignKey(TestSeries, on_delete=models.CASCADE, related_name="test_attempt")
    type = models.CharField(max_length=20, default="", blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_attempt")
    quest_id = models.CharField(max_length=50, default="", blank=True, null=True)
    skill_id = models.CharField(max_length=50, default="", blank=True, null=True)
    is_check = models.BooleanField(default=False)
    checked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="test_checked_by", blank=True, null=True)
    checked_on = models.DateTimeField(blank=True, null=True)
    total_marks = models.IntegerField(default=0)
    test_marks = models.IntegerField(default=0)
    user_skill = models.ForeignKey(SurveyLabel, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)


class UserChannelLevel(Timestamps):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=Channel_Level_Type, default="Survey")
    survey_attempt = models.ForeignKey(SurveyAttempt, on_delete=models.CASCADE, null=True, blank=True)
    test_attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, null=True, blank=True)
    skill_level = models.CharField(max_length=100)


class UserTestAnswer(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name="test_attempet_answer")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="test_attempt_user")
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="attempt_quyestion")
    response = models.TextField()
    question_marks = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)

    class Meta:
        ordering = ('-created_at',)


class SkillConfig(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(UserRoles, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="skill_channel")
    journey_pre_assessment = models.ForeignKey(
        TestSeries, on_delete=models.CASCADE, null=True, blank=True,  related_name="journey_pre_assessment")
    sub_channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, related_name="skill_sub_channel")
    pre_assessment = models.ForeignKey(TestSeries, null=True, blank=True,
                                       on_delete=models.CASCADE, related_name="skill_pre_assessment")
    channel_group = models.ForeignKey(ChannelGroup, on_delete=models.CASCADE, null=True,
                                      blank=True, related_name="skill_channel_group")
    assessment = models.ForeignKey(TestSeries, on_delete=models.CASCADE, null=True, blank=True)


class SkillConfigLevel(Timestamps):
    skill_config = models.ForeignKey(SkillConfig, on_delete=models.CASCADE, related_name="skill_config_name")
    channel_group = models.ForeignKey(ChannelGroup, on_delete=models.CASCADE)
    assessment = models.ForeignKey(TestSeries, on_delete=models.CASCADE)


class UserCourseStart(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="content_user")
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="user_content")
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="user_content_channel")
    channel_group = models.ForeignKey(ChannelGroup, on_delete=models.CASCADE, null=True,
                                      blank=True, related_name="user_content_channel_group")
    status = models.CharField(max_length=100, choices=UserCourseStatus, default="Enroll")

    def __str__(self):
        return "status: %s Channel: %s" % (self.status, self.channel)

    class Meta:
        ordering = ('-created_at',)


class SurveyChannel(Timestamps):
    survey = models.ForeignKey(Survey,  on_delete=models.CASCADE, null=True, blank=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)


class SurveyAttemptChannel(Timestamps):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    survey_attempt = models.ForeignKey(SurveyAttempt, related_name="survey_attempt_channel", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class UserReadContentData(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='read_content_user')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="read_content_channel")
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="read_content_content")
    content_data = models.ForeignKey(ContentData, on_delete=models.CASCADE, related_name="read_content_contentdata")
    channel_group = models.ForeignKey(ChannelGroup, on_delete=models.CASCADE, null=True, blank=True)

    status = models.CharField(max_length=100, choices=UserReadContentDataStatus, default="InProgress")

    def __str__(self):
        return "status: %s Channel: %s" % (self.status, self.content)

    class Meta:
        unique_together = ('user', 'content', 'content_data')


class MentoringJourney(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)  # channel
    journey_group = models.ForeignKey(ChannelGroup, on_delete=models.CASCADE)  # channelGroup
    systemKey = models.CharField(max_length=200)
    name = models.CharField(max_length=255, blank=True)
    meta_key = models.CharField(max_length=200)  # type
    value = models.CharField(max_length=200)  # value
    display_order = models.IntegerField(default=1)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_checked = models.BooleanField(default=True) # if not checked the content would be grayed out
    is_delete = models.BooleanField(default=False)


class ProgramTeamAnnouncement(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)  # company
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)  # channel
    topic = models.CharField(max_length=255, blank=True)
    summary = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    announce_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True)
    attachment = models.FileField(upload_to='broadcast/', null=True, blank=True, verbose_name="attachment")

    class Meta:
        ordering = ('-announce_date',)


class MatchQuesConfig(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-created_at',)


class MatchQuestion(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor_ques = models.ForeignKey(ProfileAssestQuestion, on_delete=models.CASCADE,
                                    null=True, blank=True, related_name="mentor_question")
    learner_ques = models.ForeignKey(ProfileAssestQuestion, on_delete=models.CASCADE,
                                     null=True, blank=True, related_name="learner_question")
    ques_config = models.ForeignKey(MatchQuesConfig, null=True, blank=True, on_delete=models.CASCADE)
    question_type = models.CharField(max_length=128, blank=True)
    is_dependent = models.BooleanField(default=False)
    dependent_learner = models.ForeignKey(ProfileAssestQuestion, on_delete=models.CASCADE,
                                          null=True, blank=True, related_name="dependent_learner_question")
    dependent_mentor = models.ForeignKey(ProfileAssestQuestion, on_delete=models.CASCADE,
                                         null=True, blank=True, related_name="dependent_mentor_question")
    dependent_option = models.CharField(max_length=255, blank=True)


class ProgramAnnouncementWhatsappReport(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    announcement = models.ForeignKey(ProgramTeamAnnouncement, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_message_send = models.BooleanField(default=False)
    report_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True)

class PublicProgramAnnouncement(Timestamps):
    annoucement_type = (
        ("Journey", "Journey"),
        ("MicroSkill", "MicroSkill"),
        ("ProfileAssessment", "ProfileAssessment"),
        ("Survey", "Survey"),
        ("MentoringJournals", "MentoringJournals"),
        ("Advertisement", "Advertisement"),
        ("ProgramAnnouncement", "ProgramAnnouncement"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)  # company
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)  # channel
    skill_id = models.CharField(max_length=255, null=True, blank=True)
    channel_group = models.CharField(max_length=255, null=True, blank=True)
    topic = models.CharField(max_length=255, blank=True)
    cover_image = models.ImageField(upload_to='public_announcement/', null=True)
    topic_id = models.CharField(max_length=255, blank=True)
    summary = models.TextField()
    type = models.CharField(max_length=50, choices=annoucement_type, default="Journey")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    announce_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True)

    class Meta:
        ordering = ('-created_at',)

class CertificateTemplate(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    Certificate_for = models.CharField(max_length=50)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE) 
    file = models.ImageField(upload_to='Certificates/template/')
    user_name = models.CharField(max_length=50)
    user_name_coordinates = models.CharField(max_length=50)
    role = models.CharField(max_length=200)
    role_coordinates = models.CharField(max_length=50)
    journey_title = models.CharField(max_length=50)
    journey_coordinates = models.CharField(max_length=50)
    from_till_date = models.CharField(max_length=50)
    from_till_date_coordinates = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.title} - {self.journey.title}"

class CertificateSignature(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sign = models.ImageField(upload_to='Certificates/signature/')
    sign_coordinates = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    name_coordinates = models.CharField(max_length=50)
    headline = models.CharField(max_length=50)
    headline_coordinates = models.CharField(max_length=50)
    certificate_template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE)
    display_order = models.IntegerField(default=1)

    class Meta:
        ordering = ('-created_at',)

class UserCertificate(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE) 
    certificate_template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    file = models.ImageField(upload_to='Certificates/users/')
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.journey.title}"
