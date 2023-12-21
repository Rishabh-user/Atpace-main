from rest_framework import serializers

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