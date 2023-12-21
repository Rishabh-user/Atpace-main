from apps.test_series.models import TestOptions, TestQuestion
from rest_framework import serializers

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ['title', 'type', 'is_active', 'skill_level',
                  'is_required', 'correct_answer', 'display_order']

class AssessmentOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestOptions
        fields = ['options']
