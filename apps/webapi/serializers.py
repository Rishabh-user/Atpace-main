from rest_framework import serializers
from apps.users.models import User



class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'phone', 'is_active', 'id']


