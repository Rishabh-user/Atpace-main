from numpy import require
from rest_framework import serializers
from apps.atpace_community.models import Attachments, Post, Report, SpaceGroups, SpaceMembers, Spaces, likes, Comment, Attachments, Event, SavedPost, UserPinnedPost, NotificationSettings, ContentToReview
from apps.atpace_community.utils import avatar, time_ago
from apps.push_notification.models import AtPaceNotification
from apps.users.models import User, Company
from apps.chat_app.models import Chat, Room


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


class SpaceSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(max_length=128)
    space_group_id = serializers.CharField(max_length=128)

    class Meta:
        model = Spaces
        fields = ['title', 'space_group_id', 'description', 'cover_image', 'privacy',
                  'space_type', 'is_hidden', 'hidden_from_non_members', 'is_active', 'user_id']


class SpaceGroupSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(max_length=128)

    class Meta:
        model = SpaceGroups
        fields = ['title', 'description', 'cover_image', 'privacy',
                  'is_hidden', 'hidden_from_non_members', 'is_active', 'user_id']


class SpaceMemberSerializer(serializers.Serializer):
    space_group_id = serializers.CharField(max_length=128)
    space_id = serializers.CharField(max_length=128)
    user_type = serializers.CharField(max_length=128)


class UploadMeidaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attachments
        fields = ['image_upload', 'file_upload']


class PostSerializer(serializers.ModelSerializer):
    media_upload = UploadMeidaSerializer(many=True, required=False)
    cover_image = serializers.ImageField(max_length=128, required=False)
    post_type = serializers.CharField(max_length=128, required=False)
    tags = serializers.CharField(max_length=128, required=False)
    Body = serializers.CharField()

    class Meta:
        model = Post
        fields = ['media_upload', 'title', 'Body', 'cover_image', 'post_type', 'tags',
                  'is_comments_enabled', 'is_liking_enabled', 'space_id', 'space_group_id', 'notify_space_members']


class EventSerializer(serializers.Serializer):
    media_upload = UploadMeidaSerializer(many=True, required=False)
    cover_image = serializers.ImageField(max_length=128, required=False)
    post_type = serializers.CharField(max_length=128)
    tags = serializers.CharField(max_length=128, required=False)
    title = serializers.CharField(max_length=128)
    Body = serializers.CharField()
    is_comments_enabled = serializers.BooleanField()
    livestream = serializers.BooleanField()
    is_liking_enabled = serializers.BooleanField()
    notify_space_members = serializers.BooleanField()
    space_group_id = serializers.CharField(max_length=128, required=False)
    space_id = serializers.CharField(max_length=128)
    # start_time = serializers.DateTimeField()
    # end_time = serializers.DateTimeField()
    location = serializers.CharField(max_length=128)
    attendees = serializers.ListField()
    speaker = serializers.CharField(max_length=128)
    frequency = serializers.CharField(max_length=128)
    event_url = serializers.URLField(allow_blank=True, required=False)
    bg_image = serializers.ImageField(required=False)


class CommentSerializer(serializers.Serializer):
    media_upload = UploadMeidaSerializer(many=True, required=False)
    body = serializers.CharField(required=True)
    post_id = serializers.CharField(max_length=128, required=True)
    cover_image = serializers.CharField(max_length=128, required=False)
    comment_for = serializers.CharField(max_length=128, required=False)
    parent_id = serializers.CharField(max_length=128, required=False)


class LikeSerializer(serializers.Serializer):
    post_id = serializers.CharField(max_length=128, required=False)
    comment_id = serializers.CharField(max_length=128, required=False)


class ReportSerializer(serializers.Serializer):
    class Meta:
        model = Report
        fields = ['comment', 'report_type', 'post_id']


class SavedPostSerializer(serializers.Serializer):
    post_id = serializers.CharField(max_length=128)


class InviteLinkSerializer(UserIdSerializer):
    email = serializers.EmailField(max_length=128)
    first_name = serializers.CharField(max_length=128)
    last_name = serializers.CharField(max_length=128)

class PinnedPostSerializer(serializers.Serializer):
    post_id = serializers.CharField(max_length=128)
    space_id = serializers.CharField(max_length=128, required=False)
    group_id = serializers.CharField(max_length=128, required=False)
    is_pinned = serializers.BooleanField()
    
class ApproveRejectContentSerializer(serializers.Serializer):
    review_content_id = serializers.CharField(max_length=128)
    post_on_community = serializers.BooleanField()

#data migrations serializers
class UsersSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "last_login", "is_superuser", "username", "first_name", "last_name", "is_staff", "is_active", "date_joined", "address", "state", "city", "country", "zip_code",
                    "latitude", "longitude", "profile_heading", "private_profile", "about_us", "phone", "gender", "age", "organization", "current_status", "position", "favourite_way_to_learn",
                    "interested_topic", "upscaling_reason", "time_spend", "prefer_not_say", "timespend", "email",
                    "is_whatsapp_enable", "is_term_and_conditions_apply", "is_phone_verified", "is_email_verified", "is_social_login", "facebook_account_id", "google_account_id", "social_login_type",
                    "pdpa_statement", "is_delete", "avatar", "is_archive", "referral_code", "user_status", "token", "is_lite_signup", "date_modified", "profile_assest_enable", "is_email_private",
                    "is_phone_private", "is_linkedin_private"]


class SpaceGroupsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SpaceGroups
        fields = "__all__"


class SpacesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Spaces
        fields = "__all__"

class SpaceMembersSerializer(serializers.ModelSerializer):

    class Meta:
        model = SpaceMembers
        fields = "__all__"

class PostsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = "__all__"

class CommentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = "__all__"

class LikessSerializer(serializers.ModelSerializer):

    class Meta:
        model = likes
        fields = "__all__"

class AttachmentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attachments
        fields = "__all__"

class EventsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Event
        fields = "__all__"

class NotificationSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotificationSettings
        fields = "__all__"

class ReportsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = "__all__"

class UserPinnedPostsSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserPinnedPost
        fields = "__all__"

class ContentToReviewsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContentToReview
        fields = "__all__"

class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = "__all__"

class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = "__all__"

class ChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        fields = "__all__"