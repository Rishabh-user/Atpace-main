from apps.atpace_community.models import SpaceGroups, Spaces
from apps.content.models import journeyContentSetup
from apps.leaderboard.models import BadgeDetails, PointsTable
from apps.utils.models import JourneyCategory
from rest_framework import serializers

class AutoApproveSerializer(serializers.Serializer):
    company_id = serializers.ListField()
    auto_approve = serializers.CharField(max_length=128)

class LiveStreamSerializer(serializers.Serializer):
    speaker_id = serializers.CharField(max_length=128)
    company_id = serializers.CharField(max_length=128)
    journey_id = serializers.CharField(max_length=128)
    space_name = serializers.CharField(max_length=128, required=False)
    custom_url = serializers.CharField(required=False)
    title = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=128)
    start_time = serializers.CharField(max_length=128)
    end_time = serializers.CharField(max_length=128)
    is_active = serializers.CharField(max_length=128)
    add_to_community = serializers.CharField(max_length=128)
    participants_list = serializers.ListField(required=False)

class ApproveRejectSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=128)
    channel_group_content_id = serializers.CharField(max_length=128)
    status = serializers.CharField(max_length=128)

class ProgramAnnouncementSerializer(serializers.Serializer):
    mentors = serializers.CharField(max_length=128)
    mentees = serializers.CharField(max_length=128)
    program_team = serializers.CharField(max_length=128)
    everyone = serializers.CharField(max_length=128)
    journey = serializers.CharField(max_length=128)
    company = serializers.CharField(max_length=128)
    topic = serializers.CharField(max_length=128)
    summary = serializers.CharField()
    attachment = serializers.ImageField()

class GroupChatSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=128)
    members = serializers.CharField(max_length=128)
    image = serializers.ImageField()

class AllotUserSerializer(serializers.Serializer):
    journey = serializers.CharField(max_length=128)
    user_list = serializers.CharField()
    is_wp_enable = serializers.CharField(max_length=128)

class QuestionSerializer(serializers.Serializer):
    mentor_ques_id = serializers.CharField(max_length=128)
    learner_ques_id = serializers.CharField(max_length=128)
    dependent_mentor_ques_id = serializers.CharField(max_length=128, allow_blank=True)
    dependent_learner_ques_id = serializers.CharField(max_length=128, allow_blank=True)
    dependent_option = serializers.CharField(max_length=128, allow_blank=True)
    question_type = serializers.CharField(max_length=128)
    is_dependent = serializers.CharField(max_length=128)

class MatchQuestionSerializer(serializers.Serializer):
    journey = serializers.CharField(max_length=128)
    company = serializers.CharField(max_length=128)
    match_question = QuestionSerializer(many=True)

class TagSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    is_active = serializers.CharField(max_length=128)
    color = serializers.CharField(max_length=128)

class IndustrySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    is_active = serializers.CharField(max_length=128)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyCategory
        fields = "__all__"

class CreateContentSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=128)
    image = serializers.ImageField()

class EditDraftSerializer(serializers.Serializer):
    content_id = serializers.CharField(max_length=128)
    data_id = serializers.CharField(max_length=128)
    title = serializers.CharField(max_length=128)
    data = serializers.CharField(max_length=128)
    image = serializers.ImageField()
    type = serializers.CharField(max_length=128)
    file = serializers.ImageField()
    option_list = serializers.JSONField()
    custom_answer = serializers.CharField(max_length=128)

class AddFieldSerializer(serializers.Serializer):
    content_id = serializers.CharField(max_length=128)
    type = serializers.CharField(max_length=128)

class CreateSurveySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    short_description = serializers.CharField()
    cover_image = serializers.ImageField()

class CreateAssessmentSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    short_description = serializers.CharField()
    cover_image = serializers.ImageField()
    autho_check = serializers.CharField(max_length=128)

class CreatePoolSerializer(serializers.Serializer):
    journey = serializers.CharField(max_length=128)
    company = serializers.CharField(max_length=128)
    # description = serializers.CharField(max_length=128)
    name = serializers.CharField(max_length=128)
    pool_by = serializers.CharField(max_length=128)
    tags = serializers.CharField(max_length=128)
    industry = serializers.CharField(max_length=128)
    is_active = serializers.CharField(max_length=128)

class AddMentorToPoolSerializer(serializers.Serializer):
    pool_id = serializers.CharField(max_length=128)
    user_id = serializers.CharField(max_length=128)

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spaces
        fields = ['title', 'description', 'space_group', 'space_type', 'cover_image', 'privacy', 'is_hidden', 'hidden_from_non_members', 'is_active']

class SpaceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceGroups
        fields = ['title', 'description', 'cover_image', 'privacy', 'is_hidden', 'hidden_from_non_members', 'is_active']

class JourneyContentCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = journeyContentSetup
        fields = ['journey', 'learn_label', 'overview', 'pdpa_label', 'pdpa_description']

class CapacityRatioSerializer(serializers.Serializer):
    subscription_id = serializers.CharField(max_length=128)
    company = serializers.CharField(max_length=128, required=False)
    journey = serializers.CharField(max_length=128, required=False)
    max_mentor = serializers.CharField(max_length=128)
    max_learner = serializers.CharField(max_length=128)
    learners_per_mentor = serializers.CharField(max_length=128)

class PointsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsTable
        fields = ['name', 'label', 'points', 'comment']

class BadgeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BadgeDetails
        fields = ['name', 'description', 'image', 'points_required', 'badge_for', 'is_active']

class MatchingSerializer(serializers.Serializer):
    company_id = serializers.CharField(max_length=128, allow_blank=True)
    journey_id = serializers.CharField(max_length=128)
    pool_id = serializers.CharField(max_length=128)

class AddMentorPoolSerializer(serializers.Serializer):
    pool_id = serializers.CharField()
    mentor_id = serializers.CharField()


class AssignMentorSerializer(serializers.Serializer):
    learner_id = serializers.CharField(max_length=128)
    mentor_id = serializers.CharField(max_length=128)
    journey_id = serializers.CharField(max_length=128)
    
class MatchingReportSerializer(serializers.Serializer):
    company_id = serializers.CharField(max_length=128)
    
class CancelSubscriptionSerializer(serializers.Serializer):
    company_id = serializers.CharField(max_length=128)
    user_subscription_id = serializers.CharField(max_length=128)
    is_cancel = serializers.CharField(max_length=128)


class MessageSchedulerSerializer(serializers.Serializer):
    company = serializers.CharField(max_length=128)
    scheduler_day = serializers.CharField(max_length=128)
    scheduler_time = serializers.TimeField()
    receiver = serializers.CharField(max_length=128)
    message = serializers.CharField()
    created_by = serializers.CharField(max_length=128)
    title = serializers.CharField(max_length=128)
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class GroupChatMemberSerializer(serializers.Serializer):
    group_id = serializers.CharField(max_length=128)
    member_id = serializers.CharField(max_length=128)

class AddGroupChatMemberSerializer(serializers.Serializer):
    group_id = serializers.CharField(max_length=128)
    member_id_list = serializers.ListField

class MentorApproveRejectSerializer(serializers.Serializer):
    mentor_id = serializers.CharField(max_length=128)
    status = serializers.CharField(max_length=128)
    
class ProgramManagerTaskSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=128)
    # task_type = serializers.CharField(max_length=128)
    # meta_key = serializers.CharField(max_length=128)
    # meta_value = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=100)
    is_recurring = serializers.BooleanField(default=False)
    recurring_time = serializers.CharField(max_length=128, required=False)
    set_remainder = serializers.BooleanField(default=False)
    reminder_before = serializers.IntegerField(required=False)
    start_time = serializers.DateTimeField()
    due_time = serializers.DateTimeField()
    company_id = serializers.CharField(max_length=100)
    timezone = serializers.CharField(max_length=100)


class AssignTaskSerializer(serializers.Serializer):
    assignee = serializers.CharField(max_length=128)
    task_id = serializers.CharField(max_length=128)
    is_assigned = serializers.BooleanField(default=False)


class RevokeTaskSerializer(serializers.Serializer):
    revoke_to = serializers.CharField(max_length=128)
    user_task_id = serializers.CharField(max_length=128)
    is_revoked = serializers.BooleanField(default=False)

class UpdateTaskStatusSerializer(serializers.Serializer):
    task_id = serializers.CharField(max_length=128)
    comment = serializers.CharField(max_length=256)
    task_status = serializers.CharField(max_length=128)
