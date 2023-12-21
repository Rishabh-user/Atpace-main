from urllib import response
import pytz
from datetime import datetime, date
from rest_framework import serializers
from apps.atpace_community.utils import avatar
# from .views.leaderboard import DeleteUserGoal
from apps.users.models import ContactProgramTeamImages, ProfileAssestQuestion, User, UserProfileAssest, UserTypes
from apps.test_series.models import TestSeries
from apps.mentor.models import BookmarkMentor, mentorCalendar
from apps.content.models import Channel, UserChannel
from apps.users.utils import applyCouponCode


# from .models import PhoneVerifier

utc = pytz.UTC


class UserIdSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=128)
    user = None

    def validate(self, data):
        try:
            user = User.objects.get(pk=data['user_id'])
        except User.DoesNotExist:
            # data = {
            #     "message": "User not Found",
            #     "success": False
            # }
            print(data)
            raise serializers.ValidationError("Invalid User")
        return data


class UnlockJourneySerializer(UserIdSerializer):
    journey_id = serializers.CharField(max_length=128)


class AssessmentAttemptSerializer(UserIdSerializer):
    attempt_id = serializers.CharField(max_length=128)


class UserTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTypes
        fields = ['type']


class CreateUserSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(max_length=255, required=False)
    password = serializers.CharField(max_length=255, required=False)
    userType = UserTypesSerializer(read_only=True)

    class Meta:
        fields = ('username',)
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'coupon_code', "password", 'userType']
        # extra_kwargs = {
        #     'password': {'write_only': True}
        # }

    def get_coupon_code(self, instance):
        return instance.coupon_code or ''

    def create(self, validated_data):
        user = User.objects.create_user(first_name=validated_data['first_name'], last_name=validated_data['last_name'], username=validated_data['username'],
                                        email=validated_data['email'], phone=validated_data['phone'])
        if validated_data.get('password'):
            user.set_password(validated_data['password'])
        user.save()
        if user.coupon_code != "":
            applyCouponCode(user, user.coupon_code)
        return user


class FirebaseTokenSerializer(serializers.Serializer):
    firebase_token = serializers.CharField(max_length=256, required=False, allow_blank=True)
    device_id = serializers.CharField(max_length=128, required=False, allow_blank=True)


class LoginSerializer(FirebaseTokenSerializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class GetUserCompanySerializer(serializers.Serializer):
    data = serializers.CharField(max_length=255)


class ConfirmPasswordSerializer(UserIdSerializer):
    new_password = serializers.CharField(max_length=128)
    confirm_password = serializers.CharField(max_length=128)

    def create(self, validate_data):
        user = User.objects.get(pk=validate_data.get('user_id'))
        print("user S Line 48: ", user)
        new_password = validate_data.get('new_password')
        confirm_password = validate_data.get('confirm_password')

        if new_password == confirm_password:
            user.set_password(new_password)
            user.save()
            return user
        else:
            raise serializers.ValidationError({
                'error': 'password does not match'
            })


class PasswordChangeSerializer(UserIdSerializer):
    password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128)
    confirm_password = serializers.CharField(max_length=128)

    def create(self, validate_data):
        user = User.objects.get(pk=validate_data.get('user_id'))
        password = validate_data.get('password')
        new_password = validate_data.get('new_password')
        confirm_password = validate_data.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError({
                'error': 'password does not match'
            })
        user = user.set_password(new_password)
        user.save()
        return user


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ["id", "title", "description", "channel_type", "channel_admin"]


class BrowseChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserChannel
        fields = "__all__"


class LoginWithOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=128)

    class Meta:
        model = User
        fields = ['phone']


class VerifyOtpSerializer(FirebaseTokenSerializer):
    phone = serializers.CharField(max_length=128, required=False)
    email = serializers.EmailField(required=False)
    type = serializers.CharField(max_length=128, required=False)
    otp = serializers.CharField(max_length=128)


class ReferalSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=128)
    referal_code = serializers.CharField(max_length=128)


class AssessmentSerializer(serializers.Serializer):
    assessment_id = serializers.CharField(max_length=128)
    journey_type = serializers.CharField(max_length=128)


class SurveySerializer(serializers.Serializer):
    survey_id = serializers.CharField(max_length=128)
    journey_type = serializers.CharField(max_length=128)


class CategoryJourneySerializer(serializers.Serializer):
    category = serializers.CharField(max_length=128)
    user_id = serializers.CharField(max_length=128)
    company_id = serializers.CharField(max_length=128)


class AssessmentDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSeries
        fields = "__all__"


class LoginWithEmailOrOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=128)
    user_type = serializers.CharField(max_length=128, required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=True)


class ProfileAssestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAssestQuestion
        fields = "__all__"


class UserProfileAssestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileAssest
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    about_us = serializers.CharField()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'age', 'prefer_not_say', 'about_us', 'profile_heading', 'userType', 'private_profile', "avatar",
                  'organization', 'current_status', 'position', 'expertize', 'industry', 'linkedin_profile', "favourite_way_to_learn", "interested_topic", "upscaling_reason", "time_spend", "is_email_private", "is_phone_private", "is_linkedin_private"]
        read_only_fields = ('id', 'email', 'phone', 'username')

    userType = serializers.SerializerMethodField('obj_user_type')
    industry = serializers.SerializerMethodField('obj_industry')
    expertize = serializers.SerializerMethodField('obj_expertize')
    avatar = serializers.SerializerMethodField('obj_avatar')

    def obj_user_type(self, obj):
        return ",".join(str(type.type) for type in obj.userType.all())

    def obj_industry(self, obj):
        return [industry.name for industry in obj.industry.all()]

    def obj_expertize(self, obj):
        return [expertize.name for expertize in obj.expertize.all()]

    def obj_avatar(self, obj):
        return avatar(obj)


class JourneyAssesmentResponseSerializer(serializers.Serializer):
    assessment_id = serializers.CharField(max_length=128)
    journey_type = serializers.CharField(max_length=128)
    journey_id = serializers.CharField(max_length=128)
    questions = serializers.ListField()


class JourneySurveuResponseSerializer(serializers.Serializer):
    survey_id = serializers.CharField(max_length=128)
    journey_type = serializers.CharField(max_length=128)
    journey_id = serializers.CharField(max_length=128)
    questions = serializers.ListField()


class QuestContentSerializer(UserIdSerializer):
    quest_id = serializers.CharField(max_length=128)
    journey_group = serializers.CharField(max_length=128)


class UpdateJournalSerializer(UserIdSerializer):
    id = serializers.IntegerField()
    quest_id = serializers.CharField(max_length=128)
    journey_id = serializers.CharField(max_length=128)
    learning_journal = serializers.CharField()
    type = serializers.CharField(max_length=20, required=True)
    is_draft = serializers.BooleanField()
    is_private = serializers.BooleanField()


class MentorCalendarSerializer(serializers.ModelSerializer):

    feedback_type = serializers.CharField(max_length=128, default='MentorCall')
    class Meta:
        model = mentorCalendar
        fields = ['id', 'title', 'description', 'start_time', 'end_time', 'url', 'reminder', 'is_cancel',
                  'call_type', 'slot_status', 'status', 'bookmark', 'created_at', 'mentor', 'mentor_name', 'mentor_avatar', 'feedback_type']

    status = serializers.SerializerMethodField('obj_status')
    mentor_name = serializers.SerializerMethodField('get_mentor_name')
    mentor_avatar = serializers.SerializerMethodField('get_mentor_avator')

    def obj_status(self, obj):
        # current_time = utc.localize(datetime.now())
        current_time = utc.localize(datetime.combine(date.today(), datetime.min.time()))
        print("Objeci is canceleed", obj.is_cancel)
        print("Objeci status", obj.slot_status)
        print("Objeci status", obj.start_time, "\n")
        if obj.is_cancel and obj.slot_status == "Booked":
            return "Cancelled"
        elif (not obj.is_cancel and obj.slot_status == "Booked") and (obj.start_time >= current_time):
            return "Upcoming"
        elif (not obj.is_cancel and obj.slot_status == "Booked") and (obj.start_time < current_time):
            return "Completed"
        elif obj.slot_status == "Available":
            return ""

    def get_mentor_name(self, obj):
        return f'{obj.mentor.first_name} {obj.mentor.last_name}'

    def get_mentor_avator(self, obj):
        return obj.mentor.avatar.url


class ContentQuizAsnwerSerializer(UserIdSerializer):
    id = serializers.CharField(max_length=128)
    option_id = serializers.IntegerField()
    option = serializers.CharField(max_length=128)
    journey_id = serializers.CharField(max_length=128)
    quest_id = serializers.CharField(max_length=128)


class addFavouriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookmarkMentor
        fields = "__all__"


class BookAppoinmentSerializer(UserIdSerializer):
    mentor_id = serializers.CharField(max_length=128)
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()
    title = serializers.CharField(max_length=200)


class CancelAppoinmentSerializer(UserIdSerializer):
    mentor_id = serializers.CharField(max_length=128)
    id = serializers.CharField(max_length=128)
    title = serializers.CharField(max_length=200)
    timezone = serializers.CharField(max_length=128)


class AvatarUpdateSerializer(UserIdSerializer):
    avatar = serializers.ImageField()

    def create(self, validate_data):
        user = User.objects.filter(id=validate_data.get('user_id'))
        print("user S Line 234: ", user)
        avatar = validate_data.get('avatar')
        user.save()
        return user


class AskQuestionSerializer(UserIdSerializer):
    journey_id = serializers.CharField(max_length=128)
    quest_id = serializers.CharField(max_length=128)
    title = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=128)
    type = serializers.CharField(max_length=128)


class PostCommentSerializer(UserIdSerializer):
    journey_id = serializers.CharField(max_length=128)
    post_id = serializers.CharField(max_length=128)
    answer = serializers.CharField(max_length=128)


class AvailableSlotSerializer(UserIdSerializer):
    mentor_id = serializers.CharField(max_length=128, required=False)
    date = serializers.DateField(required=False)
    company_id = serializers.CharField(max_length=128)



class UploadImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactProgramTeamImages
        fields = ['image']


class ContacProgramTeamsSerializer(UserIdSerializer):
    subject = serializers.CharField(max_length=128)
    issue = serializers.CharField(max_length=128)
    image = UploadImageSerializer(many=True)


class MentorsScheduedSessionSerializer(UserIdSerializer):
    mentor_id = serializers.CharField(max_length=128)
    company_id = serializers.CharField(max_length=128)
    today = serializers.CharField(max_length=128, required=False)


class ChatMessageSerializer(UserIdSerializer):
    mentor_id = serializers.CharField(max_length=128, required=False)
    room_name = serializers.CharField(max_length=128)


class AddEventSerializer(serializers.Serializer):
    mentor_id = serializers.CharField(max_length=128)
    journey_id = serializers.CharField(max_length=128)
    title = serializers.CharField(max_length=128)
    start_time = serializers.CharField(max_length=128)
    end_time = serializers.CharField(max_length=128)


class UpdateEventSerializer(serializers.Serializer):
    mentorcal_id = serializers.CharField(max_length=128)
    mentor_id = serializers.CharField(max_length=128)
    title = serializers.CharField(max_length=128)
    start_time = serializers.CharField(max_length=128)
    end_time = serializers.CharField(max_length=128)


class LearningJournalPostCommentSerializer(serializers.Serializer):
    learningjournal_id = serializers.CharField(max_length=128)
    answer = serializers.CharField(max_length=128)
    mentor_id = serializers.CharField(max_length=128)


class UploadFileSerializer(serializers.Serializer):
    upload_file = serializers.FileField()


class DeleteEventSerializer(serializers.Serializer):
    mentorcal_id = serializers.CharField(max_length=128)
    mentor_id = serializers.CharField(max_length=128)


class DashboardSerializer(UserIdSerializer):
    user_type = serializers.CharField(max_length=128)
    company_id = serializers.CharField(max_length=128)


class UserGoalsSerializer(serializers.Serializer):
    heading = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=128)
    duration_number = serializers.CharField(max_length=128)
    duration_time = serializers.CharField(max_length=128)
    category = serializers.CharField(max_length=128)
    priority_level = serializers.CharField(max_length=128)
    frequency = serializers.CharField(max_length=128)


class UserGoalprogressSerializer(serializers.Serializer):
    goal_id = serializers.CharField(max_length=128)
    status = serializers.CharField(max_length=128)


class CreateChatGroupSerializer(UserIdSerializer):
    room_name = serializers.CharField(max_length=128, required=False)
    group_name = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=128)
    group_avatar = serializers.ImageField(required=False)
    members = serializers.ListField()
    user_type = serializers.CharField(max_length=128)


class RemoveGroupMembersSerializer(UserIdSerializer):
    user_type = serializers.CharField(max_length=128)
    room_name = serializers.CharField(max_length=128)
    members = serializers.ListField()


class CreateJournalSerializer(UserIdSerializer):
    title = serializers.CharField(max_length=128)
    body = serializers.CharField(max_length=128)


class EditJournalSerializer(UserIdSerializer):
    id = serializers.CharField(max_length=128)
    body = serializers.CharField(max_length=128)


class EditJournalCommentSerializer(UserIdSerializer):
    id = serializers.CharField(max_length=128)
    body = serializers.CharField(max_length=128)


class SubmitProfileAssessmentSerilizer(UserIdSerializer):
    assessment = serializers.ListField()


class SocialLoginSerializer(serializers.ModelSerializer):
    signup = serializers.BooleanField()
    facebook_account_id = serializers.CharField(max_length=128, allow_blank=True, required=False)
    google_account_id = serializers.CharField(max_length=128, allow_blank=True, required=False)
    coupon_code = serializers.CharField(max_length=128, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'facebook_account_id',
                  'google_account_id', 'social_login_type', 'coupon_code', 'signup']


class TranslateDataSerializer(serializers.Serializer):
    from_lang = serializers.CharField(max_length=128, allow_blank=True, required=False)
    to_lang = serializers.CharField(max_length=128)
    text = serializers.ListField()


class AssignSurveyListSerializer(UserIdSerializer):
    company_id = serializers.CharField(max_length=128)
    user_type = serializers.CharField(max_length=128)
    
class MobileLogsSerializer(serializers.Serializer):
    data = serializers.CharField()
    
class FeedbackTemplateSerializer(serializers.Serializer):
    name = serializers.CharField()
    cover_image = serializers.ImageField()
    journey = serializers.CharField(allow_blank=True, required=False)
    short_description = serializers.CharField()
    template_for = serializers.CharField()
    is_draft = serializers.CharField()
    is_active = serializers.CharField()

class CompanyJourneySerializer(serializers.Serializer):
    company_id = serializers.CharField()


class FeedbackResponseSerializer(UserIdSerializer):
    feedback_id = serializers.CharField(max_length=128)
    feedback_for = serializers.CharField(max_length=128)
    feedback_for_id = serializers.CharField(max_length=128)
    is_private = serializers.BooleanField()
    is_name_private = serializers.BooleanField()
    questions = serializers.ListField()
    
class ValidationSerializer(serializers.Serializer):
    value = serializers.CharField(max_length=128, allow_blank=True, required=False)
    coupon_code = serializers.CharField(max_length=128, allow_blank=True, required=False)

class CheckLiteSignupUserSerializer(serializers.Serializer):
    email = serializers.CharField()
    phone = serializers.CharField()
    journey_id = serializers.CharField()

class UserEnrollCheckSerializer(serializers.Serializer):
    email = serializers.CharField()
    type = serializers.CharField()
    journey_id = serializers.CharField()

class AssesmentQuestionSerializer(serializers.Serializer):
    type = serializers.CharField()
    journey_id = serializers.CharField()
class UpdateEmailSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    email = serializers.EmailField(max_length=128)

class VerifyEmailOtpSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    otp = serializers.CharField(max_length=128)


class GetRSVPResponseSerializer(serializers.Serializer):
    meet_id = serializers.CharField(max_length=20)
    meet_type = serializers.CharField(max_length=10)
    user_id = serializers.CharField(max_length=20)
    response = serializers.CharField(max_length=10)
    notification_id = serializers.CharField(max_length=128, required=False)
