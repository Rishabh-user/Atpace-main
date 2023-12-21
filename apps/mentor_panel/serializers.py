from rest_framework import serializers


class PostAdvanceProfileSerilizer(serializers.Serializer):
    mentoring_style = serializers.CharField()
    mentoring_types = serializers.CharField()
    target_audience = serializers.CharField()
    languages = serializers.CharField()
    total_experience = serializers.CharField(required=False, allow_blank=True)
    contact_preferences = serializers.CharField()
    partner_badge = serializers.CharField(max_length=128)
    keep_contact_details_private = serializers.BooleanField()
    linkedin_profile = serializers.CharField(max_length=256, allow_blank=True)
    facebook_profile = serializers.CharField(max_length=256, allow_blank=True)
    instagram_profile = serializers.CharField(max_length=256, allow_blank=True)
    twitter_profile = serializers.CharField(max_length=256, allow_blank=True)
    publish_to_marketplace = serializers.BooleanField()
    private_profile = serializers.BooleanField()


class WorkExperienceSerializers(serializers.Serializer):
    company = serializers.CharField(max_length=128)
    designation = serializers.CharField(max_length=128)
    start_date = serializers.DateField()
    currently_working = serializers.BooleanField()
    end_date = serializers.DateField(required=False, allow_null=True)
    location = serializers.CharField(max_length=128)
    location_type = serializers.CharField(max_length=128)
    employment_type = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True)


class MentorCertificateSerializers(serializers.Serializer):
    title = serializers.CharField(max_length=128)
    certificate = serializers.FileField()
    generated_date = serializers.DateField()
    is_expiration_date = serializers.BooleanField()
    valid_upto = serializers.DateField(required=False, allow_null=True)
    certification_level = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False)

class MentorEducationSerializer(serializers.Serializer):
    program = serializers.CharField(max_length=50)
    major = serializers.CharField(max_length=30)
    university = serializers.CharField(max_length=50)
    location = serializers.CharField(max_length=30)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    is_ongoing = serializers.BooleanField()
    excellence = serializers.CharField(max_length=30, required=False)
    description = serializers.CharField(max_length=100, required=False)

class EmailForInvitingSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=128)
    mentor_id = serializers.CharField(max_length=128)
    
class PublishOnMarketPlaceSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=128)
    mentor_id = serializers.CharField(max_length=128)
    is_publish = serializers.BooleanField(default=False)