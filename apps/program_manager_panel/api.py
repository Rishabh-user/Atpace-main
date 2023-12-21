from tokenize import group
from apps.api.serializers import UserIdSerializer
from apps.atpace_community.models import Post, SpaceGroups, Spaces
from apps.content.utils import change_course_status_in_group, company_journeys, generate_certificate
from apps.leaderboard.views import NotificationAndPoints, send_push_notification 
from apps.payment_gateway.models import Transaction
from apps.program_manager_panel.models import MentorMenteeRatio, Subscription, SubcribedUser, SubscriptionOffer, \
    MessageScheduler, ProgramManagerTask, TaskRemainder, AssignTaskToUser
from apps.survey_questions.models import Survey, SurveyAttempt
from apps.test_series.models import TestSeries
from apps.utils.models import Industry, JourneyCategory, Tags
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
import random, requests, os
from apps.mentor_panel.models import *
from django.db.models.query_utils import Q
from apps.chat_app.models import Chat, Room as AllRooms
from apps.users.templatetags.tags import get_chat_room
from datetime import timedelta, datetime, date, timezone
from apps.api.utils import check_valid_user, meeting_notification, room_members, update_boolean
from apps.content.models import Channel, ChannelGroup, ChannelGroupContent, Content, ContentData, ContentDataOptions, MatchQuesConfig, MatchQuestion, MentoringJourney, ProgramTeamAnnouncement, SurveyAttemptChannel, UserChannel, journeyContentSetup, ContentChannels, SkillConfig, ChannelGroup
from apps.atpace_community.utils import aware_time, cover_images, response_post, add_member_to_space, add_to_community_event, avatar, group_avatar, broadcast_attachment, certificate_file
from apps.leaderboard.models import AutoApproveGoal, BadgeDetails, PointsTable
from apps.mentor.models import AllMeetingDetails, AssignMentorToUser, MeetingParticipants, Pool, PoolMentor
from apps.program_manager_panel.serializers import AddFieldSerializer, AssignMentorSerializer, AddMentorPoolSerializer, AllotUserSerializer, ApproveRejectSerializer, \
    AutoApproveSerializer, MatchingReportSerializer, MatchingSerializer, BadgeCreateSerializer, CapacityRatioSerializer, CategorySerializer, CreateAssessmentSerializer, \
    CreateContentSerializer, CreatePoolSerializer, CreateSurveySerializer, EditDraftSerializer, GroupChatSerializer, IndustrySerializer, JourneyContentCreationSerializer, \
    LiveStreamSerializer, MatchQuestionSerializer, PointsCreateSerializer, ProgramAnnouncementSerializer, SpaceGroupSerializer, SpaceSerializer, TagSerializer, \
    CancelSubscriptionSerializer, MessageSchedulerSerializer, GroupChatMemberSerializer, AddGroupChatMemberSerializer, MentorApproveRejectSerializer, ProgramManagerTaskSerializer, \
    AssignTaskSerializer, RevokeTaskSerializer, UpdateTaskStatusSerializer
from apps.program_manager_panel.utils import error_message, obj_image, journey_params, obj_image, program_manager_journey_list
from apps.users.utils import lives_streaming_room, matching_mentor_1, menter_mentee_capacity, local_time, matching_mentor, meeting, minutes, send_certificate_email_by_manager, program_announcement_email, registration_list, strf_format, unixTimstamp, convert_to_local_time, convert_to_utc
from apps.users.views import MatchingQuestion, check_check_box
from apps.vonage_api.utils import journey_enrolment, live_stream_event, program_team_broadcast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ravinsight import settings
from apps.users.models import Collabarate, Company, Learner, Mentor, ProfileAssestQuestion, User, ContactProgramTeam, ContactProgramTeamImages, UserTypes
from apps.users.helper import add_user_to_company, user_company
from apps.community.models import LearningJournals
from ravinsight.web_constant import BASE_URL, SITE_NAME, DOMAIN, LOGIN_URL, INFO_CONTACT_EMAIL
from notifications.signals import notify
from django.http import HttpResponse
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from apps.leaderboard.views import CheckEndOfJourney
from apps.content.models import UserCertificate, CertificateTemplate

class IssuesRaised(APIView):

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        company = user.company.all()
        #print(company)
        if company_id := self.request.query_params.get('company_id'):
            company = company.filter(pk=company_id)
        data = ContactProgramTeam.objects.filter(company__in=company)
        ProgramTeam = []
        for obj in data:
            image = ContactProgramTeamImages.objects.filter(contact_program=obj).first()
            #print(image)
            ProgramTeam.append({
                "id": obj.id,
                "name": f"{obj.user.first_name} {obj.user.last_name}",
                "subject": obj.subject,
                "issue": obj.issue,
                "company": obj.company.name,
                "image": obj_image(image) if image else '',
                "created_at": strf_format(local_time(obj.created_at))
            })

        response = {
            "message": "All Issues Raised",
            "success": True,
            "data": {
                "issues_raised": ProgramTeam,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class ProgramUserRegistrationList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        #print(user)
        journey_id = self.request.query_params.get('journey_id') or None
        user_name = self.request.query_params.get('user_name') or None
        assessment = self.request.query_params.get('assessment') or None
        company_id = self.request.session['company_id']
        if not self.request.query_params.get('timezone'):
            return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        timezone = self.request.query_params.get('timezone')
        response = registration_list(user=user, filter_user=user_name,
                                     filter_assessment=assessment, filter_journey=journey_params(journey_id), company_id=company_id, offset=timezone)
        return Response(response, status=status.HTTP_200_OK)


class MyJourneyList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        journeys = program_manager_journey_list(user, company_id=self.request.session['company_id'])
        journey_list = []
        for journey in journeys:
            journey_list.append({
                "journey_id": journey.id,
                "name": journey.title,
                "category": journey.category.category if journey.category else "",
                "short_description": journey.short_description,
                "description": journey.description,
                "image": obj_image(journey),
                "company": journey.company.name,
                "channel_type": journey.channel_type,
            })
        response = {
            "message": "My Journey List",
            "success": True,
            "data": journey_list
        }
        return Response(response, status=status.HTTP_200_OK)


class GoalSetting(APIView):

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company_list = []
        userCompany = user_company(user, self.request.session.get('company_id'))
        for company in userCompany:
            auto_approve = AutoApproveGoal.objects.filter(company=company).first()
            is_approve = False
            if auto_approve:
                is_approve = auto_approve.is_auto_approve
            company_list.append({
                "id": auto_approve.id if auto_approve else '',
                "company_id": company.pk,
                "company_name": company.name,
                "is_approve": is_approve,
                "created_at": strf_format(local_time(auto_approve.created_at)) if auto_approve else ''
            })

        response = {
            "message": "Auto Approve Company List",
            "success": True,
            "company_list": company_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = AutoApproveSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            companys = request.data['company_id']
            auto_approve = update_boolean(request.data['auto_approve'])
            companys = companys.split(",")
            for company_id in companys:
                company = Company.objects.get(pk=company_id)
                if not AutoApproveGoal.objects.filter(company=company).exists():
                    AutoApproveGoal.objects.create(company=company, is_auto_approve=auto_approve, created_by=user)
                else:
                    AutoApproveGoal.objects.filter(company=company).update(
                        is_auto_approve=auto_approve, updated_by=user)

            response = {
                "message": "Auto approve list created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class PendingContent(APIView):

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        all_journeys = Channel.objects.filter(company__in=company, is_active=True,
                                              is_delete=False, closure_date__gt=datetime.now())
        if journey_id := self.request.query_params.get('journey_id'):
            all_journeys = all_journeys.filter(pk=journey_id, parent_id=None)
        channel_group = ChannelGroup.objects.filter(channel__in=all_journeys, is_delete=False)
        channel_group_content = ChannelGroupContent.objects.filter(status="Pending",
                                                                   channel_group__in=channel_group, is_delete=False).order_by('-created_at')
        content_list = []
        for channel_group_content in channel_group_content:
            content_list.append({
                "user_id": user.id,
                "user_name": f"{user.first_name} {user.last_name}",
                "id": channel_group_content.pk,
                "content_id": channel_group_content.content.pk,
                "content_title": channel_group_content.content.title,
                "content_image": obj_image(channel_group_content.content),
                "content_description": channel_group_content.content.description,
                "status": channel_group_content.content.status,
                "channel_group_id": channel_group_content.channel_group.pk,
                "channel_grouptitle": channel_group_content.channel_group.title,
                "channel_id": channel_group_content.channel_group.channel.pk,
                "channel_title": channel_group_content.channel_group.channel.title,
                "created_at": strf_format(local_time(channel_group_content.created_at)),
                "updated_at": strf_format(local_time(channel_group_content.updated_at)),
            })
        response = {
            "message": "Auto approve list created",
            "success": True,
            "data": content_list
        }
        return Response(response, status=status.HTTP_201_CREATED)


class ContentApproveReject(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = ApproveRejectSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(request.data['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            course_status = request.data['status']
            channel_group = ChannelGroupContent.objects.filter(
                pk=request.data['channel_group_content_id'], is_delete=False)
            if not channel_group:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            if course_status == "Approve":
                channel_group.update(status="Live")
                channel_group = channel_group.first()
                Content.objects.filter(pk=channel_group.content.pk).update(status="Live")
                message = "Content Approved"
            else:
                channel_group.update(status="Reject")
                message = "Content Rejected"

            response = {
                "message": message,
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class StreamList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if 'timezone' in request.session:
            time_zone = self.request.session['timezone']
        elif 'timezone' in self.request.query_params:
            time_zone = self.request.query_params.get('timezone')
        else:
            return Response({"message": "Please specify timezone", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        if call_type := self.request.query_params.get('call_type'):
            userCompany = user_company(user, self.request.session.get('company_id'))
            channel = Channel.objects.filter(company__in=userCompany, closure_date__gt=datetime.now())
            #print(f"channel {channel}")
            channel_ids = [journey.id for journey in channel]
            collaborates = Collabarate.objects.filter(is_active=True, is_cancel=False, type=call_type, company__in=userCompany)
            if call_type == "LiveStreaming":
                collaborates = collaborates.filter(journey__in=channel_ids)
        else:
            return Response({"message": "Please specify call type", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        data = []
        participant_list = []
        journey = None
        for collaborate in collaborates:
            if call_type == "GroupStreaming":
                participant_list = [{"id": participant.id, "name": f"{participant.first_name} {participant.last_name}",
                                     "email": participant.email, "profile_image": avatar(participant)} for participant in collaborate.participants.all()]
            if collaborate.journey:
                journey = channel.filter(Q(title__icontains=collaborate.journey) | Q(pk=collaborate.journey),
                                         parent_id=None, is_active=True, is_delete=False).first()
            # if collaborate.company:
            #     company = Company.objects.get(id=collaborate.company.pk)
            data.append({

                "id": collaborate.id,
                "title": collaborate.title,
                "journey_id": journey.pk if journey else '',
                "journey": journey.title if journey else '',
                "company_id": collaborate.company.id if collaborate.company else '',
                "company_name": collaborate.company.name if collaborate.company else '',
                "description": collaborate.description,
                "custom_url": collaborate.custom_url,
                "speaker_name": f"{collaborate.speaker.first_name} {collaborate.speaker.last_name}",
                "start_time": strf_format(convert_to_local_time(collaborate.start_time, time_zone)),
                "end_time": strf_format(convert_to_local_time(collaborate.end_time, time_zone)),
                "type": collaborate.type,
                "is_active": collaborate.is_active,
                "is_cancel": collaborate.is_cancel,
                "add_to_community": collaborate.add_to_community,
                "space_name": collaborate.space_name,
                "participant_list": participant_list,
                "cancel_by": f"{collaborate.cancel_by.first_name} {collaborate.cancel_by.last_name}" if collaborate.cancel_by else '',
                "created_at": strf_format(convert_to_local_time(collaborate.created_at, time_zone)),
            })
        response = {
            "message": "Call created",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = LiveStreamSerializer(data=request.data)
        if serializer.is_valid():
            call_type = self.request.query_params.get('call_type') or None
            journey_id = data.get('journey_id') or None
            if not call_type:
                return Response({"message": "Please specify call type", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                company = Company.objects.get(pk=request.data['company_id'])
            except Company.DoesNotExist:
                return Response({"message": "Invalid company_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                speaker = User.objects.get(id=request.data['speaker_id'],
                                           userType__type__in=["Mentor", "ProgramManager"])
            except User.DoesNotExist:
                return Response({"message": "Speaker can only be Mentor or ProgramManager", "success": False}, status=status.HTTP_404_NOT_FOUND)
            if journey_id:
                journey = Channel.objects.filter(id=journey_id, parent_id=None,
                                                 is_active=True, is_delete=False).first()
                if not journey:
                    return Response({"message": "journey does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            collaborate = Collabarate.objects.create(title=request.data['title'], journey=request.data['journey_id'], is_active=request.data['is_active'],
                                                     company=company, speaker=speaker, type=call_type, created_by=user, add_to_community=update_boolean(request.data['add_to_community']))
            if not data.get('custom_url'):
                meet, collaborate.token = lives_streaming_room(request.data['title'],call_type, journey_id) # token is the meet_id here
                if collaborate.token == 400:
                    return Response({"message": meet['message'], "success": False}, status=status.HTTP_404_NOT_FOUND)
                collaborate.url_title = collaborate.token
                collaborate.custom_url = f"{BASE_URL}/config/dyte/{collaborate.token}"
            else:
                collaborate.custom_url = data.get('custom_url')
            if collaborate.speaker.phone and collaborate.speaker.is_whatsapp_enable:
                description = f""" Hi {collaborate.speaker}! You have been assigned to a Livestream as an attendee:
                                {collaborate.title} {collaborate.start_time}
                                Would you like to RSVP now? """
                # meeting_notification(collaborate.speaker, collaborate.title, call_type)
                meeting_notification(collaborate.speaker, collaborate.title, description)
                live_stream_event(collaborate.speaker, collaborate.title, collaborate.speaker, collaborate.start_time)
            if collaborate.add_to_community:
                collaborate.space_name = data.get('space_name')
                collaborate.save()
                space_id = data.get('space_name')
                add_to_community_event(collaborate, user, space_id)
            collaborate.save()
            if call_type == "GroupStreaming" and data.get('participants_list'):
                for id in data.get('participants_list'):
                    collaborate.participants.add(id)
            response = {
                "message": "Call created",
                "success": True,
                "data": collaborate.id
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class GetEditStreams(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if call_type := self.request.query_params.get('call_type'):
            collaborate = Collabarate.objects.filter(
                id=self.kwargs['collaborates_id'], is_active=True, is_cancel=False, type=call_type)
            if not collaborate:
                return Response({"message": "invalid uuid", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Please specify call type", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        participant_list = []
        journey = company = None
        if call_type == "GroupStreaming":
            participant_list = [{"id": participant.id, "name": f"{participant.first_name} {participant.last_name}",
                                 "email": participant.email, "profile_image": avatar(participant)} for participant in collaborate.participants.all()]
        if collaborate.journey:
            journey = Channel.objects.filter(title__icontains=collaborate.journey,
                                             parent_id=None, is_active=True, is_delete=False).first()
        if collaborate.company:
            company = Company.objects.get(id=collaborate.company.pk)
        data = {
            "id": collaborate.id,
            "title": collaborate.title,
            "journey_id": journey.pk if journey else '',
            "journey": journey.title if journey else '',
            "company_id": company.id if company else '',
            "company_name": company.name if company else '',
            "description": collaborate.description,
            "custom_url": collaborate.custom_url,
            "speaker_name": f"{collaborate.speaker.first_name} {collaborate.speaker.last_name}",
            "start_time": strf_format(local_time(collaborate.start_time)),
            "end_time": strf_format(local_time(collaborate.end_time)),
            "type": collaborate.type,
            "is_active": collaborate.is_active,
            "is_cancel": collaborate.is_cancel,
            "add_to_community": collaborate.add_to_community,
            "space_name": collaborate.space_name,
            "participant_list": participant_list,
            "cancel_by": f"{collaborate.cancel_by.first_name} {collaborate.cancel_by.last_name}" if collaborate.cancel_by else '',
            "created_at": strf_format(local_time(collaborate.created_at))
        }
        response = {
            "message": "Call created",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        data = request.data
        serializer = LiveStreamSerializer(data=request.data)
        if serializer.is_valid():
            if call_type := self.request.query_params.get('call_type'):
                collaborate = Collabarate.objects.filter(
                    id=self.kwargs['collaborates_id'], is_active=True, is_cancel=False, type=call_type)
                if not collaborate:
                    return Response({"message": "invalid uuid", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"message": "Please specify call type", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            journey_id = data.get('journey_id') or None
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                company = Company.objects.get(pk=request.data['company_id'])
            except Company.DoesNotExist:
                return Response({"message": "Invalid company_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                speaker = User.objects.get(id=request.data['speaker_id'],
                                           userType__type__in=["Mentor", "ProgramManager"])
            except User.DoesNotExist:
                return Response({"message": "Speaker can only be Mentor or ProgramManager", "success": False}, status=status.HTTP_404_NOT_FOUND)
            if journey_id:
                journey = Channel.objects.filter(id=journey_id, parent_id=None,
                                                 is_active=True, is_delete=False).first()
                if not journey:
                    return Response({"message": "journey does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            collaborate.update(title=request.data['title'], journey=request.data['journey_id'], is_active=request.data['is_active'],
                               company=company, speaker=speaker, type=call_type, created_by=user, add_to_community=update_boolean(request.data['add_to_community']))
            collaborate = collaborate.first()
            if not data.get('custom_url'):
                meet, collaborate.token = lives_streaming_room(request.data['title'], call_type, journey_id) # token is the meet_id here
                if collaborate.token == 400:
                    return Response({"message": meet['message'], "success": False}, status=status.HTTP_404_NOT_FOUND)
                collaborate.url_title = collaborate.token
                collaborate.custom_url = f"{BASE_URL}/config/dyte/{collaborate.token}"
            else:
                collaborate.custom_url = data.get('custom_url')
            space_id = data.get('space_name')
            add_to_community_event(collaborate, user, space_id)
            collaborate.save()
            if call_type == "GroupStreaming" and data.get('participants_list'):
                participants_list1 = data.get('participants_list')
                participants_list2 = [participant.id for participant in collaborate.participants.all()]
                for id in participants_list2:
                    if id not in participants_list1:
                        collaborate.participants.remove(id)

                for id in participants_list1:
                    if id not in participants_list2:
                        collaborate.participants.add(id)
            response = {
                "message": "Call updated",
                "success": True,
                "data": collaborate.id
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if call_type := self.request.query_params.get('call_type'):
            collaborate = Collabarate.objects.filter(
                id=self.kwargs['collaborates_id'], is_active=True, is_cancel=False, type=call_type)
            if not collaborate:
                return Response({"message": "invalid uuid", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Please specify call type", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        collaborate.update(is_active=False, is_cancel=True, cancel_by=user)
        response = {
            "message": "Call Deleted Successfully",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class ViewStreamData(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if call_type := self.request.query_params.get('call_type'):
            collaborate = Collabarate.objects.filter(
                id=self.kwargs['collaborates_id'], is_active=True, is_cancel=False, type=call_type)
            if not collaborate:
                return Response({"message": "invalid uuid", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Please specify call type", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        title = collaborate.url_title
        if not title:
            title = collaborate.custom_url.split('/')[-1]
            title = title.split("?")[0]
        data = meeting(title)['data']
        participants = []
        for data in data:
            participants.append(data['participants'])
            try:
                meet_details = AllMeetingDetails.objects.get(id=data['id'])
            except AllMeetingDetails.DoesNotExist:
                meet_details = AllMeetingDetails.objects.create(id=data['id'], collaborate_meeting=collaborate, ongoing=data['ongoing'],
                                                                max_participants=data['max_participants'], title=data['room'], start_time=unixTimstamp(data['start_time']), duration=minutes(data['duration']))
        if participants:
            for user in participants[0]:
                try:
                    MeetingParticipants.objects.get(id=user['participant_id'])
                except MeetingParticipants.DoesNotExist:
                    MeetingParticipants.objects.create(id=user['participant_id'], session=meet_details,
                                                       user_name=user['user_name'], join_time=unixTimstamp(user['join_time']), duration=minutes(user['duration']))

        meets = AllMeetingDetails.objects.filter(collaborate_meeting=collaborate)
        meet_list = []
        for meet in meets:
            all_participant = MeetingParticipants.objects.filter(session=meet)
            user_list = [{"id": participant.id, "user_name": participant.user_name, "join_time": participant.join_time,
                          "duration": participant.duration} for participant in all_participant]
            meet_list.append({
                "id": meet.id,
                "title": meet.title,
                "start_time": strf_format(local_time(meet.start_time)),
                "duration": meet.duration,
                "ongoing": meet.ongoing,
                "max_participants": meet.max_participants,
                "participants_list": user_list
            })
        response = {
            "message": "meeting details",
            "succes": True,
            "data": meet_list
        }
        return Response(response, status=status.HTTP_200_OK)


class ProgramAnnouncement(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if 'timezone' in request.session:
            time_zone = self.request.session['timezone']
        elif 'timezone' in self.request.query_params:
            time_zone = self.request.query_params.get('timezone')
        else:
            return Response({"message": "Please specify timezone", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        userCompany = user_company(user, self.request.session.get('company_id'))
        announcements = ProgramTeamAnnouncement.objects.filter(
            created_by=user, company__in=userCompany, journey__closure_date__gt=datetime.now())
        if journey_id := self.request.query_params.get('journey_id'):
            announcements = announcements.filter(journey__id=journey_id)
        announcement_list = []
        for announcement in announcements:
            announcement_list.append({
                "id": announcement.id,
                "company_id": announcement.company.pk if announcement.company else "",
                "company_name": announcement.company.name if announcement.company else "",
                "journey_id": announcement.journey.id,
                "journey_name": announcement.journey.title,
                "topic": announcement.topic,
                "summary": announcement.summary,
                "announce_date": strf_format(convert_to_local_time(announcement.announce_date, time_zone)),
                "created_by": f"{announcement.created_by.first_name} {announcement.created_by.last_name}",
                "attachment": broadcast_attachment(announcement),
            })
        response = {
            "message": "Annoucement Data",
            "success": True,
            "data": announcement_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = ProgramAnnouncementSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentors = update_boolean(request.data['mentors'])
            learners = update_boolean(request.data['mentees'])
            program_team = update_boolean(request.data['program_team'])
            everyone = update_boolean(request.data['everyone'])
            journey_id = request.data['journey']
            company_id = request.data['company']
            company = user.company.filter(pk=company_id).first()
            if not company:
                return Response({"message": "Invalid company_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                journey = Channel.objects.get(id=journey_id, parent_id=None)
            except Channel.DoesNotExist:
                return Response({"message": "Invalid journey_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            topic = request.data['topic']
            summary = request.data['summary']
            announcement = ProgramTeamAnnouncement.objects.create(
                journey=journey, topic=topic, summary=summary, created_by=user, announce_date=datetime.now(), company=company)
            if "attachment" in request.FILES:
                attachment = request.FILES['attachment']
                name = attachment.name
                content = attachment.read()
                content_type = attachment.content_type
                attachment_info = [name, content, content_type]
                announcement.attachment = attachment
                announcement.save()
                #print("attachment", attachment, announcement.attachment)

            user_channel = UserChannel.objects.filter(Channel_id=journey_id, status="Joined", is_removed=False)
            user_list = []
            if user_channel:
                if mentors:
                    user_channel = user_channel.filter(user__userType__type="Mentor")
                    user_list.extend([channel.user for channel in user_channel])
                if learners:
                    user_channel = user_channel.filter(user__userType__type="Learner")
                    user_list.extend([channel.user for channel in user_channel])
                if everyone:
                    user_list.extend([channel.user for channel in user_channel])
            program_data = User.objects.filter(~Q(id=user.id), company=company, userType__type="ProgramManager")
            if program_team or everyone:
                user_list.extend(list(program_data))
            elif program_team and everyone:
                user_list.extend(list(program_data))
            lis = set(user_list)
            user_list = list(lis)
            email_list = [channel_user.email for channel_user in user_list]
            message = f"""
                    Hello,\n
                    Your Program team has posted the following updates for your attention\n\n
                    By: {user.first_name} {user.last_name}\n
                    Topic: {topic}\n
                    Summary Text: {summary}\n
                    {BASE_URL}\n
                    Regards,\n
                    Program Team
                """
            if user_list:
                program_announcement_email(topic, summary, email_list, user, attachment_info=attachment_info)
                for channel_user in user_list:
                    room = get_chat_room(user, channel_user)
                    room = AllRooms.objects.get(name=room)
                    chat = Chat.objects.create(from_user=user, to_user=channel_user, message=message, room=room)
                    print(f"in app chat: {chat.to_user}")
                    if channel_user.phone and channel_user.is_whatsapp_enable:
                        program_team_broadcast(channel_user, announcement, user)
                    description = f"""Hi {channel_user.first_name} {channel_user.last_name}!
                    Your journey has sent a broadcast notification."""
                    context = {
                        "screen": "Broadcast",
                    }
                    send_push_notification(channel_user, 'Journey Broadcast Notification', description, context)
            response = {
                "message": "Journey Announcement Successful.",
                "success": True,
                "data": announcement.id
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UserToken(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        token, created = Token.objects.get_or_create(user=user)
        token = token.key
        response = {
            "message": "Login successfull",
            "success": True,
            "data": {
                "id": user.id,
                "token": token,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class ForumEvent(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if 'timezone' in request.session:
            time_zone = self.request.session['timezone']
        elif 'timezone' in self.request.query_params:
            time_zone = self.request.query_params.get('timezone')
        else:
            return Response({"message": "Please specify timezone", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        posts = Post.objects.filter(post_type="Event", inappropriate_content=False, is_active=True, is_delete=False)
        event_list = [response_post(post.id, None, offset=time_zone) for post in posts]
        # #print(f"event_list: {event_list['event']['host'].name}")
        response = {
            "message": "Event data list",
            "success": True,
            "data": event_list
        }
        return Response(response, status=status.HTTP_200_OK)


class AlloteUserToJourney(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        channels = program_manager_journey_list(user)
        userchannels = UserChannel.objects.filter(Channel__in=channels, status="Joined", is_alloted=True)
        channel_list = []
        for channel in userchannels:
            channel_list.append({
                "user_id": channel.user.id,
                "user_name": f"{channel.user.first_name} {channel.user.last_name}",
                "user_email": channel.user.email,
                "profile_image": avatar(channel.user),
                "journey_id": channel.Channel.id,
                "journey_name": channel.Channel.title,
                "status": channel.status,
                "is_alloted": channel.is_alloted,
                "alloted_by": f"{channel.alloted_by.first_name} {channel.alloted_by.last_name}",
                "created_at": strf_format(local_time(channel.created_at))
            })
        response = {
            "message": "List of users alloted to listed journeys",
            "success": True,
            "data": channel_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = AllotUserSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            journey = Channel.objects.get(pk=request.data['journey'], is_active=True, is_delete=False, parent_id=None)
            userlist = request.data['user_list']
            #print("user list 673443", request.data['user_list'], request.data.getlist('user_list'))
            userlist = userlist.split(",")
            #print("user list32323", userlist)
            is_wp_enable = update_boolean(request.data['is_wp_enable'])
            for user_id in userlist:
                #print("user id 674", user_id)
                alloted_user = check_valid_user(user_id)
                if not alloted_user:
                    return Response({"message": f"Invalid {user_id}", "success": False}, status=status.HTTP_404_NOT_FOUND)
                user_channel = UserChannel.objects.filter(user=alloted_user, Channel=journey)
                if not user_channel.exists():
                    context = {
                        "screen": "ProgramJourney",
                        "navigationPayload": {
                            "courseId": str(journey.id)
                        }
                    }
                    send_push_notification(alloted_user, journey.title, f"You're enrolled in {journey.title}", context)
                    NotificationAndPoints(alloted_user, "joined journey")
                    UserChannel.objects.create(Channel=journey, user=alloted_user, status="Joined",
                                               alloted_by=user, is_alloted=True)
                    add_user_to_company(alloted_user, journey.company)
                    if journey.whatsapp_notification_required and (alloted_user.phone and is_wp_enable):
                        journey_enrolment(alloted_user, journey)
                    if journey.is_community_required:
                        add_member_to_space(journey, alloted_user)
                elif user_channel.filter(status="removed"):
                    user_channel.update(status="Joined")
                    if journey.whatsapp_notification_required and (alloted_user.phone and is_wp_enable):
                        journey_enrolment(alloted_user, journey)
                else:
                    return Response({"message": f"Journey already alloted to {alloted_user}", "success": True}, status=status.HTTP_200_OK)
            response = {
                "message": "Journey allocation to users is successful",
                "success": True
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class ArchieveUsers(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        companys = user_company(user, self.request.session.get('company_id'))
        user_type = UserTypes.objects.filter(type__in=['Learner', 'Mentor'])

        users = User.objects.filter(company__in=companys, userType__in=user_type,
                                    is_archive=True, is_delete=False, is_active=False).distinct()
        user_list = []
        for arc_user in users:
            user_list.append({
                "id": arc_user.id,
                "name": f"{arc_user.first_name} {arc_user.last_name}",
                "email": arc_user.email,
                "username": arc_user.username,
                "profile_image": avatar(arc_user),
                "user_type": ", ".join(str(type.type) for type in arc_user.userType.all()),
                "company": ", ".join(company.name for company in arc_user.company.all()),
                "updated_at": strf_format(local_time(arc_user.date_modified)),
                "is_archive": arc_user.is_archive,
                "phone": str(arc_user.phone),
                "is_lite_signup": arc_user.is_lite_signup,
                "status": arc_user.is_active
            })
        response = {
            "message": "Archieve users list",
            "success": True,
            "data": user_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = UserIdSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user = User.objects.filter(pk=request.data['user_id']).update(is_archive=True, is_active=False)
            response = {
                "message": "User Archived successful",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class ProgramManagerDataList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)

        companys = user_company(user, self.request.session.get('company_id'))
        user_type = UserTypes.objects.filter(type__in=['Learner', 'Mentor'])
        users = User.objects.filter(company__in=companys, userType__in=user_type,
                                    is_active=True, is_delete=False).distinct()
        user_list = [{"id": student.id, "name": f"{student.first_name} {student.last_name}",
                      "user_type": ", ".join(str(type.type) for type in student.userType.all()),
                      "company": ", ".join(company.name for company in student.company.all()), "email": student.email}
                     for student in users]
        company_list = [{"id": company.pk, "name": company.name} for company in user.company.all()]
        response = {
            "message": "program manager journey list",
            "success": True,
            "user_list": user_list,
            "company_list": company_list
        }
        return Response(response, status=status.HTTP_200_OK)


class MatchingData(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        companys = user.company.all()
        company_list = [{"id": company.pk, "name": company.name} for company in companys]
        journey_list = []
        pool_list = []
        if company_id := self.request.query_params.get('company_id'):
            journeys = program_manager_journey_list(user).filter(
                company__id=company_id, channel_type="MentoringJourney")
            journey_list = [{"id": journey.pk, "name": journey.title} for journey in journeys]

        if journey_id := self.request.query_params.get('journey_id'):
            pools = Pool.objects.filter(journey__id=journey_id, is_active=True)
            pool_list = [{"id": pool.id, "name": pool.name} for pool in pools]

        response = {
            "message": "matching data list",
            "success": True,
            "journey_list": journey_list,
            "pool_list": pool_list,
            "company_list": company_list
        }
        return Response(response, status=status.HTTP_200_OK)


class ProgramManagerJourneyList(APIView):
    def get(self, request, *args, **kwargs):
        company_id = self.request.query_params.get('company_id') or None
        journey_type = self.request.query_params.get('journey_type') or None
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        journeys = program_manager_journey_list(user)
        if company_id:
            journeys = journeys.filter(company__id=company_id)
        if journey_type:
            journeys = journeys.filter(channel_type=journey_type)
        journey_list = [{"id": journey.pk, "name": journey.title, "type": journey.channel_type} for journey in journeys]
        response = {
            "message": "program manager journey list",
            "success": True,
            "data": journey_list
        }
        return Response(response, status=status.HTTP_200_OK)


class MatchingQuestions(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        ques_config = MatchQuesConfig.objects.filter(company__in=company, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now())
        ques_config_list = [{"id": config.id, "company_id": config.company.id, "company_name": config.company.name, "journey_name": config.journey.title,
                             "journey_id": config.journey.id, "created_at": strf_format(local_time(config.created_at)), "updated_at": strf_format(local_time(config.updated_at))} for config in ques_config]
        response = {
            "message": "question configuration list",
            "success": True,
            "data": ques_config_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        #print(request.data)
        serializer = MatchQuestionSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            company = Company.objects.get(pk=request.data['company'])
            journey = Channel.objects.get(pk=request.data['journey'])
            ques_config = MatchQuesConfig.objects.filter(company=company, journey=journey).first()
            if ques_config:
                return Response({"message": "Journey and company match already exist", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            ques_config = MatchQuesConfig.objects.create(company=company, journey=journey, created_by=user)
            for key in request.data['match_question']:
                #print(key)
                mentor_ques = ProfileAssestQuestion.objects.get(pk=key['mentor_ques_id'])
                learner_ques = ProfileAssestQuestion.objects.get(pk=key['learner_ques_id'])
                question_type = key['question_type']
                is_dependent = update_boolean(key['is_dependent'])
                dependent_mentor_ques = None
                dependent_option = key['dependent_option']
                dependent_learner_ques = None
                if is_dependent:
                    try:
                        dependent_mentor_ques = ProfileAssestQuestion.objects.get(pk=key['dependent_mentor_ques_id'])
                        dependent_learner_ques = ProfileAssestQuestion.objects.get(pk=key['dependent_learner_ques_id'])
                    except ProfileAssestQuestion.DoesNotExist:
                        return Response({"message": "Profile Assesst question does not exist", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                    if dependent_option == "":
                        return Response({"message": "dependent option could not be blank", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                MatchQuestion.objects.create(ques_config=ques_config, question_type=question_type, mentor_ques=mentor_ques, dependent_option=dependent_option,
                                             learner_ques=learner_ques, dependent_mentor=dependent_mentor_ques, dependent_learner=dependent_learner_ques, is_dependent=is_dependent)
            response = {
                "message": "Match questions created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class ProfileQuestionList(APIView):
    def get(self, request, *args, **kwargs):
        user_type = self.request.query_params.get('user_type')
        profile_assest_questions = ProfileAssestQuestion.objects.filter(
            question_for=user_type, is_active=True, is_delete=False)
        question_list = [{"question_id": question.id, "question": question.question, "options": question.options, "display_order": question.display_order,
                          "question_type": question.question_type} for question in profile_assest_questions]
        response = {
            "message": "all profile assest questions",
            "success": True,
            "data": question_list
        }
        return Response(response, status=status.HTTP_200_OK)


class MatchingQuestionsData(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            ques_config = MatchQuesConfig.objects.get(id=self.kwargs['config_id'])
        except MatchQuesConfig.DoesNotExist:
            return Response({"message": "Invalid config_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        match_questions = MatchQuestion.objects.filter(ques_config=ques_config)
        match_question_list = []
        for question in match_questions:
            match_question_list.append({
                "id": question.id,
                "mentor_ques": question.mentor_ques.question,
                "learner_ques": question.learner_ques.question,
                "question_type": question.question_type,
                "is_dependent": question.is_dependent,
                "dependent_learner": question.dependent_learner,
                "dependent_mentor": question.dependent_mentor,
                "dependent_option": question.dependent_option
            })
        response = {
            "message": "all match question",
            "success": True,
            "data": match_question_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        #print(request.data)
        serializer = MatchQuestionSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                ques_config = MatchQuesConfig.objects.get(id=self.kwargs['config_id'])
            except MatchQuesConfig.DoesNotExist:
                return Response({"message": "Invalid config_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            for key in request.data['match_question']:
                #print(key)
                mentor_ques = ProfileAssestQuestion.objects.get(pk=key['mentor_ques_id'])
                learner_ques = ProfileAssestQuestion.objects.get(pk=key['learner_ques_id'])
                question_type = key['question_type']
                is_dependent = update_boolean(key['is_dependent'])
                dependent_mentor_ques = None
                dependent_option = key['dependent_option']
                dependent_learner_ques = None
                if is_dependent:
                    try:
                        dependent_mentor_ques = ProfileAssestQuestion.objects.get(pk=key['dependent_mentor_ques_id'])
                        dependent_learner_ques = ProfileAssestQuestion.objects.get(pk=key['dependent_learner_ques_id'])
                    except ProfileAssestQuestion.DoesNotExist:
                        return Response({"message": "Profile Assesst question does not exist", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                    if dependent_option == "":
                        return Response({"message": "dependent option could not be blank", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                MatchQuestion.objects.filter(ques_config=ques_config).update(question_type=question_type,
                                                                             mentor_ques=mentor_ques, dependent_option=dependent_option, learner_ques=learner_ques, dependent_mentor=dependent_mentor_ques, dependent_learner=dependent_learner_ques, is_dependent=True)
            response = {
                "message": "Match questions created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class CreateListTag(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        tags = Tags.objects.all()
        tag_list = [{"id": tag.id, "name": tag.name, "color": tag.color, "is_active": tag.is_active} for tag in tags]
        response = {
            "message": "all tag list",
            "success": True,
            "data": tag_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            name = request.data['name']
            tags = Tags.objects.filter(name=name)
            if tags:
                return Response({"message": f"Tag with {name} is already exist", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            tag = Tags.objects.create(
                name=name, color=request.data['color'], is_active=update_boolean(request.data['is_active']))
            response = {
                "message": "Tag created",
                "success": True,
                "data": {
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color,
                    "is_active": tag.is_active
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class CreateListIndustry(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        industyrs = Industry.objects.all()
        industy_list = [{"id": industy.id, "name": industy.name, "is_active": industy.is_active}
                        for industy in industyrs]
        response = {
            "message": "all industy list",
            "success": True,
            "data": industy_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = IndustrySerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            name = request.data['name']
            industry = Industry.objects.filter(name=name)
            if industry:
                return Response({"message": f"Industy with {name} is already exist", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            industry = Industry.objects.create(name=name, is_active=update_boolean(request.data['is_active']))
            response = {
                "message": "Industry created",
                "success": True,
                "data": {
                    "id": industry.id,
                    "name": industry.name,
                    "is_active": industry.is_active
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class CreateListCategory(APIView):
    serializer_class = CategorySerializer
    model = JourneyCategory
    queryset = JourneyCategory.objects.all()

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(self.queryset.all(), many=True)
        response = {
            "message": "category list",
            "success": True,
            "data": serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            serializer.save()
            response = {
                "message": "category created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class CreateContentList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        
        company = user.company.filter(id=self.request.session['company_id']).first()
        journey_content = ContentChannels.objects.filter(Channel__company=company).values('content_id')
        # mentoring_journey = MentoringJourney.objects.filter(meta_key="quest", journey__company=company).values('value')
        content_id_list = [str(ids['content_id']) for ids in journey_content]
        contents = Content.objects.filter(Q(id__in=content_id_list) | Q(user=user), is_delete=False)
        content_list = []
        for content in contents:
            content_list.append({
                "id": content.id,
                "name": content.title,
                "description": content.description,
                "icon": obj_image(content),
                "status": content.status,
                "content_admin": f"{content.user.first_name} {content.user.last_name}",
                "content_admin_email": content.user.email,
                "created_at": strf_format(local_time(content.created_at)),
                "updated_at": strf_format(local_time(content.updated_at))
            })
        response = {
            "message": "Content list",
            "success": True,
            "data": content_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = CreateContentSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            title = request.data['title']
            description = request.data['description']
            image = request.FILES['image']
            Content.objects.create(title=title, image=image, description=description, user=user)
            response = {
                "message": "Content created successfully",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class EditContentDraft(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        content = Content.objects.filter(id=self.kwargs['content_id'], user=user)
        if not content:
            return Response({"message": "Invalid content_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        content = content.first()
        content_data = ContentData.objects.filter(content=content)
        content_data_list = []
        for data in content_data:
            content_data_list.append({
                "id": data.pk,
                "title": data.title,
                "type": data.type,
                "data": data.data,
                "link_data": data.link_data,
                "file": data.file,
                "video": data.file,
                "url": data.url,
                "option_list": data.option_list,
                "custom_answer": data.custom_answer,
                "display_order": data.display_order,
                "time": data.time
            })
        content_json = {
            "id": content.id,
            "name": content.title,
            "description": content.description,
            "icon": obj_image(content),
            "data": content_data_list
        }
        response = {
            "message": "Content data",
            "success": True,
            "data": content_json
        }
        return Response(response, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        content = Content.objects.filter(id=self.kwargs['content_id'], user=user)
        if not content:
            return Response({"message": "Invalid content_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        content.update(is_delete=True)
        response = {
            "message": "Content deleted",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class AddFieldContentDraft(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddFieldSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            main_content = Content.objects.filter(id=self.kwargs['content_id'], user=user)
            if not main_content:
                return Response({"message": "Invalid content_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            change_course_status_in_group(main_content)
            main_content.update(status="Pending")
            display_order = ContentData.objects.filter(content=main_content).count()
            type = request.data['type']
            content_data = ContentData.objects.create(type=type, content=main_content, display_order=display_order+1)
            if type == "Quiz" or type == "Poll":
                ContentDataOptions.objects.create(content_data=content_data)
            elif type == "Text":
                content_data.data = "Start Writing"
            content_data.save()
            response = {
                "message": "Field added to content",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateFieldData(APIView):
    def post(self, request, *args, **kwargs):
        serializer = EditDraftSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            main_content = Content.objects.filter(id=self.kwargs['content_id'], user=user)
            if not main_content:
                return Response({"message": "Invalid content_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            content = ContentData.objects.filter(pk=request.data['data_id'])
            type = request.data['type']
            if type == "Quize":
                pass
            change_course_status_in_group(content[0].content)
            response = {
                "message": "Content field updated",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class SurveyList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user.company.filter(id=self.request.session['company_id']).first()
        mentoring_journey = MentoringJourney.objects.filter(meta_key="survey", journey__company=company).values('value')
        survey_id_list = [ids['value'] for ids in mentoring_journey]
        surveys = Survey.objects.filter(Q(id__in=survey_id_list) | Q(created_by=user), is_active=True)

        survey_list = [{"id": survey.id, "name": survey.name, "cover_image": cover_images(survey), "is_active": survey.is_active, 
                        "short_description": survey.short_description, "created_at": strf_format(local_time(survey.created_at)), "updated_at": strf_format(local_time(survey.updated_at))} for survey in surveys]
        response = {
            "message": "Survey list",
            "success": True,
            "data": survey_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = CreateSurveySerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            name = request.data['name']
            cover_image = request.FILES['cover_image']
            short_description = request.data['short_description']
            Survey.objects.create(name=name, cover_image=cover_image,
                                  short_description=short_description, created_by=user)
            response = {
                "message": "Survey created successfully",
                "success": True
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UserSurveyResponse(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user.company.all()
        all_journey = Channel.objects.filter(company__in=company)
        all_survey = MentoringJourney.objects.filter(journey__in=all_journey, meta_key="survey").values("value")
        survey_id_list = [ids['value'] for ids in all_survey]
        survey_attempts = SurveyAttempt.objects.filter(survey__in=survey_id_list)
        user_survey_attempt = []
        for survey_attempt in survey_attempts:
            survey_attempt_channel = SurveyAttemptChannel.objects.filter(
                survey_attempt=survey_attempt, user=user).first()
            user_survey_attempt.append({
                "attempt_id": survey_attempt.id,
                "survey_name": survey_attempt.survey.name,
                "survey_id": survey_attempt.survey.id,
                "user_id": survey_attempt.user.id,
                "user_name": f"{survey_attempt.user.first_name} {survey_attempt.user.last_name}",
                "is_check": survey_attempt.is_check,
                "user_skill": survey_attempt.user_skill,
                "channel": survey_attempt_channel.channel.title,
                "created_at": strf_format(local_time(survey_attempt.created_at)),
            })
        response = {
            "message": "User survey responses",
            "success": True,
            "data": user_survey_attempt
        }
        return Response(response, status=status.HTTP_200_OK)


class AssessmentList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user.company.filter(id=self.request.session['company_id']).first()
        mentoring_journey = MentoringJourney.objects.filter(meta_key="assessment", journey__company=company, is_delete=False).values("value")
        assessment_ids = [ids['value'] for ids in mentoring_journey]
        print(assessment_ids)
        skill_config_data = SkillConfig.objects.filter(channel__company=company)
        for config in skill_config_data:
            if config.pre_assessment:
                id = config.pre_assessment.id
            if config.journey_pre_assessment:
                id = config.journey_pre_assessment.id
            assessment_ids.append(str(id))
        channel_group = ChannelGroup.objects.filter(channel__company=company, channel__channel_type="SkillDevelopment")
        for group in channel_group:
            if group.post_assessment:
                assessment_ids.append(group.post_assessment.id)
        assessments = TestSeries.objects.filter(Q(id__in=assessment_ids) | Q(created_by=user), is_active=True)
        assessment_list = [{"id": assessment.id, "name": assessment.name, "cover_image": cover_images(assessment), "auto_check": assessment.auto_check,
                            "is_active": assessment.is_active, "short_description": assessment.short_description, "created_at": strf_format(local_time(assessment.created_at)), "updated_at": strf_format(local_time(assessment.updated_at))} for assessment in assessments]
        response = {
            "message": "User assessment list",
            "success": True,
            "data": assessment_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = CreateAssessmentSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            name = request.data['name']
            cover_image = request.FILES['cover_image']
            auto_check = request.data['auto_check']
            short_description = request.data['short_description']
            TestSeries.objects.create(name=name, cover_image=cover_image,
                                      short_description=short_description, auto_check=auto_check, created_by=user)
            response = {
                "message": "Assessment created successfully",
                "success": True
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class PoolSetup(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        pools = Pool.objects.filter(is_active=True, company__in=company, journey__closure_date__gt=datetime.now())
        if company := self.request.query_params.get('company'):
            pools = pools.filter(company__name__icontains=company)

        if journey := self.request.query_params.get('journey'):
            pools = pools.filter(journey__title__icontains=journey)

        pool_list = []
        for pool in pools:
            pool_list.append({
                "id": pool.id,
                "name": pool.name,
                "journey_name": pool.journey.title,
                "company_name": pool.company.name,
                "description": pool.description,
                "pool_by": pool.pool_by,
                "tags": ','.join([tag.name for tag in pool.tags.all()]),
                "industry": ','.join([industry.name for industry in pool.industry.all()]),
                "is_active": pool.is_active,
                "created_by": pool.created_by
            })
        response = {
            "message": "All pool list",
            "success": True,
            "data": pool_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = CreatePoolSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                journey = Channel.objects.get(id=request.data['journey'])
            except Channel.DoesNotExist:
                return Response({"message": "Invalid journey_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                company = Company.objects.get(pk=request.data['company'])
            except Company.DoesNotExist:
                return Response({"message": "Invalid company_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            tags = request.data['tags']
            tag_list = tags.split(',')
            industrys = request.data['industry']
            industry_list = industrys.split(",")
            pool = Pool.objects.create(name=request.data['name'], company=company, journey=journey, is_active=update_boolean(request.data['is_active']),
                                       pool_by=request.data['pool_by'], created_by=user)
            for tag_id in tag_list:
                pool.tags.add(tag_id)
            for id in industry_list:
                pool.industry.add(id)
            response = {
                "message": "Pool created successfully",
                "success": True
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class PoolAllocation(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        mentors = User.objects.filter(userType__type="Mentor", is_active=True, is_delete=False, company__in=company)
        pool_mentor_list = []
        #print("mentors", mentors)
        for mentor in mentors:
            pool_list = []
            pool_mentors = PoolMentor.objects.filter(
                mentor=mentor, is_active=True, mentor__is_active=True, mentor__is_delete=False)
            for pool_mentor in pool_mentors:
                pool_list.append({
                    "pool_id": pool_mentor.pool.id,
                    "pool_name": pool_mentor.pool.name,
                })
            pool_mentor_list.append({
                "mentor_id": mentor.id,
                "mentor_name": f"{mentor.first_name} {mentor.last_name}",
                "status": mentor.is_active,
                "pools": pool_list,
                "mentor_username": mentor.username
            })
        response = {
            "message": "pool allocated user list",
            "success": True,
            "data": pool_mentor_list
        }
        return Response(response, status=status.HTTP_200_OK)


class ProgramForum(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        posts = Post.objects.filter(created_by=user, inappropriate_content=False, is_active=True, is_delete=False)
        post_list = [response_post(post) for post in posts]
        response = {
            "message": "User all post",
            "success": True,
            "data": post_list
        }
        return Response(response, status=status.HTTP_200_OK)


class SpaceDetails(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SpaceSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                space_group = SpaceGroups.objects.get(id=request.data['space_group'])
            except SpaceGroups.DoesNotExist:
                return Response({"message": "Invalid space_group_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            Spaces.objects.create(title=request.data['title'], description=request.data['description'], cover_image=request.FILES['cover_image'], created_by=user, space_group=space_group,
                                  space_type=request.data['space_type'], privacy=request.data['privacy'], is_hidden=request.data['is_hidden'], hidden_from_non_members=request.data['hidden_from_non_members'], is_active=update_boolean(request.data['is_active']))
            response = {
                "message": "Space created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpaceGroupDetails(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SpaceGroupSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            SpaceGroups.objects.create(title=request.data['title'], description=request.data['description'], cover_image=request.FILES['cover_image'], created_by=user,
                                       privacy=request.data['privacy'], is_hidden=request.data['is_hidden'], hidden_from_non_members=request.data['hidden_from_non_members'], is_active=update_boolean(request.data['is_active']))
            response = {
                "message": "Space Group created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class JourneyPageSetup(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        journey = company_journeys(self.request.session['user_type'], user, self.request.session.get('company_id'))
        journeycontents = journeyContentSetup.objects.filter(
            created_by=user, is_active=True, is_delete=False, journey__in=journey)
        setup_list = []
        for content in journeycontents:
            setup_list.append({
                "id": content.id,
                "journey": content.journey.title,
                "learn_label": content.learn_label,
                "overview": content.overview,
                "pdpa_label": content.pdpa_label,
                "pdpa_description": content.pdpa_description,
                "is_active": content.is_active,
                "created_at": strf_format(local_time(content.created_at)),
                "updated_at": strf_format(local_time(content.updated_at))
            })
        response = {
            "message": "journey setup data list",
            "success": True,
            "data": setup_list
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = JourneyContentCreationSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            channel = Channel.objects.filter(
                id=request.data['journey'], channel_type="MentoringJourney", is_delete=False, is_active=True, is_lite_signup_enable=True).first()
            if not channel:
                return Response({"message": "Invalid journey", "success": False}, status=status.HTTP_404_NOT_FOUND)
            journeyContentSetup.objects.create(journey=channel, overview=request.data['overview'], learn_label=request.data['learn_label'],
                                               pdpa_description=request.data['pdpa_description'], pdpa_label=request.data['pdpa_label'], created_by=user)
            response = {
                "message": "Journey content created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class EditJourneyPageSetup(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        setup = journeyContentSetup.objects.get(id=self.kwargs['setup_id'])
        data = {
            "id": setup.id,
            "journey": setup.journey.title,
            "learn_label": setup.learn_label,
            "overview": setup.overview,
            "pdpa_label": setup.pdpa_label,
            "pdpa_description": setup.pdpa_description,
            "is_active": setup.is_active,
            "created_at": strf_format(local_time(setup.created_at)),
            "updated_at": strf_format(local_time(setup.updated_at))
        }
        response = {
            "message": "journey setup data",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)


class AllBadgeList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        badges = BadgeDetails.objects.filter(is_active=True, created_by=user)
        data = []
        for badge in badges:
            data.append({
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "image": obj_image(badge),
                "points_required": badge.points_required,
                "badge_for": badge.badge_for,
                "created_at": strf_format(local_time(badge.created_at)),
                "is_active": badge.is_active
            })

        # #print("data badge", data)

        response = {
            "message": "All badges list",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = BadgeCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            # serializer.save()
            badge = BadgeDetails.objects.create(name=request.data["name"], description=request.data["description"], image=request.data["image"], is_active=update_boolean(
                request.data["is_active"]), points_required=request.data["points_required"], badge_for=request.data["badge_for"], created_by=user)
            response = {
                "message": "Badge Created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class AllPoints(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        points = PointsTable.objects.filter(is_active=True)
        data = []
        for point in points:
            data.append({
                "id": point.id,
                "name": point.name,
                "label": point.label,
                "points": point.points,
                "message": point.comment,
                "is_active": point.is_active,
                "created_at": strf_format(local_time(point.created_at))
            })

        response = {
            "message": "All points",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = PointsCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            # serializer.save()
            point = PointsTable.objects.create(
                name=request.data["name"], label=request.data["label"], points=request.data["points"], comment=request.data["comment"], created_by=user)
            response = {
                "message": "Point Created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UserSubscriptionList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        subscriptions = SubcribedUser.objects.filter(user=user,
                                                     is_subscribed=True, is_active=True, is_delete=False, is_cancel=False)
        data = []
        for subs in subscriptions:
            data.append({
                "id": subs.id,
                "subscription_title": subs.subscription.title,
            })
        response = {
            "message": "All Subscriptions",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)


class CapacityRatioList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        ratios = MentorMenteeRatio.objects.filter(
            user_subscription__is_subscribed=True, user_subscription__is_cancel=False, is_active=True, is_delete=False, company__in=company)
        data = [{
                "id": ratio.id,
                "subscription_name": ratio.user_subscription.subscription.title if ratio.user_subscription else ratio.subscription.title,
                "subscription_id": ratio.user_subscription.subscription.id if ratio.user_subscription else ratio.subscription.id,
                "company_id": ratio.company.id if ratio.company else '',
                "company_name": ratio.company.name if ratio.company else '',
                "max_mentor": ratio.max_mentor,
                "max_learner": ratio.max_learner,
                "learners_per_mentor": ratio.learners_per_mentor,
                "max_member": ratio.max_member,
                "is_active": ratio.is_active
                } for ratio in ratios]
        response = {
            "message": "mentor mentee ratio list",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = CapacityRatioSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user_subscription = SubcribedUser.objects.get(id=request.data['subscription_id'])
            except SubcribedUser.DoesNotExist:
                return Response({"message": "Invalid subscription_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            ratio = MentorMenteeRatio.objects.filter(subscription=user_subscription.subscription).last()
            max_mentor = request.data['max_mentor']
            learners_per_mentor = request.data['learners_per_mentor']
            if ratio.learners_per_mentor < int(learners_per_mentor):
                return Response({"message": f"Set a mentee per mentor capacity less than ( {ratio.learners_per_mentor} ) subscription limit", "success": True, "default_ratio": ratio.learners_per_mentor}, status=status.HTTP_200_OK)
            max_learner = request.data['max_learner']
            MentorMenteeRatio.objects.create(user_subscription=user_subscription, max_mentor=max_mentor, subscription=user_subscription.subscription,
                                             company=user_subscription.company, max_learner=max_learner, learners_per_mentor=learners_per_mentor)
            response = {
                "message": "Mentor Mentee Ratio Created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class DefaultCapacityRatio(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user_subscription = SubcribedUser.objects.get(id=self.kwargs['subs_id'], is_active=True, is_delete=False)
        except SubcribedUser.DoesNotExist:
            return Response({"message": "Invalid subs_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        ratio = MentorMenteeRatio.objects.filter(
            subscription=user_subscription.subscription, is_active=True, is_delete=False).last()
        if not ratio:
            return Response({"message": "No default ratio available", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "id": ratio.id,
            "subscription_id": user_subscription.subscription.id,
            "subscription_name": user_subscription.subscription.title,
            "max_mentor": ratio.max_mentor,
            "max_learner": ratio.max_learner,
            "learners_per_mentor": ratio.learners_per_mentor,
            "max_member": ratio.max_member,
            "is_active": ratio.is_active
        }
        response = {
            "message": "default mentor mentee ratio",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)


class UpdateCapacityRatio(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        ratio = MentorMenteeRatio.objects.filter(id=self.kwargs['ratio_id'], is_active=True, is_delete=False)
        if not ratio:
            return Response({"message": "Invalid ratio_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "id": ratio.id,
            "subscription_name": ratio.user_subscription.subscription.title,
            "subscription_id": ratio.user_subscription.subscription.id,
            "max_mentor": ratio.max_mentor,
            "max_learner": ratio.max_learner,
            "learners_per_mentor": ratio.learners_per_mentor,
            "max_member": ratio.max_member,
            "is_active": ratio.is_active
        }
        response = {
            "message": "mentor mentee ratio",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer = CapacityRatioSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            ratio = MentorMenteeRatio.objects.filter(id=self.kwargs['ratio_id'], is_active=True, is_delete=False)
            if not ratio:
                return Response({"message": "Invalid ratio_id or inactive data", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user_subscription = SubcribedUser.objects.get(id=request.data['subscription_id'])
            except SubcribedUser.DoesNotExist:
                return Response({"message": "Invalid subscription_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            max_mentor = request.data['max_mentor']
            max_learner = request.data['max_learner']
            learners_per_mentor = request.data['learners_per_mentor']
            ratio.filter(subscription=user_subscription, max_mentor=max_mentor,
                         max_learner=max_learner, learners_per_mentor=learners_per_mentor)
            response = {
                "message": "Mentor Mentee Ratio Created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class AutoMatching(APIView):
    def post(self, request, *args, **kwargs):
        serializer = MatchingSerializer(data=request.data)
        if serializer.is_valid():
            print("DATA",  request.data)
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                journey = Channel.objects.get(pk=request.data['journey_id'],
                                              parent_id=None, is_active=True, is_delete=False)
            except Channel.DoesNotExist:
                return Response({"message": "Invalid jounrey_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                company = Company.objects.get(pk=request.data['company_id'], is_delete=False)
            except Company.DoesNotExist:
                return Response({"message": "Invalid company_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                pool = Pool.objects.get(pk=request.data['pool_id'], is_active=True)
            except Pool.DoesNotExist:
                return Response({"message": "Invalid pool_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user_list = matching_mentor_1(journey, pool, company)
            data = {
                "company_id": company.id,
                "company_name": company.name,
                "journey_id": journey.id,
                "journey_name": journey.title,
                "pool_id": pool.id,
                "pool_name": pool.name,
                "user_list": user_list
            }
            response = {
                "message": "auto matching data",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class ManualMatching(APIView):
    def post(self, request, *args, **kwargs):
        serializer = MatchingSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                journey = Channel.objects.get(pk=request.data['journey_id'],
                                              parent_id=None, is_active=True, is_delete=False)
            except Channel.DoesNotExist:
                return Response({"message": "Invalid journey_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                pool = Pool.objects.get(pk=request.data['pool_id'], is_active=True)
            except Pool.DoesNotExist:
                return Response({"message": "Invalid pool_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user_list = []
            user_channel = UserChannel.objects.filter(
                Channel=journey, status="Joined", user__is_active=True, user__is_delete=False)
            pool_mentor = PoolMentor.objects.filter(pool=pool, mentor__is_active=True, mentor__is_delete=False)
            #print("pool_mentor 1867", pool_mentor)
            poll_mentor_list_data = []
            for pool_mentor in pool_mentor:
                mentor = pool_mentor.mentor
                if UserTypes.objects.get(type="Mentor") in mentor.userType.all():
                    poll_mentor_list_data.append({
                        "name": mentor.first_name + " " + mentor.last_name,
                        "id": mentor.id,
                    })

            for user_channel in user_channel:
                new_pool_list = []

                for mentor in poll_mentor_list_data:
                    assign_check = AssignMentorToUser.objects.filter(
                        journey=journey, mentor_id=mentor['id'], user=user_channel.user, is_assign=True, is_revoked=False, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now()).first()
                    new_pool_list.append({
                        "name": mentor['name'],
                        "id": mentor['id'],
                        "already_checked": assign_check.mentor.id if assign_check else "",
                        "assign_date": strf_format(local_time(assign_check.created_at)) if assign_check else ""
                    })

                if UserTypes.objects.get(type="Learner") in user_channel.user.userType.all():
                    user_list.append({
                        "user": user_channel.user.id,
                        "email": user_channel.user.email,
                        "name": f"{user_channel.user.first_name} {user_channel.user.last_name}",
                        "poll_mentor_list": new_pool_list
                    })
            data = {
                "journey_id": journey.id,
                "journey_name": journey.title,
                "pool_id": pool.id,
                "pool_name": pool.name,
                "user_list": user_list
            }
            response = {
                "message": "manual matching data",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class MetneeList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        journey = Channel.objects.filter(company__in=company)
        assigned_mentor_user = AssignMentorToUser.objects.filter(journey__in=journey, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now())
        if assign := self.request.query_params.get('assign'):
            assigned_mentor_user = assigned_mentor_user.filter(is_assign=True)
        if revoke := self.request.query_params.get('revoke'):
            assigned_mentor_user = assigned_mentor_user.filter(is_revoked=True)
        learner_list = [{
            "mentee_id": learner.user.id,
            "mentee_name": f"{learner.user.first_name} {learner.user.last_name}",
            "mentee_email": learner.user.email,
            "user_type": ','.join([type.type for type in learner.user.userType.all()]),
            "mentor_id": learner.mentor.id,
            "mentor_name": f"{learner.mentor.first_name} {learner.mentor.last_name}",
            "mentor_email": learner.mentor.email,
            "journey_name": learner.journey.title,
            "assign_by": f"{learner.assign_by.first_name} {learner.assign_by.last_name}",
            "is_assign": learner.is_assign,
            "is_revoked": learner.is_revoked,
            "created_at": strf_format(local_time(learner.created_at)),
            "assign_date": strf_format(local_time(learner.created_at)),
            "revoke_date": strf_format(local_time(learner.updated_at))
        } for learner in assigned_mentor_user]
        response = {
            "message": "All mentee list",
            "success": True,
            "data": learner_list
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        journey = Channel.objects.filter(company__in=company)
        assigned_mentor_user = AssignMentorToUser.objects.filter(journey__in=journey, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now())
        if assign := self.request.query_params.get('assign'):
            assigned_mentor_user = assigned_mentor_user.filter(is_assign=True)
        if revoke := self.request.query_params.get('revoke'):
            assigned_mentor_user = assigned_mentor_user.filter(is_revoked=True)
        mentor_list = []
        mentor_id_list = []
        for mentor in assigned_mentor_user:
            if mentor.mentor.id not in mentor_id_list:
                #print("line 1924", mentor, mentor.mentor)
                mentor_id_list.append(mentor.mentor.id)
                # learners = AssignMentorToUser.objects.filter(mentor=mentor.mentor, journey__company=company)
                # learners_list = [{
                #     "mentee_id": learner.user.id,
                #     "name": f"{learner.user.first_name} {learner.user.last_name}",
                #     "email": learner.user.email
                # } for learner in learners]
                mentor_list.append({
                    "mentor_id": mentor.mentor.id,
                    "mentor_name": f"{mentor.mentor.first_name} {mentor.mentor.last_name}",
                    "mentor_email": mentor.mentor.email,
                    # "mentee_list": learners_list,
                    "type": ','.join([type.type for type in mentor.mentor.userType.all()]),
                    "journey_name": mentor.journey.title,
                    "assign_by": f"{mentor.assign_by.first_name} {mentor.assign_by.last_name}",
                    "is_assign": mentor.is_assign,
                    "is_revoked": mentor.is_revoked,
                    "created_at": strf_format(local_time(mentor.created_at)),
                    "assign_date": strf_format(local_time(mentor.created_at)),
                    "revoke_date": strf_format(local_time(mentor.updated_at))
                })
        response = {
            "message": "All Mentor list",
            "success": True,
            "data": mentor_list
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorMenteePairing(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        journey = Channel.objects.filter(company__in=company, closure_date__gt=datetime.now())
        assigned_mentor_user = AssignMentorToUser.objects.filter(journey__in=journey, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now())
        if assign := self.request.query_params.get('assign'):
            assigned_mentor_user = assigned_mentor_user.filter(is_assign=True)
        if revoke := self.request.query_params.get('revoke'):
            assigned_mentor_user = assigned_mentor_user.filter(is_revoked=True)
        learner_list = [{
            "mentee_id": learner.user.id,
            "mentee_name": f"{learner.user.first_name} {learner.user.last_name}",
            "mentee_email": learner.user.email,
            "user_type": ','.join([type.type for type in learner.user.userType.all()]),
            "mentor_id": learner.mentor.id,
            "mentor_name": f"{learner.mentor.first_name} {learner.mentor.last_name}",
            "mentor_email": learner.mentor.email,
            "journey_name": learner.journey.title,
            "assign_by": f"{learner.assign_by.first_name} {learner.assign_by.last_name}",
            "is_assign": learner.is_assign,
            "is_revoked": learner.is_revoked,
            "assign_date": strf_format(local_time(learner.created_at)),
            "revoke_date": strf_format(local_time(learner.updated_at))
        } for learner in assigned_mentor_user]
        response = {
            "message": "All mentee list",
            "success": True,
            "data": learner_list
        }
        return Response(response, status=status.HTTP_200_OK)


class ALLSubscriptions(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        subscription = Subscription.objects.filter(is_active=True, is_delete=False)
        subscriptiom_list = []
        for subs in subscription:
            # mentor_mentee_ratio = MentorMenteeRatio.objects.filter(subscription=subs, is_active=True, is_delete=False)
            # #print("mentor_mentee_ratio ",mentor_mentee_ratio)
            user_subscription = SubcribedUser.objects.filter(
                subscription=subs, user=user, is_active=True, is_delete=False).first()
            #print("user_subscription ", user_subscription)
            if user_subscription:
                left_days = local_time(user_subscription.end_date) - aware_time(datetime.now())
                mentor_mentee_ratio = MentorMenteeRatio.objects.filter(
                    user_subscription=user_subscription, is_active=True, is_delete=False).first()
                if not mentor_mentee_ratio:
                    mentor_mentee_ratio = MentorMenteeRatio.objects.filter(
                        subscription=subs, is_active=True, is_delete=False).first()
            else:
                mentor_mentee_ratio = MentorMenteeRatio.objects.filter(
                    subscription=subs, is_active=True, is_delete=False).first()
            #print("mentor_mentee_ratio ", mentor_mentee_ratio)
            subscriptiom_list.append({
                "id": subs.id,
                "title": subs.title,
                "description": subs.description,
                "terms_conditions": subs.terms_conditions,
                "price": subs.price,
                "currency": subs.currency,
                "duration": subs.duration,
                "trial_duration": subs.trial_duration,
                "duration_type": subs.duration_type,
                "is_trial": subs.is_trial,
                "trial_period": subs.trial_period,
                "sub_type": subs.sub_type,
                "on_offer": subs.on_offer,
                "max_member": mentor_mentee_ratio.max_member if mentor_mentee_ratio else '',
                "max_mentor": mentor_mentee_ratio.max_mentor if mentor_mentee_ratio else '',
                "max_learner": mentor_mentee_ratio.max_learner if mentor_mentee_ratio else '',
                "learner_per_mentor": mentor_mentee_ratio.learners_per_mentor if mentor_mentee_ratio else '',
                "left_days": left_days.days if user_subscription else '',
                "is_purchased": user_subscription.is_subscribed if user_subscription else False,
                "valid_till": strf_format(local_time(user_subscription.end_date)) if user_subscription else '',
                "created_at": strf_format(local_time(subs.created_at))
            })
        response = {
            "message": "All subscriptions list",
            "success": True,
            "data": subscriptiom_list
        }
        return Response(response, status=status.HTTP_200_OK)


class SubscriptionDetail(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CancelSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                company = Company.objects.get(id=request.data['company_id'])
            except Company.DoesNotExist:
                return Response({"message": "Invalid company_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            is_cancel = update_boolean(request.data['is_cancel'])
            user_subscription = SubcribedUser.objects.filter(user=user,
                                                             id=request.data['user_subscription_id'], company=company, is_active=True, is_delete=False).first()
            if not user_subscription:
                return Response({"message": "Invalid user_subscription_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            #print("line 2037", user_subscription, is_cancel)
            user_subscription.is_cancel = is_cancel
            user_subscription.end_date = datetime.now()
            user_subscription.is_subscribed = False
            user_subscription.is_active = False
            user_subscription.is_delete = True
            user_subscription.save()
            MentorMenteeRatio.objects.filter(user_subscription=user_subscription).update(
                is_active=False, is_delete=True)
            response = {
                "message": "The subscription is cancelled",
                "success": True
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            subs = Subscription.objects.get(id=self.kwargs['subs_id'])
        except Subscription.DoesNotExist:
            return Response({"message": "Invalid subscription_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_subscription = SubcribedUser.objects.filter(user=user, subscription=subs, is_cancel=False)
        if user_subscription:
            user_subscription = user_subscription.first()
            left_days = user_subscription.end_date - aware_time(datetime.now())
            #print(f"left_days {left_days.days}")
        subscription = {
            "title": subs.title,
            "description": subs.description,
            "terms_conditions": subs.terms_conditions,
            "price": subs.price,
            "currency": subs.currency,
            "duration": subs.duration,
            "trial_duration": subs.trial_duration,
            "duration_type": subs.duration_type,
            "is_trial": subs.is_trial,
            "trial_period": subs.trial_period,
            "sub_type": subs.sub_type,
            "on_offer": subs.on_offer,
            "left_days": left_days.days,
            "is_purchased": True if user_subscription else False,
            "valid_till": strf_format(local_time(user_subscription.end_date)) if user_subscription else '',
            "created_at": strf_format(local_time(subs.created_at))
        }
        response = {
            "message": "All subscriptions list",
            "success": True,
            "data": subscription
        }
        return Response(response, status=status.HTTP_200_OK)


class UserTransactions(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        transactions = Transaction.objects.filter(user=user, company__in=company)
        transaction_list = []
        for transaction in transactions:
            user_subscription = SubcribedUser.objects.filter(user=user, subscription=transaction.subscription).first()
            transaction_list.append({
                "id": transaction.id,
                "user_name": f"{transaction.user.first_name} {transaction.user.last_name}",
                "company_name": transaction.company.name,
                "subscription_name": transaction.subscription.title,
                "transaction_id": transaction.transaction_id,
                "amount": transaction.amount,
                "currency_code": transaction.currency_code,
                "status": transaction.status,
                "subscription_duration": f"{transaction.subscription.duration} {transaction.subscription.duration_type}",
                "transaction_date": strf_format(local_time(transaction.created_at)),
                "subscription_start_date": strf_format(local_time(user_subscription.start_date)),
                "subscription_end_date": strf_format(local_time(user_subscription.end_date))
            })
        response = {
            "message": "All transaction list",
            "success": True,
            "data": transaction_list
        }
        return Response(response, status=status.HTTP_200_OK)


class AddMentorPool(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddMentorPoolSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            pool_id = request.data['pool_id']
            pool = Pool.objects.filter(id=pool_id).first()
            if not pool:
                return Response({"message": "Invalid pool_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentor_id = request.data['mentor_id'].split(",")
            #print("mentor_id", mentor_id)
            for id in mentor_id:
                #print("mentor_id", id)
                mentor = Mentor.objects.filter(pk=id).first()
                if PoolMentor.objects.filter(pool=pool, mentor=mentor).exists():
                    return Response({"message": "mentor pool already exist", "success": False}, status=status.HTTP_200_OK)
                PoolMentor.objects.create(pool=pool, mentor=mentor)
            response = {
                "message": "add mentor to pool successful",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateMentorPool(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddMentorPoolSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentor = Mentor.objects.filter(pk=request.data['mentor_id']).first()
            if not mentor:
                return Response({"message": "Invalid mentor_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            PoolMentor.objects.filter(mentor=mentor).update(is_active=False)
            selected_pool_list = request.data['pool_id']
            selected_pool_list = selected_pool_list.split(",")
            for pool_id in selected_pool_list:
                pool = Pool.objects.filter(id=pool_id).first()
                if not pool:
                    return Response({"message": "Invalid pool_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
                if PoolMentor.objects.filter(pool=pool, mentor=mentor, is_active=True).exists():
                    PoolMentor.objects.filter(mentor=mentor, pool=pool).update(is_active=True)
                else:
                    PoolMentor.objects.create(pool=pool, mentor=mentor, is_active=True)
            response = {
                "message": "mentor pool updated successfully",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignMentor(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AssignMentorSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentor = request.data['mentor_id']
            try:
                journey = Channel.objects.get(pk=request.data['journey_id'])
            except Channel.DoesNotExist:
                return Response({"message": "Invalid Channel_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                learner = Learner.objects.get(pk=request.data['learner_id'])
            except Learner.DoesNotExist:
                return Response({"message": "Invalid Learner_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                mentor = Mentor.objects.get(pk=mentor)
            except Mentor.DoesNotExist:
                return Response({"message": "Invalid Mentor_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            ratio = menter_mentee_capacity(company=journey.company, user=user)
            assign_menter = AssignMentorToUser.objects.filter(mentor=mentor, journey=journey, is_assign=True, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now()).count()
            if ratio:
                mentor_capacity = ratio.learners_per_mentor
                if mentor_capacity <= assign_menter:
                    return Response({"message": "Mentor has reached the total mentee capacity", "success": True}, status=status.HTTP_200_OK)
            assign_menter = AssignMentorToUser.objects.filter(
                user=learner, mentor=mentor, journey=journey, is_assign=True, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now())
            if assign_menter.count() > 0:
                return Response({"message": "Already Assigned", "success": True}, status=status.HTTP_200_OK)
            assign_menter_check = AssignMentorToUser.objects.filter(user=learner, journey=journey, is_assign=True, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now())
            if assign_menter_check.count() > 0:
                assign_menter_check.update(is_assign=False, is_revoked=True, revoked_by=request.user)
            AssignMentorToUser.objects.create(user=learner, mentor=mentor, journey=journey, assign_by=user)
            description = f"""Hi {mentor.first_name} {mentor.last_name}!
                        You have been matched with {learner.get_full_name()} for {journey.title}!
                        Go start your journey with your Mentee by saying Hi first!"""

            context = {
                "screen":"Mentee",
            }
            send_push_notification(mentor, 'Mentee Assigned', description, context)

            description = f"""Hi {learner.first_name} {learner.last_name}!
                        You have been matched with {mentor.get_full_name()} for {journey.title}!
                        Go start your journey with your Mentor by saying Hi first!"""

            context = {
                "screen":"Mentor",
            }
            send_push_notification(learner, 'Mentor Assigned', description, context)
            response = {
                "message": "mentor assigned successfully",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UserChatList(APIView):
    def get(self, request, *args, **kwargs):
        user_type = self.request.query_params.get('user_type')
        # #print('usertieepe', user_type)
        try:
            mentor = User.objects.get(id=self.kwargs['mentor_id'], userType__type=user_type)
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        all_rooms = AllRooms.objects.filter(Q(user1=mentor) | Q(user2=mentor) | Q(members__in=[mentor]))
        all_rooms_list = []
        for rooms in all_rooms:
            if (rooms.type == 'OneToOne'):

                unread_msg = Chat.objects.filter(Q(to_user=mentor) & Q(from_user=rooms.user2) | Q(to_user=mentor) & Q(
                    from_user=rooms.user1), ~Q(read_by__in=[mentor])).count()

                if mentor == rooms.user1:
                    all_rooms_list.append({
                        "type": rooms.type,
                        "user_id": rooms.user2.id,
                        "name": f"{rooms.user2.first_name} {rooms.user2.last_name}",
                        "avatar": avatar(rooms.user2),
                        "room_name": rooms.name,
                        "unread_msg": unread_msg,
                        "members_count": ""
                    })
                else:
                    all_rooms_list.append({
                        "type": rooms.type,
                        "user_id": rooms.user1.id,
                        "name": f"{rooms.user1.first_name} {rooms.user1.last_name}",
                        "avatar": avatar(rooms.user1),
                        "room_name": rooms.name,
                        "unread_msg": unread_msg,
                        "members_count": ""
                    })

            else:
                unread_msg = Chat.objects.filter(~Q(read_by__in=[mentor]) & ~Q(
                    from_user=mentor), room=rooms).count()
                all_rooms_list.append({
                    "type": rooms.type,
                    "user_id": "",
                    "name": rooms.group_name,
                    "avatar": group_avatar(rooms),
                    "room_name": rooms.name,
                    "unread_msg": unread_msg,
                    "members_count": rooms.members.count(),
                })

        mentor_details = {
            "id": mentor.id,
            "full_name": f"{mentor.first_name} {mentor.last_name}",
            "username": mentor.username,
            "profile_image": avatar(mentor),
            "profile_heading": mentor.profile_heading,
        }
        response = {
            "message": "Success",
            "success": True,
            "data": all_rooms_list,
            "mentor_details": mentor_details
        }
        return Response(response, status=status.HTTP_200_OK)


class UserChatMsg(APIView):
    def get(self, request, *args, **kwargs):
        user_type = self.request.query_params.get('user_type')
        # #print('usertieepe', user_type)
        try:
            mentor = User.objects.get(id=self.kwargs['mentor_id'], userType__type=user_type)
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        try:
            my_room = AllRooms.objects.get(name=self.kwargs['room_name'])
        except AllRooms.DoesNotExist:
            return Response({"message": "Room does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        if not self.request.query_params.get('timezone'):
            return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        timezone = self.request.query_params.get('timezone')

        chats = Chat.objects.filter(
            Q(from_user=my_room.user1) & Q(to_user=my_room.user2) | Q(from_user=my_room.user2) & Q(
                to_user=my_room.user1) | Q(room=my_room)).order_by('timestamp')
        # #print(chats)
        chat_list = []
        if chats:
            for chat in chats:
                chat.read_by.add(mentor)
                chat.save()

            for msg in chats:
                # #print("sender", msg.from_user)
                chat_list.append({
                    "id": msg.id,
                    "room_type": my_room.type,
                    "sender_id": msg.from_user.id,
                    "from_user": f"{msg.from_user.first_name} {msg.from_user.last_name}",
                    "sender_avatar": avatar(msg.from_user),
                    "receiver_avatar": avatar(msg.to_user) if msg.to_user else "",
                    "receiver_id": msg.to_user.id if msg.to_user else '',
                    "to_user": f"{msg.to_user.first_name} {msg.to_user.last_name}" if msg.to_user else '',
                    "message": msg.message,
                    "msg_type": msg.msg_type,
                    "file": certificate_file(msg),
                    "file_name": msg.file_name if msg.file_name else '',
                    "is_read": msg.is_read,
                    "room_name": my_room.name,
                    "group_name": my_room.group_name if my_room.group_name else '',
                    "group_avatar": group_avatar(my_room) if my_room.group_image else "",
                    "created_at": strf_format(convert_to_local_time(msg.timestamp, timezone)),
                    "type":msg.msg_type
                })

        sender_details = {
            "id": mentor.id,
            "full_name": f"{mentor.first_name} {mentor.last_name}",
            "username": mentor.username,
            "profile_image": avatar(mentor),
            "profile_heading": mentor.profile_heading,
        }
        if my_room.type == "OneToOne":
            if mentor == my_room.user1:
                receiver_details = {
                    "id": my_room.user2.id,
                    "full_name": f"{my_room.user2.first_name} {my_room.user2.last_name}",
                    "username": my_room.user2.username,
                    "profile_image": avatar(my_room.user2),
                }
            else:
                receiver_details = {
                    "id": my_room.user1.id,
                    "full_name": f"{my_room.user1.first_name} {my_room.user1.last_name}",
                    "username": my_room.user1.username,
                    "profile_image": avatar(my_room.user1),
                }
        else:
            receiver_details = {
                "group_name": my_room.group_name,
                "group_image": group_avatar(my_room),
                "group_members": my_room.members.count()
            }

        room_details = {
            "room_type": my_room.type,
            "room_name": my_room.name
        }

        response = {
            "message": "Success",
            "success": True,
            "data": chat_list,
            "sender_details": sender_details,
            "receiver_details": receiver_details,
            "room_details":room_details
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorMatchingReport(APIView):
    def post(self, request, *args, **kwargs):
        serializer = MatchingReportSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            #print("companuy_id", request.data['company_id'])
            try:
                company = Company.objects.get(pk=request.data['company_id'])
            except Company.DoesNotExist:
                return Response({"message": "Invalid Company Id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            learner_left = 0
            member_left = 0
            mentor_count = 0
            learner_count = 0
            ratio = menter_mentee_capacity(company, user)
            if not ratio:
                return Response({"message": "There is no valid plans for this company, Please purchase first then recheck the report", "success": False}, status=status.HTTP_404_NOT_FOUND)
                # max_mentor = ratio.max_mentor
                # max_learner = ratio.max_learner
            max_member = User.objects.filter(Q(userType__type="Mentor") or Q(
                userType__type="Learner"), is_active=True, is_delete=False, company=company).count()
            users = User.objects.filter(userType__type="Mentor", is_active=True, is_delete=False, company=company)
            learners_per_mentor = ratio.learners_per_mentor
            # if max_member > ratio.max_member:
            #     member_left = "You're exceeding max count"
            # elif max_member < ratio.max_member:
            #     member_left = ratio.max_member - max_member
            # elif max_member == ratio.max_member:
            #     member_left = 0
            # if max_mentor <= assign_menter:
            #     return Response({"message": "Mentor has reached the total mentee capacity", "success": True}, status=status.HTTP_200_OK)
            if users:
                mentor_count = users.count()
                learner_count = max_member - mentor_count
            mentor_list = []
            for mentor in users:
                learners_list = []
                learners = AssignMentorToUser.objects.filter(mentor_id=mentor, journey__company=company, journey__is_active=True, journey__is_delete=False, journey__closure_date__gt=datetime.now())
                if learners.count() > learners_per_mentor:
                    learner_left = "count exceeds"
                elif learners.count() == learners_per_mentor:
                    learner_left = 0
                elif learners.count() < learners_per_mentor:
                    learner_left = learners_per_mentor - learners.count()
                learners_list = [{
                    "learner_id": learner.user.id,
                    "learner_name": f"{learner.user.first_name} {learner.user.last_name}",
                    "learner_email": learner.user.email
                } for learner in learners]
                mentor_list.append({
                    "mentor_id": mentor.id,
                    "mentor_name": f"{mentor.first_name} {mentor.last_name}",
                    "mentor_email": mentor.email,
                    "max_learner": ratio.learners_per_mentor,
                    "remaining_learner": learner_left,
                    "assigned_learner": learners.count(),
                    "learner_list": learners_list
                })
            response = {
                "message": "Mentor Matching Report",
                "success": True,
                "data": mentor_list,
                "joined_learner": learner_count,
                "max_learner": ratio.max_learner,
                "joined_mentor": mentor_count,
                "max_mentor": ratio.max_mentor,
                "joined_member": max_member,
                "max_member": ratio.max_member
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllUserSubscription(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        user_subscription = SubcribedUser.objects.filter(
            user=user, company__in=company, is_active=True, is_delete=False)
        if not user_subscription:
            return Response({"message": "You don't have any subscription", "success": True}, status=status.HTTP_200_OK)
        subscription_list = []
        for subs in user_subscription:
            mentor_mentee_ratio = MentorMenteeRatio.objects.filter(
                user_subscription=subs, is_active=True, is_delete=False).first()
            if not mentor_mentee_ratio:
                mentor_mentee_ratio = MentorMenteeRatio.objects.filter(
                    subscription=subs.subscription, is_active=True, is_delete=False).first()
            left_days = subs.end_date - aware_time(datetime.now())
            if subs.offer_applied:
                subscription_offer = SubscriptionOffer.objects.filter(subscription=subs.subscription).first()
            subscription_list.append({
                "id": subs.id,
                "company_id": subs.company.id,
                "company_name": subs.company.name,
                "title": subs.subscription.title,
                "subscription_id": subs.subscription.id,
                "description": subs.subscription.description,
                "terms_conditions": subs.subscription.terms_conditions,
                "price": subs.subscription.price,
                "currency": subs.subscription.currency,
                "duration": subs.subscription.duration,
                "duration_type": subs.subscription.duration_type,
                "sub_type": subs.subscription.sub_type,
                "left_days": left_days.days,
                "is_subscribed": subs.is_subscribed,
                "offer_applied": subs.offer_applied,
                "offer_title": subscription_offer.title if subs.offer_applied else '',
                "is_cancel": subs.is_cancel,
                "max_member": mentor_mentee_ratio.max_member if mentor_mentee_ratio else '',
                "max_mentor": mentor_mentee_ratio.max_mentor if mentor_mentee_ratio else '',
                "max_learner": mentor_mentee_ratio.max_learner if mentor_mentee_ratio else '',
                "learner_per_mentor": mentor_mentee_ratio.learners_per_mentor if mentor_mentee_ratio else '',
                "canceling_reason": subs.canceling_reason,
                "is_purchased": True if user_subscription else False,
                "valid_from": strf_format(local_time(subs.start_date)) if user_subscription else '',
                "valid_till": strf_format(local_time(subs.end_date)) if user_subscription else '',
                "created_at": strf_format(local_time(subs.created_at))
            })
        response = {
            "message": "All subscriptions list",
            "success": True,
            "data": subscription_list,
        }
        return Response(response, status=status.HTTP_200_OK)


class CheckForSubscription(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company = user_company(user, self.request.session.get('company_id'))
        user_subscription = SubcribedUser.objects.filter(
            user=user, is_active=True, is_delete=False, is_cancel=False, company__in=company)
        #print("user_subscription ", user_subscription.values())
        if not user_subscription:
            return Response({"message": "You don't have any subscription, click here to buy one!", "success": False, "css_class": "alert-danger"}, status=status.HTTP_200_OK)
        elif user_subscription.filter(end_date__lt=datetime.now()).exists():
            return Response({"message": "Your subscription is expired, click here to renew!", "success": False, "css_class": "alert-danger"}, status=status.HTTP_200_OK)
        left_days = user_subscription.first().end_date - aware_time(datetime.now())
        if left_days.days < 10:
            response = {
                "message": f"You're plan will be expired in {left_days} days, click here to renew!",
                "success": False,
                "css_class": "alert-warning"
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "No alert available", "success": True, "css_class": "alert-success"}, status=status.HTTP_200_OK)


class SubscribeFreeSubscription(APIView):
    def post(self, request, *args, **kwargs):

        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            subscription = Subscription.objects.get(pk=request.data['subscription_id'])
        except Subscription.DoesNotExist:
            return Response({"message": "Invalid Subscription Id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            company = Company.objects.get(pk=request.data["company_id"])
        except Company.DoesNotExist:
            return Response({"message": "Invalid Company Id", "success": False}, status=status.HTTP_404_NOT_FOUND)

        start_date = date.today()
        user_subscription = SubcribedUser.objects.filter(
            user=user, is_cancel=False, company=company).order_by('updated_at').last()
        if user_subscription:
            start_date = user_subscription.end_date + timedelta(days=1)
        subcribeUser = SubcribedUser.objects.create(
            user=user, subscription=subscription, company=company, is_subscribed=True, start_date=start_date)
        subcribeUser.subscription_end_time(start_date, subscription.duration, subscription.duration_type)
        response = {
            "message": "Congrations! You have successfully subscribed to the plan.",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class CompanySubcription(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            company = Company.objects.get(pk=self.kwargs['company_id'])
        except Company.DoesNotExist:
            return Response({"message": "Invalid company_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        subscriptions = SubcribedUser.objects.filter(user=user, company=company,
                                                     is_subscribed=True, is_active=True, is_delete=False, is_cancel=False)
        data = []
        for subs in subscriptions:
            data.append({
                "id": subs.id,
                "subscription_title": subs.subscription.title,
            })
        response = {
            "message": "All Subscriptions",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)


class MessageSchedulerView(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            company = Company.objects.get(pk=request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "Company no found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        msg_scheduler = MessageScheduler.objects.filter(company=company, is_active=True, is_delete=False)
        data = []
        for scheduler in msg_scheduler:
            data.append({
                "id": scheduler.id,
                "company": scheduler.company.name if scheduler.company else "",
                "journey": scheduler.journey.title if scheduler.journey else "",
                "journal": scheduler.journal.name if scheduler.journal else "",
                "title": scheduler.title,
                "start_date": scheduler.start_date,
                "end_date": scheduler.end_date,
                "scheduler_day": scheduler.day,
                "scheduler_time": scheduler.time,
                "receiver": scheduler.receiver,
                "receiver_platform": scheduler.receiver_platform,
                "scheduler_type": scheduler.scheduler_type,
                "message": scheduler.message,
                "created_at": scheduler.created_at,
                "updated_at": scheduler.updated_at,
                "is_active": scheduler.is_active,
                "is_delete": scheduler.is_delete,

            })
        response = {
            "message": "Message Scheduler List",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = MessageSchedulerSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                company = Company.objects.get(pk=request.data['company'])
            except Company.DoesNotExist:
                return Response({"message": "Company not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

            msg_scheduler = MessageScheduler.objects.create(day=request.data["scheduler_day"], time=request.data["scheduler_time"], receiver=request.data["receiver"], receiver_platform=request.data["receiver_platform"],
                                                            scheduler_type=request.data["scheduler_type"], company=company, message=request.data["message"], created_by=user, start_date=request.data["start_date"], end_date=request.data["end_date"], title=request.data["title"])
            if "journey_id" in request.data:
                try:
                    journey = Channel.objects.get(pk=request.data['journey_id'])
                    msg_scheduler.journey = journey
                    print("request.data[journal_id]", request.data["journal_id"])
                    journal = LearningJournals.objects.get(pk=request.data["journal_id"])
                    msg_scheduler.journal = journal
                    msg_scheduler.save()
                except Exception as e:
                    return Response({"message": "Journey or journal not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

            response = {
                "message": "Message Scheduler created successfully!",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)



class GroupChatMembersList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.request.query_params.get('user_id'))
        if not user:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            group_obj = AllRooms.objects.get(name=self.kwargs['room_id'])
        except AllRooms.DoesNotExist:
            return Response({"message": "Invalid room_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        
        member_list = []
        for member in group_obj.members.all():
            member_list.append({
                "id": member.id,
                "name": member.first_name + " " + member.last_name,
                "avatar": avatar(member),
                "is_admin": True if group_obj.group_admin.filter(id=member.id) else False
            })
        group_admin_list = []
        for admin in group_obj.group_admin.all():
            group_admin_list.append({
                "id": admin.id,
                "name": admin.first_name + " " + admin.last_name,
                "avatar": avatar(admin)
            })
        data = {
            "group_id": group_obj.name,
            "group_name": group_obj.group_name,
            "created_by": group_obj.created_by.first_name + " " + group_obj.created_by.last_name if group_obj.created_by else "",
            "created_by_id": group_obj.created_by.id if group_obj.created_by else "",
            "member_list": member_list,
            "group_admin_list": group_admin_list
        }
        response = {
            "message": "All Group Members",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)


class RemoveGroupChatMember(APIView):
    def post(self, request, *args, **kwargs):
        serializer = GroupChatMemberSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid user_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
            member = check_valid_user(request.data['member_id'])
            if not member:
                return Response({"message": "Invalid member_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                group_obj = AllRooms.objects.get(name=request.data['group_id'])
            except AllRooms.DoesNotExist:
                return Response({"message": "Invalid group_id", "success": False}, status=status.HTTP_404_NOT_FOUND)

            group_obj.members.remove(member)
            group_obj.save()

            response = {
                "message": "Group Member Removed Successfully!",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class AddGroupChatMember(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddGroupChatMemberSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid user_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                group_obj = AllRooms.objects.get(name=request.data['group_id'])
            except AllRooms.DoesNotExist:
                return Response({"message": "Invalid group_id", "success": False}, status=status.HTTP_404_NOT_FOUND)

            member_list = request.data['member_id_list']
            member_list = member_list.split(",")
            for member in member_list:
                if not group_obj.members.filter(id=member).exists():
                    group_obj.members.add(member)
            group_obj.save()


            response = {
                "message": "Group Members Added Successfully!",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class SendNotificationToMentionUser(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddGroupChatMemberSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid user_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                group_obj = AllRooms.objects.get(name=request.data['group_id'])
            except AllRooms.DoesNotExist:
                return Response({"message": "Invalid group_id", "success": False}, status=status.HTTP_404_NOT_FOUND)

            mention_member_list = request.data['member_id_list']
            # if not member:
            #     return Response({"message": "Invalid member_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            print("mention_member_list", mention_member_list)
            mention_member_list = mention_member_list.split(",")
            for mention_member in mention_member_list:
                print("mention_member", mention_member)
                member = User.objects.filter(id=mention_member).first()
                if member:
                    description = f"""Hi {member.first_name} {member.last_name}!
                    You were mentioned in {group_obj.group_name}"""

                    context = {
                        "screen":"Chat",
                    }
                    send_push_notification(member, 'Chat', description, context)
                    notify.send(member, recipient=member, verb=group_obj.group_name, description=f"{user.first_name} {user.last_name} mentioned you in {group_obj.group_name}")

            response = {
                "message": "Send Notification Successfully!",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class ManagerCalendar(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if 'timezone' in request.session:
            time_zone = self.request.session['timezone']
        elif 'timezone' in self.request.query_params:
            time_zone = self.request.query_params.get('timezone')
        else:
            return Response({"message": "Please specify timezone", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            userCompany = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        collaborates = Collabarate.objects.filter(is_active=True, is_cancel=False, company__in=[userCompany])

        data = []
        participant_list = []
        for collaborate in collaborates:
            if collaborate.type == "GroupStreaming":
                participant_list = [{"id": participant.id, "name": f"{participant.first_name} {participant.last_name}",
                                     "email": participant.email, "profile_image": avatar(participant)} for participant in collaborate.participants.all()]
            print("time", type(convert_to_local_time( collaborate.end_time, time_zone)), type(date.today()) )
            data.append({

                "id": collaborate.id,
                "title":  collaborate.title + "- Click here To start ",
                "start": convert_to_local_time( collaborate.start_time, time_zone).strftime("%Y-%m-%dT%H:%M:%S"),
                "end": convert_to_local_time( collaborate.end_time, time_zone).strftime("%Y-%m-%dT%H:%M:%S"),
                "allDay": False,
                "backgroundColor": '#3379FF',
                "borderColor": '#3379FF',
                "reminder": 0,
                "is_cancel":  collaborate.is_cancel,
                "call_type":  collaborate.type,
                "slot_status": "",
                "status": "",
                "participants": participant_list,
                "url":  collaborate.custom_url,
                "type": "collabarate",
                "created_by": f"{ collaborate.created_by.first_name} { collaborate.created_by.last_name}",
                "created_at": local_time( collaborate.created_at).isoformat(),
                "feedback_type": collaborate.type,
                "is_expired": True if convert_to_local_time( collaborate.end_time, time_zone).date() < date.today() else False,
                "is_assigned": False,
                "task_status": ""

            })
        response = {
            "message": "Manager Calendar List",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

class ReviewMentorForMarketPlace(APIView):

    def get(self, request, *args, **kwargs):
        company_id = self.request.query_params.get('company_id')
        if not check_valid_user(self.kwargs['user_id']):
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user = check_valid_user(self.kwargs['user_id'])
        is_admin = False
        # print("wsfewf", user.userType.all())
        if user.userType.filter(type='Admin'):
            is_admin = True

        mentor_list = Mentor.objects.filter(marketplace_status="In Review", is_active=True, is_archive=False, is_delete=False)
        
        if not is_admin:
            if not company_id:
                return Response({"message": "parameter company_id is required", "success": False}, status=status.HTTP_404_NOT_FOUND)
            company = user.company.filter(id=company_id)
            mentor_list = mentor_list.filter(company__in=company)
        review_mentor_list = []
        for mentor in mentor_list:
            market_place = MentorMarketPlace.objects.filter(user=mentor, is_active=True, is_delete=False).first()
            if market_place:
                review_mentor_list.append({
                    "id": mentor.id,
                    "name": mentor.get_full_name(),
                    "email": mentor.email,
                    "phone": str(mentor.phone),
                    "mentor_publish_on_marketplace": mentor.mentor_publish_on_marketplace,
                    "admin_publish_on_marketplace": mentor.admin_publish_on_marketplace,
                    "marketplace_status": mentor.marketplace_status,
                    "date_of_request": market_place.updated_at,
                    "marketplace_id": market_place.id
                })
        response = {
            "message": "Review Marketplace Mentor Request List",
            "review_mentor_list":review_mentor_list,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class ApproveRejectMarketplaceMentor(APIView):

    def post(self, request, *args, **kwargs):
        serializer = MentorApproveRejectSerializer(data=request.data)
        if serializer.is_valid():
            if not check_valid_user(self.kwargs['user_id']):
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentor_id = request.data['mentor_id']
            mentor_status = request.data['status']
            market_place = Mentor.objects.filter(id=mentor_id, is_active=True, is_delete=False, is_archive=False)
            mentor = market_place.first()
            market_place.update(marketplace_status=mentor_status)
            if mentor_status == 'Approved':
                if mentor.admin_publish_on_marketplace and mentor.mentor_publish_on_marketplace:
                    market_place.update(marketplace_status="Live")
                    
            else:
                subject = "Complete Your Mentor Profile on the Marketplace!"
                email_template_name = "email/marketplace_request_rejected.txt"

                c = {
                    'domain': DOMAIN,
                    'site_name': SITE_NAME,
                    'login_url': LOGIN_URL,
                    'info_contact_email': INFO_CONTACT_EMAIL,
                    "mentor_name": mentor.first_name + " " + mentor.last_name,
                }
                email_string = render_to_string(email_template_name, c)
                try:
                    send_mail(subject, email_string, 'info@growatpace.com', [mentor.email], fail_silently=False)
                except BadHeaderError:
                    return HttpResponse('Invalid header found.') 
        
            response = {
                "message": f"Mentor {mentor_status} Successfully",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

class MarketPlaceMentorList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        mentor_list = Mentor.objects.filter(company=company, is_active=True, is_delete=False, is_archive=False).order_by('-date_joined').distinct()

        market_mentor_list = [{
            "id": mentor.id,
            "name": mentor.get_full_name(),
            "username": mentor.username,
            "email": mentor.email,
            "phone": str(mentor.phone),
            "admin_publish_on_marketplace": mentor.admin_publish_on_marketplace,
            "mentor_publish_on_marketplace": mentor.mentor_publish_on_marketplace,
            "marketplace_status": mentor.marketplace_status
        }
            for mentor in mentor_list]
        response = {
            "message": f"Marketplace Mentor list",
            "data": market_mentor_list,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)
    
class CreateTask(APIView):
    model_class = ProgramManagerTask
    serializer_class = ProgramManagerTaskSerializer
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        company_id = self.request.query_params.get('company_id')
        company = user.company.filter(id=company_id).first()
        if not self.request.query_params.get('timezone'):
            return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        timezone = self.request.query_params.get('timezone')
        all_task = self.model_class.objects.filter(company=company)
        task_list = []
        for task in all_task:
            task_reminder = TaskRemainder.objects.filter(task=task).first()
            assign_to = AssignTaskToUser.objects.filter(task=task, is_assigned=True, is_delete=False, is_revoked=False)
            assign_to_list = [{"name": assign_to_user.assigned_to.get_full_name(), "user_id": assign_to_user.assigned_to.id, "id": assign_to_user.id}
                                 for assign_to_user in assign_to]
            assign_to_user = assign_to.filter(assigned_to=user).first()
            task_list.append({
                "id": task.id,
                "title": task.title,
                "company_id": task.company.id,
                "company_name": task.company.name,
                "description": task.description,
                "is_recurring": task.is_recurring,
                "recurring_time": task.recurring_times,
                "set_remainder": task.set_remainder,
                "remainder_time": task_reminder.remainder_time if task_reminder else '',
                "reminder_before": task_reminder.remainder_before if task_reminder else '',
                "start": convert_to_local_time(task.start_time, timezone),
                "end": convert_to_local_time(task.due_time, timezone),
                "created_by": task.created_by.get_full_name(),
                "call_type": "",
                "type": "task",
                "url": "",
                "backgroundColor": "",
                "borderColor": "",
                "is_expired": "",
                "assign_to": assign_to_list,
                "start_time": strf_format(convert_to_local_time(task.start_time, timezone)),
                "end_time": strf_format(convert_to_local_time(task.due_time, timezone)),
                "is_assigned": True if assign_to_user else False,
                "task_status": assign_to_user.task_status if assign_to_user else "",
            }) 
        response = {
            "message": "All Task Data",
            "success": True,
            "data": task_list
        }
        return Response(response, status=status.HTTP_200_OK)

    
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            if not data.get('company_id'):
                return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            company_id = data.get('company_id')
            company = user.company.filter(id=company_id).first()
            if not data.get('timezone'):
                return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            timezone = data.get('timezone')
            title = request.data['title']
            description = request.data['description']
            is_recurring = update_boolean(request.data['is_recurring'])
            set_remainder = update_boolean(request.data['set_remainder'])
            start_time = convert_to_utc(request.data['start_time'].replace('T',' ')+":00", timezone)
            due_time = convert_to_utc(request.data['due_time'].replace('T',' ')+":00", timezone)
            task = self.model_class.objects.create(company=company, title=title, description=description, is_recurring=is_recurring, start_time=start_time, created_by=user,
                                     set_remainder=set_remainder, due_time=due_time)
            if is_recurring:
                task.recurring_times = request.data['recurring_time']

            if set_remainder:
                reminder_before = request.data['reminder_before']
            task.save()
            if set_remainder:
                task_reminder = TaskRemainder.objects.create(task=task, remainder_before=reminder_before)
            
            if data.get('assign_to'):
                assign_to_list = data.get('assign_to').split(",")
                for assign_to in assign_to_list:
                    assign_to_user = User.objects.get(pk=assign_to)
                    AssignTaskToUser.objects.create(task=task, assigned_to=assign_to_user, assigned_by=user, is_assigned=True)

                    subject = "Task Assigned"
                    email_template_name = "email/assign_task.txt"

                    c = {
                        'domain': DOMAIN,
                        'site_name': SITE_NAME,
                        "user": assign_to_user.first_name + " " + assign_to_user.last_name,
                        "manager": user.first_name + " " + user.last_name,
                        "task_name": task.title,
                        "start_time": convert_to_local_time(task.start_time, timezone),
                        "description": task.description
                    }
                    email_string = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email_string, 'info@growatpace.com', [assign_to_user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.') 

                    message = f"""
                        Hello,\n
                        Your Program team has assign a task to you\n\n
                        Task: {task.title}\n
                        By: {user.first_name} {user.last_name}\n
                        Regards,\n
                        Program Team
                    """

                    room = get_chat_room(user, assign_to_user)
                    room = AllRooms.objects.get(name=room)
                    chat = Chat.objects.create(from_user=user, to_user=assign_to_user, message=message, room=room)
                    print(f"in app chat: {chat.to_user}")
                    

            response = {
                "message": "Task created successfully",
                "success": True,
                "task_id": task.id
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateTask(APIView):
    model_class = ProgramManagerTask
    serializer_class = ProgramManagerTaskSerializer
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        company_id = self.request.query_params.get('company_id')
        company = user.company.filter(id=company_id).first()
        if not self.request.query_params.get('timezone'):
            return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        timezone = self.request.query_params.get('timezone')
        try:
            task = self.model_class.objects.get(id=self.kwargs['task_id'])
        except ProgramManagerTask.DoesNotExist:
            return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        task_reminder = TaskRemainder.objects.filter(task=task).first()
        assign_to = AssignTaskToUser.objects.filter(task=task, is_assigned=True, is_delete=False, is_revoked=False)
        assign_to_list = [{"name": assign_to_user.assigned_to.get_full_name(), "user_id": assign_to_user.assigned_to.id, "id": assign_to_user.id}
                                 for assign_to_user in assign_to]
        data = {
            "id": task.id,
            "title": task.title,
            "company_id": task.company.id,
            "company_name": task.company.name,
            "description": task.description,
            "is_recurring": task.is_recurring,
            "recurring_time": task.recurring_times,
            "set_remainder": task.set_remainder,
            "remainder_time": task_reminder.remainder_time if task_reminder else '',
            "reminder_before": task_reminder.remainder_before if task_reminder else '',
            "start": convert_to_local_time(task.start_time, timezone),
            "end": convert_to_local_time(task.due_time, timezone),
            "created_by": task.created_by.get_full_name(),
            "call_type": "",
            "type": "task",
            "url": "",
            "backgroundColor": "",
            "borderColor": "",
            "is_expired": "",
            "assign_to":assign_to_list
        }
        response = {
            "message": "Get Task",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            if not data.get('company_id'):
                return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                company = user.company.get(id=data.get('company_id'))
            except:
                return Response({"message": "company_id is not valid", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            if not data.get('timezone'):
                return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                task = self.model_class.objects.get(id=self.kwargs['task_id'])
            except:
                return Response({"message": "Task not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

            start_time = request.data['start_time'].replace('T',' ')
            due_time = request.data['due_time'].replace('T',' ')
            try:
                datetime.strptime(request.data['start_time'],  "%Y-%m-%dT%H:%M:%S")
            except:
                start_time = request.data['start_time'].replace('T',' ')+":00"
                
            try:
                datetime.strptime(request.data['due_time'],  "%Y-%m-%dT%H:%M:%S")
            except:
                due_time = request.data['due_time'].replace('T',' ')+":00"

            is_recurring = update_boolean(request.data['is_recurring'])
            set_reminder = update_boolean(request.data['set_remainder'])
            task.company = company
            task.title = request.data['title']
            task.description = request.data['description']
            task.is_recurring = is_recurring
            task.start_time = convert_to_utc(start_time, data.get('timezone'))
            task.created_by = user
            if is_recurring:
                task.recurring_times = request.data['recurring_time']
            else:
                task.recurring_times = ""
            
            task.set_remainder = update_boolean(request.data['set_remainder'])
            task.due_time = convert_to_utc(due_time, data.get('timezone'))
            task.save()
            task_user = AssignTaskToUser.objects.filter(task=task, is_assigned=True, is_revoked=False)
            task_user.update(is_revoked=True, revoked_by = user)
            if data.get('assign_to'):
                assign_to_list = data.get('assign_to').split(",")
                for assign_to in assign_to_list:
                    assign_to_user = User.objects.get(pk=assign_to)
                    assign_task_to_user_obj = AssignTaskToUser.objects.filter(task=task, assigned_to=assign_to_user).first()
                    if assign_task_to_user_obj:
                        assign_task_to_user_obj.is_revoked = False
                        assign_task_to_user_obj.is_assigned = True
                        assign_task_to_user_obj.assigned_by = user
                        assign_task_to_user_obj.save()
                    else:
                        AssignTaskToUser.objects.create(task=task, assigned_to=assign_to_user, assigned_by=user, is_assigned=True)

                    subject = "Task Updated"
                    email_template_name = "email/updated_calendar_task.txt"

                    c = {
                        'domain': DOMAIN,
                        'site_name': SITE_NAME,
                        "user": assign_to_user.first_name + " " + assign_to_user.last_name,
                        "manager": user.first_name + " " + user.last_name,
                        "task_name": task.title,
                        "start_time": convert_to_local_time(task.start_time, data.get('timezone')),
                        "description": task.description
                    }
                    email_string = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email_string, 'info@growatpace.com', [assign_to_user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.') 

                    message = f"""
                        Hello,\n
                        Your Program team has updated a task that has assigned to you\n\n
                        By: {user.first_name} {user.last_name}\n
                        Task: {task.title}\n
                        Regards,\n
                        Program Team
                    """

                    room = get_chat_room(user, assign_to_user)
                    room = AllRooms.objects.get(name=room)
                    chat = Chat.objects.create(from_user=user, to_user=assign_to_user, message=message, room=room)
                    print(f"in app chat: {chat.to_user}")
            
            if set_reminder:
                task_reminder = TaskRemainder.objects.filter(task=task)
                if task_reminder.exists():
                    task_reminder.update(remainder_before=request.data['reminder_before'])
                else:
                    TaskRemainder.objects.create(task=task, remainder_before=request.data['reminder_before'])
            else:
                task_reminder = TaskRemainder.objects.filter(task=task)
                if task_reminder.exists():
                    task_reminder.update(remainder_before=0)
                    

            
            response = {
                "message": "Task created successfully",
                "success": True,
                "task_id": task.id
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

class AssignTask(APIView):
    serializer_class = AssignTaskSerializer
    model_class = AssignTaskToUser
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():  
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            task = ProgramManagerTask.objects.filter(id=request.data['task_id'])
            if not task.exists():
                return Response({"message": "Task not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            task = task.first()
            assign_to = request.data['assign_to']
            assign_to_user = User.objects.filter(id=assign_to).first()
            is_assigned = update_boolean(request.data['is_assigned'])
            if not assign_to_user:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            assign_task = self.model_class.objects.filter(task=task, assign_to=assign_to_user, is_assigned=is_assigned)
            if assign_task.exists():
                return Response({"message": "Task already assigned", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            assign_task = self.model_class.objects.create(task=task, assign_to=assign_to_user, assign_by=user, is_assigned=is_assigned)
            response = {
                "message": "Task assigned successfully",
                "success": True,
                "task_id": assign_task.id
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

class RevokeTask(APIView):
    model_class = AssignTaskToUser
    serializer_class = RevokeTaskSerializer
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            is_revoked = update_boolean(request.data['is_revoked'])
            revoke_to_user = User.objects.filter(id=request.data['revoke_to']).first()
            if not revoke_to_user:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            revoke_task = self.model_class.objects.filter(
                id=request.data['user_task_id'], is_revoked=is_revoked, assign_to=revoke_to_user)
            if revoke_task.exists():
                return Response({"message": "Task already revoked", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            
            is_assigned = True
            assign_task = self.model_class.objects.filter(id=request.data['user_task_id'], is_assigned=is_assigned, assign_to=revoke_to_user)
            
            if not assign_task.exists():
                return Response({"message": "Task not assigned", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            revoke_task.update(is_revoked=is_revoked, revoked_by=user, is_assigned=False)
            response = {
                "message": "Task revoked successfully",
                "success": True,
                "task_id": revoke_task.id
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
    
class TaskList(APIView):
    permission_classes = [AllowAny]
    def get(self,request, *args, **kwargs):
        qp_data = request.query_params

        if not qp_data.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=qp_data.get('company_id'))
        except:
            return Response({"message": "company_id is not valid", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        if not qp_data.get('timezone'):
            return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)

        assigned_to = self.kwargs.get('user_id', None)
        if not User.objects.filter(id=assigned_to).exists():
            return Response({'message':'User does not exist', 'success': False}, status.HTTP_400_BAD_REQUEST)

        timezone = qp_data.get('timezone')

        assign_task_list = []

        assign_task_data = AssignTaskToUser.objects.filter(assigned_to=assigned_to, is_active=True, is_delete=False, is_revoked=False, task__company=company, task__is_active=True, task__is_delete=False)
        for task_data in assign_task_data:
            start_time = convert_to_local_time(task_data.task.start_time, timezone)
            end_time = convert_to_local_time(task_data.task.due_time, timezone)
            assign_task_list.append({
                "id": task_data.task.id,
                "title": task_data.task.title,
                "description": task_data.task.description,
                "start_time": start_time,
                "end_time": end_time,
                "start": start_time,
                "end": end_time,
                "url": "",
                "reminder": "",
                "is_cancel": "",
                "call_type": "",
                "slot_status": "",
                "task_status": task_data.task_status,
                "bookmark": False,
                "created_at": local_time(task_data.created_at).isoformat(),
                "mentor": "",
                "mentor_name": "",
                "mentor_avatar": "",
                "backgroundColor":"#3379FF",
                "borderColor":"#3379FF",
                "feedback_type":"",
                "type": "task",
                "is_recurring": task_data.task.is_recurring,
                "recurring_time": task_data.task.recurring_times,
            })

        return Response({'message':'success', 'success':False, 'data':assign_task_list}, status.HTTP_200_OK)
   

class UpdateTaskStatus(APIView):
    serializer_class = UpdateTaskStatusSerializer
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():  
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                task = ProgramManagerTask.objects.get(id=request.data['task_id'])
            except ProgramManagerTask.DoesNotExist:
                return Response({"message": "Task not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try: 
                assign_task = AssignTaskToUser.objects.get(task=task, assigned_to=user, is_assigned=True, is_revoked=False, is_active=True, is_delete=False)
            except AssignTaskToUser.DoesNotExist:
                return Response({"message": "Task is not assigned to the user", "success": False}, status=status.HTTP_404_NOT_FOUND)

            comment = request.data['comment']
            task_status = request.data['task_status']
            updated_on = datetime.now(timezone.utc)
            assign_task.comment = comment
            assign_task.task_status = task_status
            assign_task.status_updated_on = updated_on
            assign_task.save()


            response = {
                "message": "Task status updated successfully",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'message': error_message(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
class AssigneeTaskStatusList(APIView):
    def get(self, request, *args, **kwargs):
        qp_data = request.query_params

        try:
            task = ProgramManagerTask.objects.get(id=self.kwargs['task_id'])
        except ProgramManagerTask.DoesNotExist:
            return Response({"message": "Task not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

        if not qp_data.get('user_id'):
            return Response({"message": "user_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=qp_data.get('user_id'))
        except:
            return Response({"message": "user_id is not valid", "success": False}, status=status.HTTP_400_BAD_REQUEST)

        if not qp_data.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = user.company.get(id=qp_data.get('company_id'))
        except:
            return Response({"message": "company_id is not valid", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        if not qp_data.get('timezone'):
            return Response({"message": "timezone is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        timezone = qp_data.get('timezone')
        assignee_task_list = []

        assignee_task_data = AssignTaskToUser.objects.filter(task=task, task__company=company, is_active=True, is_delete=False, is_revoked=False, is_assigned=True)
        for task_data in assignee_task_data:
            assignee_task_list.append({
                "task": task_data.task.title,
                "task_id": task_data.task.id,
                "assigned_to": task_data.assigned_to.get_full_name(),
                "assigned_to_id": task_data.assigned_to.id,
                "assigned_by": task_data.assigned_by.get_full_name(),
                "assigned_by_id": task_data.assigned_by.id,
                "task_status": task_data.task_status,
                "status_updated_on": strf_format(convert_to_local_time(task_data.status_updated_on, timezone)),
                "comment": task_data.comment
            })

        return Response({'message':'success', 'success':True, "data":assignee_task_list }, status.HTTP_200_OK)


class CompanyAllUsers(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            company = Company.objects.get(pk=self.kwargs['company_id'])
        except Company.DoesNotExist:
            return Response({"message": "Company not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

        users = company.company.all()
        user_list = [{"id": student.id, "name": f"{student.first_name} {student.last_name}",
                      "user_type": ", ".join(str(type.type) for type in student.userType.all()),
                      "email": student.email}
                     for student in users]

        response = {
            "message": "Company Users list",
            "success": True,
            "user_list": user_list,
        }
        return Response(response, status=status.HTTP_200_OK)

class JourneyCompletedUsers(APIView):
    def get(self, request, *args, **kwargs):

        channel_id = request.query_params['channel_id']
        user_type = request.query_params['user_type']

        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message":"User does not exist", "success":False}, status.HTTP_400_BAD_REQUEST)
        
        try:
            channel = Channel.objects.get(pk=channel_id)
        except Channel.DoesNotExist:
            return Response({"message":"Journey does not exist", "success":False}, status.HTTP_400_BAD_REQUEST)
        
        user_channel = UserChannel.objects.filter(Channel=channel, user__userType__type=user_type)
        # user_channel = UserChannel.objects.filter( ~Q(user=user), Channel=channel, is_completed=True)
        info = []
        
        for uc in user_channel:
            info.append({"user_id":uc.user.id ,"name": uc.user.get_full_name(), "channel":uc.Channel.title, "channel_id":uc.Channel.id, "is_completed": uc.is_completed, "email":uc.user.email, "user_type":user_type})
        
        return Response({"message":"success", "data":info}, status.HTTP_200_OK)

class GenerateCertandMail(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        print("DATA", data)
        end_userid = data['end_userid']
        channel_id = data['channel_id']
        user_type_role = data['user_type']

        try:
            certificate_template = CertificateTemplate.objects.get(journey__id=channel_id)
        except CertificateTemplate.DoesNotExist:
            return Response({"message":"Certificate template does not exist", "success":False}, status.HTTP_400_BAD_REQUEST)
        
        user = check_valid_user(self.kwargs['user_id'])
        end_user = check_valid_user(end_userid)

        if not (user or end_user) :
            return Response({"message":"User does not exist", "success":False}, status.HTTP_400_BAD_REQUEST)
        
        try:
            channel = Channel.objects.get(pk=channel_id)
        except Channel.DoesNotExist:
            return Response({"message":"Journey does not exist", "success":False}, status.HTTP_400_BAD_REQUEST)

        # file_url = CheckEndOfJourney(end_user, channel.pk, False)
        file_url = generate_certificate(end_userid, end_user.get_full_name(), channel_id, user_type_role=user_type_role)
        
        if file_url:
            with open(f'static/{end_userid}.png', 'wb') as f:
                r = requests.get(file_url.split('?')[0])
                f.write(r.content)  

            # try: send_certificate_email_by_manager("sarvesh@growatpace.com", end_user.get_full_name(), channel.title, end_userid)
            try: send_certificate_email_by_manager(end_user.email, end_user.get_full_name(), channel.title, end_userid)
            except Exception as e: 
                print("EXCEPTION", e)
                return Response({"message":"email was not sent", "success":False}, status.HTTP_400_BAD_REQUEST)
            
            # try: os.remove(f'static/{end_userid}.png')
            # except: print("File not deleted")
            return Response({"message":"certificate sent on email", "success":True}, status.HTTP_200_OK)
        else: 
            return Response({"message":"The certificate url is none, the might not have completed journey", "success":False}, status.HTTP_400_BAD_REQUEST)


