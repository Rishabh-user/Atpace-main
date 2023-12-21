
from apps.mentor.models import DyteAuthToken
from django.db import transaction
from django.core.management.base import BaseCommand
from ravinsight.settings.base import  DYTE_BASE_URL, DYTE_API_KEY, DYTE_ORG_ID
import requests, json

# Initialize AWS SageMaker clients
class Command(BaseCommand):
    help = "Update default data"

    @transaction.atomic
    def handle(self, *args, **options):
        hosts = DyteAuthToken.objects.filter(preset='livestream_host')
        print(hosts.count(), "HOSTS Found")
        if hosts:
            for host in hosts:
                url = f"{DYTE_BASE_URL}/meetings/{str(host.meeting_id)}/participants"
                
                payload = json.dumps({
                            "name": host.user_name,
                            "custom_participant_id": host.email,
                            "preset_name": "group_call_host"
                        })
                print("INITIATING API CALL")
                response = requests.request("POST", url, data=payload, auth=(DYTE_ORG_ID, DYTE_API_KEY), headers={"Content-Type":"application/json"})
                print(f"Added {host.email} as GROUP CALL HOST")
                data = response.json()
                print("GOT THE DATA")
                host.preset = "group_call_host"
                host.authToken = data['data']['token']
                host.participant_id = data['data']['id']
                host.preset_id = data['data']['preset_id']
                host.save()
                print("Changed the DATA")

        viewers = DyteAuthToken.objects.filter(preset='livestream_viewer')
        if viewers:
            for viewer in viewers:
                url = f"{DYTE_BASE_URL}/meetings/{str(viewer.meeting_id)}/participants"
                payload = json.dumps({
                            "name": viewer.user_name,
                            "custom_participant_id": viewer.email,
                            "preset_name": "group_call_participant"
                        })
                response = requests.request("POST", url, data=payload, auth=(DYTE_ORG_ID, DYTE_API_KEY), headers={"Content-Type": "application/json"})
                data = response.json()
                viewer.preset = "group_call_participant"
                viewer.authToken = data['data']['token']
                viewer.participant_id = data['data']['id']
                viewer.preset_id = data['data']['preset_id']
                viewer.save()