from django.core.management.base import BaseCommand
from apps.users.models import Collabarate, User
from apps.mentor.models import DyteAuthToken
import json
from rest_framework import serializers

class Command(BaseCommand):
    help = "Update default data"
    
    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ["id", "username"]

    class DyteAuthTokenSerializer(serializers.ModelSerializer):
        class Meta:
            model = DyteAuthToken
            fields = "__all__"

    def handle(self, **options):
        collaborate = Collabarate.objects.all()
        dyte_auth_token = DyteAuthToken.objects.all()
        # call_data = self.CollaborateSerializer(collaborate, many=True).data
        call_data = [{
            "id": str(call.id),
            "title": call.title,
            "url_title": str(call.url_title),
            "journey": str(call.journey),
            "company": str(call.company.id) if call.company else call.company,
            "description": call.description,
            "custom_url": call.custom_url,
            "speaker": str(call.speaker.id),
            "start_time": str(call.start_time),
            "end_time": str(call.end_time),
            "type": call.type,
            "token": str(call.token)
        }
            for call in collaborate
        ]
        auth_token_data = self.DyteAuthTokenSerializer(dyte_auth_token, many=True).data
        call_json_object = json.dumps(call_data, indent=4)
        auth_json_object = json.dumps(auth_token_data, indent=4)
        with open("call.json", "w+") as file:
            file.write(auth_json_object)
        self.stdout.write(self.style.SUCCESS("All call Updated!"))

        with open("auth_token.json", "w+") as file:
            file.write(call_json_object)
        self.stdout.write(self.style.SUCCESS("All auth_token Updated!"))