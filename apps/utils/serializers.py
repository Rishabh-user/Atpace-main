from statistics import mode
from rest_framework import serializers
from .models import Industry, JourneyCategory


class CategorySerializers(serializers.ModelSerializer):
	class Meta:
		model= JourneyCategory
		fields = ['category', 'color', 'icon']


class IndustrySerializers(serializers.ModelSerializer):
	class Meta:
		model = Industry
		field = ['name']