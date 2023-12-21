from apps.survey_questions.models import Question
from rest_framework import serializers

class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['title', 'type', 'is_active', 'skill_level',
                  'is_required', 'correct_answer', 'display_order']

