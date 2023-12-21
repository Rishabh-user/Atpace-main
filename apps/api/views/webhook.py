from django.contrib import messages
from django.shortcuts import redirect, render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.vonage_api.models import VonageWhatsappReport
from apps.vonage_api.utils import status_update, update_message_status, create_message_reply, send_message
from ravinsight.web_constant import BASE_URL
from rest_framework import status
from apps.mentor.models import AllMeetingDetails, MeetingParticipants
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.mentor.models import DyteMeetDetails

class vonage_inbond(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        print(request.data)
        data = request.data
        if "button" in data or "text" in data:
            create_message_reply(data)
        else:
            to_user = data['to']
            from_user = data['from']
            
            send_message(from_user, to_user)
        response = {
            "message":"success"
        }
        return Response(response)

class vonage_status(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        print(request.data)
        status_update(request.data)
        update_message_status(request.data)
        response = {
            'message':"success"
        }
        return Response(response)


class DyteWebhook(APIView):
    permission_classes = [AllowAny]
    @csrf_exempt
    def post(self, request):
        # print("WEBHOOK data", request.data)
        data = request.data
        event = data['event']

        meet_id = data['meeting']['id']
        sessionId = data['meeting']['sessionId']
        meet_title = data['meeting']['title']
        roomName = data['meeting']['roomName']
        meet_status = data['meeting']['status']
        meet_created_at = data['meeting']['createdAt']
        meet_started_at = data['meeting']['startedAt']
        organizer_id = data['meeting']['organizedBy']['id']
        organizer_name = data['meeting']['organizedBy']['name']

        peer_id = data['participant']['peerId']
        user_name = data['participant']['userDisplayName']
        user_custom_id = data['participant']['customParticipantId']
        client_specific_id = data['participant']['clientSpecificId']
        joinedAt = data['participant']['leftAt']
        leftAt = data['participant']['joinedAt']

        DyteMeetDetails.objects.create(
            event=event, meet_id=meet_id, session_id=sessionId, meet_title=meet_title,
            roomName=roomName, meet_status=meet_status, meet_created_at=meet_created_at, 
            meet_started_at=meet_started_at, organizer_id=organizer_id, organizer_name=organizer_name,
            peer_id=peer_id, user_name=user_name, user_custom_id=user_custom_id,
            client_specific_id=client_specific_id, left_at=leftAt, joined_at=joinedAt )
        print("meet details saved")
        return Response({"message":"success"}, status.HTTP_200_OK)
    
# dyte_redirect_webhook_function = csrf_exempt(dyte_redirect_webhook.as_view())    
def app_redirect_url(request):
    messages.error(request, "Please use mobie to open the application")
    return redirect(f"{BASE_URL}/login/")
