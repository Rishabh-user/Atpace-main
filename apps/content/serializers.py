from apps.content.models import Channel
from rest_framework import serializers


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['pk', 'title', 'parent_id', 'is_active', 'company',
                  'is_test_required', 'is_community_required', 'is_delete', 'channel_admin']
