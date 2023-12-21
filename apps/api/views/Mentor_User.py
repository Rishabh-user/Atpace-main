import pytz
from datetime import datetime, date
import asyncio
from apps import api
from apps.api.views.views import JourneyAllPost
from apps.content.utils import company_journeys
from apps.leaderboard.views import send_push_notification
from apps.utils.utils import url_shortner
from ravinsight.web_constant import BASE_URL
from rest_framework import status
from datetime import datetime
from apps.api.serializers import AddEventSerializer, RemoveGroupMembersSerializer, SubmitProfileAssessmentSerilizer, ChatMessageSerializer, DeleteEventSerializer, LearningJournalPostCommentSerializer, MentorsScheduedSessionSerializer, MentorCalendarSerializer, EditJournalSerializer, UpdateEventSerializer, CreateChatGroupSerializer, CreateJournalSerializer, EditJournalCommentSerializer
from apps.api.utils import AsyncIter, chat_notification, room_members, update_boolean
from apps.users.templatetags.dashboard import get_weekly_journal, mentor_journeys, today_sessions, total_mentee, total_sessions
from apps.users.models import Collabarate, Company, ProfileAssestQuestion, User, Mentor, UserProfileAssest, UserTypes
from apps.content.models import Channel, ChannelGroup,  MentoringJourney, Content, UserChannel, UserCourseStart, TestAttempt
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.mentor.models import AssignMentorToUser, PoolMentor, mentorCalendar
from apps.community.models import LearningJournals, WeeklyLearningJournals, LearningJournalsComments, LearningJournalsAttachment
from apps.survey_questions.models import Survey, SurveyAttempt
from apps.test_series.models import TestSeries
from apps.atpace_community.utils import avatar, post_comment_file, post_comment_images, group_avatar, strf_format
from apps.chat_app.models import Chat, Room as AllRooms
from django.db.models.query_utils import Q
from apps.users.templatetags.tags import get_chat_room
from apps.users.utils import local_time, send_update_booking_mail, convert_to_local_time, convert_to_utc
from cgitb import text
import json
from channels.generic.websocket import AsyncWebsocketConsumer
# from apps.chat_app.models import Chat, Room as AllRooms
from apps.users.models import User
from apps.vonage_api.utils import send_chat_info
import random
import string
from channels.db import database_sync_to_async
import base64
from django.core.files.base import ContentFile
from rest_framework.permissions import AllowAny
from apps.atpace_community.utils import replace_links_with_anchor_tags
import re

utc = pytz.UTC

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        # # print("Websocket connected")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code,):
        # # print("Websocket disconnected", close_code)
        # Leave room group
        result = await database_sync_to_async(self.update_status)()
        # # print(result)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):

        if 'msg_type' in text_data:
            data = json.loads(text_data)
        else:
            data = {
                "message": text_data,
                "msg_type": "TEXT"
            }

        from_user_id = self.scope['url_route']['kwargs']['uuid']
        room_name = self.scope['url_route']['kwargs']['room_name']

        my_room = await database_sync_to_async(AllRooms.objects.get)(name=room_name)
        from_user = await database_sync_to_async(User.objects.get)(pk=from_user_id)

        file_name = ""
        imgdata = ""
        msg_type = data['msg_type']

        if msg_type == 'TEXT':
            message = data['message']
            # message = replace_links_with_anchor_tags(message) if ('<p>http' in message) or (re.search("(^https?://[^\s]+)", message)) else message
            message = replace_links_with_anchor_tags(message)
            response = {
                'type': 'chat_message',
                'message' : message,
                'file_url': '', 
                'file_name': '', 
                'msg_type': 'TEXT',
                'user_id': str(from_user_id),
                "from_user": from_user.first_name + " " + from_user.last_name
            }
        else:
            file_name = data['file_name']
            message = "test"
            file_content = data['file_content']
            fileType = data['file_type']
            file_data = f'data:{fileType};base64,{file_content}'
            response = {
                'type': 'chat_message',
                'message': '',
                'file_url': file_data, 
                'file_name': file_name, 
                'msg_type': msg_type,
                'user_id': str(from_user_id),
                "from_user": from_user.first_name + " " + from_user.last_name
            }

            format, imgstr = file_data.split(';base64,') 
            ext = format.split('/')[-1] 
            print("ext", ext, file_name, format)

            imgdata = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)        

        if my_room.type == "OneToOne":
            to_user = await database_sync_to_async(User.objects.get)(pk=my_room.user2_id)

            if to_user.id == from_user.id:
                to_user = await database_sync_to_async(User.objects.get)(pk=my_room.user1_id)

            result = await database_sync_to_async(self.check_status)(to_user)

            if (result == False):

                description = f"""Hi {to_user.get_full_name()}!
                You have received a message from {from_user.first_name} {from_user.last_name}."""

                await chat_notification(to_user, description, my_room)
                
            chat = Chat(
                from_user=from_user,
                to_user=to_user,
                message=message,
                msg_type = msg_type,
                file = imgdata,
                file_name = file_name
            )
        else:

            await database_sync_to_async(self.send_notification_to_group_member)(my_room, from_user)

            chat = Chat(
                from_user=from_user,
                message=message,
                room=my_room,
                msg_type = msg_type,
                file = imgdata,
                file_name = file_name
            )

        my_room.updated_at = datetime.now()
        await database_sync_to_async(my_room.save)()

        await database_sync_to_async(chat.save)()

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            response
        )

    def get_rooms(self):
        all_rooms = AllRooms.objects.get(name="mentoruser")
        # # # print(all_rooms, "line 72")
        return all_rooms

    def update_status(self):
        logged_user = self.scope['user'].id
        # # # print(logged_user)
        user = User.objects.get(pk=logged_user)
        # # # print("user_status1", user.user_status)
        user.user_status = False
        user.save()
        # # # print("user_status2", user.user_status)
        return "True"

    def check_status(self, to_user):
        user = User.objects.get(pk=to_user.id)
        # # # print(user.user_status)
        return user.user_status

    #Get all group members and send push notification
    def send_notification_to_group_member(self, room, from_user):
        members = room.members.filter(~Q(pk=from_user.id))
        for member in members:
            print("memebr", member)
            result = self.check_status(member)
            # result = await database_sync_to_async(self.check_status)(member)
            print("result", result)
            if (result == False):
                print("inside fun")

                unread_count = Chat.objects.filter(~Q(read_by__in=[member]), room=room).count()
                print("unread", unread_count)

                description = f"""Hi {member.get_full_name()}!
                You have {unread_count} in {room.group_name}"""

                print("description", description)
                context = {
                    "screen":"ChatScreen"
                }

                send_push_notification(member, 'New Message Received', description, context)
        return True

    # Receive message from room group

    async def chat_message(self, event):
        message = event['message']
        user_id = event['user_id']
        from_user = event['from_user']
        file_url = event['file_url']
        file_name = event['file_name']
        msg_type = event['msg_type']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'file_url':file_url,
            'file_name':file_name,
            'msg_type': msg_type,
            'type':msg_type,
            'sender_user_id': user_id,
            'sender_user': from_user,
        }))


class MentorMentees(APIView):
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        type = UserTypes.objects.get(type="Mentor")
        # # # print(self.kwargs['mentor_id'])
        # # # print(type)
        try:
            user = User.objects.get(id=self.kwargs['mentor_id'], userType=type)
            # # # print(user)
        except User.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        mentees = AssignMentorToUser.objects.filter(mentor=user, is_assign=True, is_revoked=False, journey__company=company, journey__closure_date__gt=datetime.now())
        data = []
        mentor_details = {
            "full_name": f"{user.first_name} {user.last_name}",
            "user_id": user.id,
            "username": user.username,
            "user_profile_image": user.avatar.url,
            "user_profile_heading": user.profile_heading,
        }
        # # # print(mentees)
        for mentee in mentees:
            data.append({
                "mentee_name": f"{mentee.user.first_name} {mentee.user.last_name}",
                "mentee_id": mentee.user.id,
                "mentee_profile_heading": mentee.user.profile_heading,
                "mentee_profile_image": mentee.user.avatar.url,
                "mentee_username": mentee.user.username,
                "mentee_email": mentee.user.email,
                "mentee_phone": str(mentee.user.phone),
                "mentee_current_status": mentee.user.current_status,
                "mentee_status": mentee.user.user_status,
                "mentee__type": ", ".join(str(type.type) for type in mentee.user.userType.all()),
                "journey_name": mentee.journey.title,
                "journey_id": mentee.journey.id,
                "assign_by": mentee.assign_by.first_name,
                "is_assign": mentee.is_assign,
                "is_revoked": mentee.is_revoked,
                "revoked_by": mentee.revoked_by.first_name if mentee.revoked_by else ''
            })
        # # # print("data",data)
        response = {
            "success": True,
            "data": "mentees/coachees data",
            "mentor_details": mentor_details,
            "mentee_details": data
        }
        # # # print("response",response)
        return Response(response, status=status.HTTP_200_OK)


class MentorAllotedJourneys(APIView):
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_type = UserTypes.objects.get(type="Mentor")
        # # print(user_type)
        try:
            user = User.objects.get(id=self.kwargs['mentor_id'], userType=user_type)
        except User.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        journey = Channel.objects.filter(Q(is_global=True) | Q(company=company), closure_date__gt=datetime.now(),
                                      parent_id=None, is_active=True, is_delete=False)
        journeys = PoolMentor.objects.filter(pool__journey__in=journey,
            mentor=user, pool__journey__is_active=True, pool__journey__is_delete=False)
        journey_id_list = []
        # print("journeys ",journeys)
        data = []
        if journeys:
            for journey in journeys:
                if journey.pool.journey.id not in journey_id_list:
                    # print("journey.pool.journey.id ",journey.pool.journey.id)
                    data.append({
                        "journey_id": journey.pool.journey.id,
                        "title": journey.pool.journey.title,
                        "color": journey.pool.journey.color,
                        "pools": journey.pool.name,
                        "category": journey.pool.journey.category.category if journey.pool.journey.category else '',
                        "type": journey.pool.journey.channel_type,
                        "short_description": journey.pool.journey.short_description,
                        "company": journey.pool.company.name if journey.pool.company else '',
                        "is_active": journey.pool.journey.is_active,
                        "duration": "2 Week",
                        "tags": journey.pool.journey.tags.split(",")
                    })
                journey_id_list.append(journey.pool.journey.id)
        else:
            journeys = UserChannel.objects.filter(~Q(Channel__channel_type='SelfPaced'), user=user, Channel__closure_date=datetime.now(), Channel__company=company, is_completed=False, status='Joined', is_removed=False)
            # # print("journeys", journeys)
            for journey in journeys:
                data.append({
                    "journey_id": journey.Channel.id,
                    "title": journey.Channel.title,
                    "color": journey.Channel.color,
                    "pools": '',
                    "category": journey.Channel.category.category if journey.Channel.category else '',
                    "type": journey.Channel.channel_type,
                    "short_description": journey.Channel.short_description,
                    "company": journey.Channel.company.name if journey.Channel.company else '',
                    "is_active": journey.Channel.is_active,
                    "duration": "2 Week",
                    "tags": journey.Channel.tags.split(",")
                })
        response = {
            "success": True,
            "data": "mentor alloted journeys",
            "mentor_id": user.id,
            "journey_details": data
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorsScheduedSession(APIView):
    def post(self, request):
        data = request.data
        # # print(data)
        serializer = MentorsScheduedSessionSerializer(data=data)
        user_type = UserTypes.objects.get(type="Mentor")
        # # print(user_type)
        if serializer.is_valid():
            try:
                company = Company.objects.get(id=request.data['company_id'])
            except Company.DoesNotExist:
                return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                mentor = Mentor.objects.get(pk=request.data['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            sessions = mentorCalendar.objects.filter(mentor=mentor, mentor__company=company, is_cancel=False)
            mettings = Collabarate.objects.filter(speaker=mentor, company=company, is_cancel=False)
            all_mettings = []
            for meeting in mettings:
                participant_list = [
                    f"{participant.first_name} {participant.last_name}" for participant in meeting.participants.all()]
                all_mettings.append({
                    "id": meeting.id,
                    "title": meeting.title,
                    "description": meeting.description,
                    "start_time": convert_to_local_time(meeting.start_time, self.request.data['timezone']),
                    "end_time": convert_to_local_time(meeting.end_time, self.request.data['timezone']),
                    "url": meeting.custom_url,
                    "reminder": "",
                    "is_cancel": meeting.is_cancel,
                    "call_type": meeting.type,
                    "slot_status": "",
                    "status": "",
                    "bookmark": "",
                    "created_at": local_time(meeting.created_at).isoformat(),
                    "mentor": f"{meeting.speaker.first_name} {meeting.speaker.last_name}",
                    "mentor_name": participant_list,
                    "mentor_avatar": meeting.speaker.avatar.url,
                })

            all_list = sessions.filter(start_time__gte=datetime.now())
            all_mettings.extend(MentorCalendarSerializer(all_list, many=True).data)
            response = {
                "message": "Success",
                "success": True,
                "data": all_mettings
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class MentorDashboard(APIView):
    def get(self, request, *args, **kwargs):
        try:
            mentor = Mentor.objects.get(pk=self.kwargs['mentor_id'])
        except Mentor.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "my_journeys": mentor_journeys(mentor),
            "total_mentee_learner": total_mentee(mentor),
            "today_sessions": today_sessions(mentor),
            "total_scheduled_sessions": total_sessions(mentor),
            "all_weekly_journals": get_weekly_journal(mentor).count(),
        }
        response = {
            "message": "Success",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorCalendar(APIView):
    def get(self, request, *args, **kwargs):
        user_type = UserTypes.objects.get(type="Mentor")
        # # print(user_type)
        timezone = request.query_params.get('timezone', None)
        if timezone is None:
            return Response({"message": "timezone is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        elif timezone == "undefined":
            return Response({"message": "Please Update Your Application",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=self.kwargs['mentor_id'], userType=user_type)
        except User.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        company_list = user.company.all()
        pool_mentor = PoolMentor.objects.filter(mentor=user, pool__journey__closure_date__gt=datetime.now())
        journey_list = [pool.pool.journey.id for pool in pool_mentor]
        mentor_calendar = mentorCalendar.objects.filter(mentor=user, is_cancel=False)
        calendar_data = []
        backgroundColor = "#33FF4F"
        borderColor = "#33FF4F"
        for mentor_calendar in mentor_calendar:
            current_time = utc.localize(datetime.combine(datetime.now(), datetime.min.time()))
            current_time = convert_to_local_time(current_time, timezone)
            if mentor_calendar.is_cancel and mentor_calendar.slot_status == "Booked":
                call_status = "Cancelled"
            elif (not mentor_calendar.is_cancel and mentor_calendar.slot_status == "Booked") and (mentor_calendar.end_time > current_time):
                call_status = "Upcoming"
            elif (not mentor_calendar.is_cancel and mentor_calendar.slot_status == "Booked") and (mentor_calendar.end_time < current_time):
                call_status = "Completed"
            elif mentor_calendar.slot_status == "Available":
                call_status = ""
            participants = []
            title = mentor_calendar.title
            backgroundColor = "#33FF4F"
            borderColor = "#33FF4F"
            if mentor_calendar.slot_status == "Booked":
                backgroundColor = "#3379FF"
                borderColor = "#3379FF"
                title = f"{mentor_calendar.title} - Click here To start "
                participants = [{"participant_name": f"{participant.first_name} {participant.last_name}", "participant_id": participant.id,
                                 "participant_avatar": avatar(participant)} for participant in mentor_calendar.participants.all()]

            calendar_data.append({
                "id": mentor_calendar.id,
                "title": title,
                "start":  convert_to_local_time(mentor_calendar.start_time, timezone),
                "end": convert_to_local_time(mentor_calendar.end_time, timezone),
                "allDay": False,
                "reminder": 0,
                "is_cancel": mentor_calendar.is_cancel,
                "call_type": mentor_calendar.call_type,
                "slot_status": mentor_calendar.slot_status,
                "status": call_status,
                "backgroundColor": backgroundColor,
                "borderColor": borderColor,
                "url": mentor_calendar.url,
                "participants": participants,
                "type": "One To One",
                "created_by": mentor_calendar.created_by,
                "created_at": mentor_calendar.created_at,
                "feedback_type":"MentorCall",
                "is_speaker": False
            })
        Collabarate_data = []
        # all_mettings = Collabarate.objects.filter(Q(speaker=request.user) | Q(
        #     company__in=company_list) | Q(participants__in=[request.user]), is_cancel=False, journey__in=journey_list)
        all_mettings = Collabarate.objects.filter(Q(speaker=request.user) | Q(participants__in=[request.user]), company=company, is_active=True, is_cancel=False).distinct()
        for collabarate in all_mettings:
            if collabarate.start_time is not None:
                participants = [{"participant_name": f"{participant.first_name} {participant.last_name}", "participant_id": participant.id,
                                 "participant_avatar": avatar(participant)} for participant in collabarate.participants.all()]

                Collabarate_data.append({
                    "id": collabarate.id,
                    "title": collabarate.title + "- Click here To start ",
                    "start": convert_to_local_time(collabarate.start_time, self.request.query_params.get('timezone',None)).strftime("%Y-%m-%dT%H:%M:%S"),
                    "end": convert_to_local_time(collabarate.end_time, self.request.query_params.get('timezone',None)).strftime("%Y-%m-%dT%H:%M:%S"),
                    "allDay": False,
                    "backgroundColor": '#3379FF',
                    "borderColor": '#3379FF',
                    "reminder": 0,
                    "is_cancel": collabarate.is_cancel,
                    "call_type": collabarate.type,
                    "slot_status": "",
                    "status": "",
                    "backgroundColor": backgroundColor,
                    "borderColor": borderColor,
                    "participants": participants,
                    "url": collabarate.custom_url,
                    "type": collabarate.type,
                    "created_by": f"{collabarate.created_by.first_name} {collabarate.created_by.last_name}",
                    "created_at": local_time(collabarate.created_at).isoformat(),
                    "feedback_type": collabarate.type,
                    "is_speaker": True if user == collabarate.speaker else False
                })

        calendar_data.extend(Collabarate_data)

        response = {
            "message": "Success",
            "success": True,
            "data": calendar_data
        }
        return Response(response, status=status.HTTP_200_OK)


class MenteeJourneyDetails(APIView):
    def get(self, request, *args, **kwargs):
        user_type = UserTypes.objects.get(type="Mentor")
        try:
            mentor = User.objects.get(id=self.kwargs['mentor_id'], userType=user_type)
        except User.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(pk=self.kwargs['mentee_id'])
        except User.DoesNotExist:
            return Response({"message": "Mentee does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        # # print(user.id)
        try:
            journey = Channel.objects.get(pk=self.kwargs['journey_id'])
        except Channel.DoesNotExist:
            return Response({"message": "Journey does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        # # print("journey", journey)
        try:
            assign_mentor = AssignMentorToUser.objects.get(mentor=mentor, user=user, journey=journey)
        except Exception:
            return Response({"message": "incorrect journey or mentee id or the mentor/mentee has no similar journey", "success": False}, status=status.HTTP_400_BAD_REQUEST)

        call_lsit = mentorCalendar.objects.filter(
            mentor=mentor, participants=user, slot_status="Booked", start_time__gte=datetime.now())
        exp_call_lsit = mentorCalendar.objects.filter(
            mentor=mentor, participants=user, slot_status="Booked", start_time__lte=datetime.now())
        journey_group = ChannelGroup.objects.filter(channel=journey, is_delete=False).first()
        mentoring_journey = MentoringJourney.objects.filter(
            journey=journey, journey_group=journey_group, is_delete=False).order_by('display_order')
        room = get_chat_room(mentor, user)
        room = AllRooms.objects.get(name=room)
        contents_list = []
        content_image = ""
        for mentoring_journey in mentoring_journey:
            type = mentoring_journey.meta_key
            read_status = ""
            journals_id = ""
            attempt_id = ""
            if type == "quest":
                content = Content.objects.get(pk=mentoring_journey.value)
                content_image = content.image.url
                try:
                    user_read_status = UserCourseStart.objects.get(
                        user=user, content=content, channel_group=mentoring_journey.journey_group, channel=journey.pk)
                    read_status = user_read_status.status
                    start_time = user_read_status.created_at
                except UserCourseStart.DoesNotExist:
                    read_status = ""
            elif type == "assessment":
                test_series = TestSeries.objects.get(pk=mentoring_journey.value)
                test_attempt = TestAttempt.objects.filter(
                    test=test_series, user=user, channel=mentoring_journey.journey)
                if test_attempt.count() > 0:
                    read_status = "Complete"
                    attempt_id = test_attempt.first().id
            elif type == "survey":
                survey = Survey.objects.get(pk=mentoring_journey.value)
                survey_attempt = SurveyAttempt.objects.filter(
                    survey=survey, user=user)
                if survey_attempt.count() > 0:
                    read_status = "Complete"
                    attempt_id = survey_attempt.first().id
            elif type == "journals":
                weekely_journals = WeeklyLearningJournals.objects.get(
                    pk=mentoring_journey.value, journey_id=journey.pk)
                learnig_journals = LearningJournals.objects.filter(
                    weekely_journal_id=weekely_journals.pk, journey_id=journey.pk, email=user.email)
                if learnig_journals.count() > 0:
                    journals_id = learnig_journals.first().pk
                    read_status = "Complete"
            else:
                content_image = ""

            contents_list.append({
                "id": mentoring_journey.value,
                "journals_id": journals_id,
                "type": mentoring_journey.meta_key,
                "journey_group": journey_group.pk,
                "display_order": '',
                "title": mentoring_journey.name,
                "image": content_image,
                "id": mentoring_journey.value,
                "attempt_id": attempt_id,
                "journey_id": mentoring_journey.journey.pk,
                "read_status": read_status
            })

        learning_journals = LearningJournals.objects.filter(
            email=user.email, journey_id=journey.pk, is_draft=False, is_private=False, is_weekly_journal=False).order_by("-created_at")
        # # # print(learning_journals)
        for journals in learning_journals:
            contents_list.append({
                "id": '',
                "journals_id": journals.id,
                "type": "learning journals",
                "level":  "",
                "journey_group": journey_group.pk,
                "display_order": '',
                "title": journals.name,
                "image": '',
                "id": '',
                "attempt_id": '',
                "journey_id": journey.pk,
                "read_status": ''
            })

        user_details = []
        user_details.append(
            {
                "user_id": user.id,
                "user_name": f"{user.first_name} {user.last_name}",
                "username": user.username,
                "email": user.email,
                "position": user.position,
                "profile_heading": user.profile_heading,
                "user_profile_image": avatar(user),
                "current_status": user.current_status,
                "user_status": user.user_status,
                "room_name": room.name,
                "user_type": ", ".join(str(type.type) for type in user.userType.all()),
            }
        )
        meetings = []
        participants = []
        for call_lsit in call_lsit:
            participants = [{"participant_name": f"{participant.first_name} {participant.last_name}", "participant_id": participant.id,
                             "participant_avatar": avatar(participant)} for participant in call_lsit.participants.all()]
            meetings.append({
                "id": call_lsit.id,
                "title": call_lsit.title,
                "start_time": local_time(call_lsit.start_time).isoformat(),
                "description": call_lsit.description,
                "status": call_lsit.status,
                "url": call_lsit.url,
                "slot_status": call_lsit.slot_status,
                "is_cancel": call_lsit.is_cancel,
                "cancel_by": call_lsit.cancel_by if call_lsit.is_cancel else '',
                "participant": participants,
                "created_by": call_lsit.created_by,
                "created_at": local_time(call_lsit.created_at).isoformat()
            })
        expire_meetings = []
        for call_lsit in exp_call_lsit:
            participants = [{"participant_name": f"{participant.first_name} {participant.last_name}", "participant_id": participant.id,
                             "participant_avatar": avatar(participant)} for participant in call_lsit.participants.all()]
            expire_meetings.append({
                "id": call_lsit.id,
                "title": call_lsit.title,
                "start_time": local_time(call_lsit.start_time).isoformat(),
                "description": call_lsit.description,
                "status": call_lsit.status,
                "url": call_lsit.url,
                "slot_status": call_lsit.slot_status,
                "is_cancel": call_lsit.is_cancel,
                "cancel_by": call_lsit.cancel_by if call_lsit.is_cancel else '',
                "participant": participants,
                "created_by": call_lsit.created_by,
                "created_at": local_time(call_lsit.created_at).isoformat()
            })

        meetings.extend(expire_meetings)

        chats = Chat.objects.filter(Q(from_user=mentor) & Q(to_user=user) | Q(from_user=user) &
                                    Q(to_user=mentor)).order_by('-timestamp')
        chat_list = []
        for msg in chats:
            chat_list.append({
                "id": msg.id,
                "sender_id": msg.from_user.id,
                "from_user": f"{msg.from_user.first_name} {msg.from_user.last_name}",
                "receiver_id": msg.to_user.id,
                "to_user": f"{msg.to_user.first_name} {msg.to_user.last_name}",
                "message": msg.message,
                "type": msg.type,
                "file": msg.file.name if msg.file else '',
                "is_read": msg.is_read,
                "room_name": room.name,
                "created_at": msg.timestamp
            })

        data = {
            "user_details": user_details,
            "session": meetings,
            "content": contents_list,
            "chat": chat_list
        }

        response = {
            "message": "Success",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorLearningJournal(APIView):
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            type = UserTypes.objects.get(type=self.kwargs['type'])
        except User.DoesNotExist:
            return Response({"message": "User type does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(id=self.kwargs['user_id'], userType=type)
            # # print("user", user)
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        output_data = []
        # # # print("type",type.type)
        journey_list = [str(journey.id) for journey in company_journeys(type.type, user, company.id)]
        if type.type == "Learner":
            # # print("inside learner")
            learning_journal = []
            data = LearningJournals.objects.filter(email=user.email, is_weekly_journal=False, journey_id__in=journey_list).order_by("-created_at")
            # # print("data learner", data)
            for learning_jouranl in data:
                comments_list = []
                if str(learning_jouranl.user_id) == str(user.id):
                    is_edit_delete = True
                else:
                    is_edit_delete = False

                comments = LearningJournalsComments.objects.filter(
                    learning_journal=learning_jouranl).order_by("-created_at")[:3]
                for comment in comments:
                    if str(comment.user_id) == str(user.id):
                        is_edit_delete_comment = True
                    else:
                        is_edit_delete_comment = False
                    comments_list.append({
                        'id': comment.id,
                        'user_email': comment.user_email,
                        'user_name': comment.user_name,
                        'user_id': comment.user_id,
                        'body': comment.body,
                        'parend_comment_id': comment.parent_comment_id,
                        'is_edit_delete': is_edit_delete_comment,
                        "created_at": comment.created_at
                    })
                # # print(comments)
                learning_journal.append({
                    'id': learning_jouranl.id,
                    'name': learning_jouranl.name,
                    'email': learning_jouranl.email,
                    'is_draft': learning_jouranl.is_draft,
                    'microskill_id': learning_jouranl.microskill_id,
                    'skill_data_id': learning_jouranl.skill_data_id,
                    'learning_journal': learning_jouranl.learning_journal,
                    'is_weekly_journal': learning_jouranl.is_weekly_journal,
                    'weekely_journal_id': learning_jouranl.weekely_journal_id,
                    'journey_id': learning_jouranl.journey_id,
                    'user_name': learning_jouranl.user_name,
                    'user_id': learning_jouranl.user_id,
                    "comment": comments_list,
                    "is_edit_delete": is_edit_delete
                })
                # # # print("learning", learning_jouranl)
                # # # print("comments", comments)

            output_data.append({
                "journals": learning_journal,

            })
        else:
            users = []
            journey = []
            data = []
            learning_journal = []
            user_list = AssignMentorToUser.objects.filter(mentor=user, journey__id__in=journey_list)
            # # # print("user_list", user_list)
            for user_list in user_list:
                users.append(user_list.user.email)
                journey.append(str(user_list.journey.id))
            # # print(journey)
            # # print(users)
            data = LearningJournals.objects.filter(
                email__in=users, journey_id__in=journey, is_weekly_journal=False).order_by("-created_at")
            # # print("data", data)
            for learning_jouranl in data:
                if str(learning_jouranl.user_id) == str(user.id):
                    is_edit_delete = True
                else:
                    is_edit_delete = False
                comments_list = []
                comments = LearningJournalsComments.objects.filter(
                    learning_journal=learning_jouranl).order_by("-created_at")[:3]
                for comment in comments:
                    if str(comment.user_id) == str(user.id):
                        is_edit_delete_comment = True
                    else:
                        is_edit_delete_comment = False
                    comments_list.append({
                        'id': comment.id,
                        'user_email': comment.user_email,
                        'user_name': comment.user_name,
                        'user_id': comment.user_id,
                        'body': comment.body,
                        'parend_comment_id': comment.parent_comment_id,
                        "is_edit_delete": is_edit_delete_comment,
                        "created_at": comment.created_at
                    })

                learning_journal.append({
                    'id': learning_jouranl.id,
                    'name': learning_jouranl.name,
                    'email': learning_jouranl.email,
                    'is_draft': learning_jouranl.is_draft,
                    'microskill_id': learning_jouranl.microskill_id,
                    'skill_data_id': learning_jouranl.skill_data_id,
                    'learning_journal': learning_jouranl.learning_journal,
                    'is_weekly_journal': learning_jouranl.is_weekly_journal,
                    'weekely_journal_id': learning_jouranl.weekely_journal_id,
                    'journey_id': learning_jouranl.journey_id,
                    'user_name': learning_jouranl.user_name,
                    'user_id': learning_jouranl.user_id,
                    "comment": comments_list,
                    "is_edit_delete": is_edit_delete
                })
                # # # print("learning", learning_jouranl)
                # # # print("comments", comments)

            output_data.append({
                "journals": learning_journal,

            })

        response = {
            "message": "Success",
            "success": True,
            "type": "learning_journal",
            "data": output_data
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorWeeklyLearningJournal(APIView):
    def get(self, request, *args, **kwargs):
        
        try:
            type = UserTypes.objects.get(type=self.kwargs['type'])
        except UserTypes.DoesNotExist:
            return Response({"message": "User type does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=self.kwargs['user_id'], userType=type)
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        weekelyjournals = LearningJournals.objects.filter(
            email=user.email,  is_draft=False, is_weekly_journal=True).order_by("-created_at")
        output_data = []
        if type.type == "Learner":
            for data in weekelyjournals:
                post_user = User.objects.filter(id=data.user_id)
                attachments = LearningJournalsAttachment.objects.filter(post=data)
                comments = LearningJournalsComments.objects.filter(learning_journal=data).order_by("-created_at")[:3]
                comments_list = []
                attachments_list = []
                for comment in comments:
                    commentor = User.objects.filter(id=comment.user_id)
                    comments_list.append({
                        'id': comment.id,
                        'user_email': comment.user_email,
                        'user_name': comment.user_name,
                        'user_id': comment.user_id,
                        'body': comment.body,
                        'parend_comment_id': comment.parent_comment_id,
                        "profile_image": avatar(commentor.first()) if commentor else "",
                        'created_at': comment.created_at
                    })
                for attachment in attachments:
                    attachments_list.append({
                        'id': attachment.id,
                        'post': attachment.post,
                        'image_upload': attachment.image_upload,
                        'file_upload': attachment.file_upload,
                        'upload_for': attachment.upload_for
                    })
                output_data.append({
                    "journals": {
                        'id': data.id,
                        'name': data.name,
                        'email': data.email,
                        'is_draft': data.is_draft,
                        'microskill_id': data.microskill_id,
                        'skill_data_id': data.skill_data_id,
                        'learning_journal': data.learning_journal,
                        'is_weekly_journal': data.is_weekly_journal,
                        'weekely_journal_id': data.weekely_journal_id,
                        'journey_id': data.journey_id,
                        'profile_image': avatar(post_user.first()) if post_user else "",
                        'user_name': data.user_name,
                        'user_id': data.user_id,
                        "created_at": data.created_at if data else "",
                        "comment": comments_list,
                        "attachments": attachments_list
                    },
                })
        else:
            users = []
            journey = []
            data = []
            user_list = AssignMentorToUser.objects.filter(mentor=user)
            for user_list in user_list:

                users.append(user_list.user.email)
                journey.append(str(user_list.journey.id))
            # # print(journey)
            # # print(users)
            data = LearningJournals.objects.filter(
                email__in=users, journey_id__in=journey, is_weekly_journal=True, is_draft=False).order_by("-created_at")
            # # print(data)
            for learning_jouranl in data:
                post_user = User.objects.filter(id=learning_jouranl.user_id)

                attachments = LearningJournalsAttachment.objects.filter(post=learning_jouranl)
                comments = LearningJournalsComments.objects.filter(
                    learning_journal=learning_jouranl).order_by("-created_at")[:3]
                comments_list = []
                attachments_list = []
                for comment in comments:
                    commentor = User.objects.filter(id=comment.user_id)
                    comments_list.append({
                        'id': comment.id,
                        "learning_journal": comment.learning_journal.name,
                        "learning_journal_id": comment.learning_journal.id,
                        'user_email': comment.user_email,
                        'user_name': comment.user_name,
                        'user_id': comment.user_id,
                        'body': comment.body,
                        'parend_comment_id': comment.parent_comment_id,
                        "profile_image": avatar(commentor.first()) if commentor else "",
                        'created_at': comment.created_at
                    })
                for attachment in attachments:
                    attachments_list.append({
                        'id': attachment.id,
                        'post': attachment.post.name,
                        'post_id': attachment.post.id,
                        'image_upload': attachment.image_upload,
                        'file_upload': attachment.file_upload,
                        'upload_for': attachment.upload_for
                    })
                output_data.append({
                    "journals": {
                        'id': learning_jouranl.id,
                        'name': learning_jouranl.name,
                        'email': learning_jouranl.email,
                        'is_draft': learning_jouranl.is_draft,
                        'microskill_id': learning_jouranl.microskill_id,
                        'skill_data_id': learning_jouranl.skill_data_id,
                        'learning_journal': learning_jouranl.learning_journal,
                        'is_weekly_journal': learning_jouranl.is_weekly_journal,
                        'weekely_journal_id': learning_jouranl.weekely_journal_id,
                        'journey_id': learning_jouranl.journey_id,
                        'profile_image': avatar(post_user.first()) if post_user else "",
                        'user_name': learning_jouranl.user_name,
                        'user_id': learning_jouranl.user_id,
                        "created_at": learning_jouranl.created_at if learning_jouranl else "",
                        "comment": comments_list,
                        "attachments": attachments_list
                    },

                })
        response = {
            "message": "Success",
            "success": True,
            "type": "weekly_learning_journal",
            "data": output_data
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorChatModule(APIView):
    def get(self, request, *args, **kwargs):
        user_type = self.request.query_params.get('user_type')
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            mentor = User.objects.get(id=self.kwargs['mentor_id'], userType__type=user_type)
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        # all_room = AllRooms.objects.filter(Q(user1=mentor) | Q(user2=mentor) | Q(members__in=[mentor]), user1__is_active=True, user2__is_active=True, user1__is_delete=False, user2__is_delete=False)
        all_room = AllRooms.objects.filter(Q(user1=mentor) | Q(user2=mentor) | Q(members__in=[mentor]))
        # all_rooms1 = all_room.filter(Q(user1__company__in=[company]) & Q(user2__company__in=[company]), type="OneToOne")
        # all_rooms2 = all_room.filter(members__company__in=[company], type="OneToMany")
        # print("all_rooms1 ",all_rooms1)
        # print("all_rooms2 ",all_rooms2)
        # all_rooms = all_rooms1|all_rooms2
        all_rooms_list = []
        for rooms in all_room:

            
            if(rooms.type == 'OneToOne'):

                unread_msg = Chat.objects.filter(Q(to_user=mentor) & Q(from_user=rooms.user2) | Q(to_user=mentor) & Q(
                    from_user=rooms.user1), ~Q(read_by__in=[mentor])).count()

                all_rooms_list.append({
                    "type": rooms.type,
                    "group_name": "",
                    "group_avatar": "",
                    "members_count": "",
                    "user1_id": rooms.user1.id,
                    "user2_id": rooms.user2.id,
                    "user1_username": rooms.user1.username,
                    "user2_username": rooms.user2.username,
                    "user1_avatar": avatar(rooms.user1),
                    "user2_avatar": avatar(rooms.user2),
                    "user1_full_name": f"{rooms.user1.first_name} {rooms.user1.last_name}",
                    "user2_full_name": f"{rooms.user2.first_name} {rooms.user2.last_name}",
                    "room_name": rooms.name,
                    "unread_msg": unread_msg
                })
            else:
                print("many ",rooms.type)
                unread_msg = Chat.objects.filter(~Q(read_by__in=[mentor]) & ~Q(
                    from_user=mentor), room=rooms).count()
                all_rooms_list.append({
                    "type": rooms.type,
                    "group_name": rooms.group_name,
                    "group_avatar": group_avatar(rooms),
                    "room_name": rooms.name,
                    "unread_msg": unread_msg,
                    "members_count": rooms.members.count(),
                    "user1_username": "",
                    "user2_username": "",
                    "user1_avatar": "",
                    "user2_avatar": "",
                    "user1_full_name": "",
                    "user2_full_name": "",
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


class ChatMessages(APIView):
    serializer_class = ChatMessageSerializer

    def post(self, request, *args, **kwargs):
        # # print(request.data)
        serializer = self.serializer_class(data=request.data)
        user_type = self.request.query_params.get('user_type')
        timezone = self.request.query_params.get('timezone')
        if not timezone:
            return Response({"message": "timzone required", "success": False}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            try:
                user = User.objects.get(id=request.data['user_id'], userType__type=user_type)
            except User.DoesNotExist:
                return Response({"message": "User doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                room = AllRooms.objects.get(name=request.data['room_name'])
            except AllRooms.DoesNotExist:
                return Response({"message": "Room doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            chats = Chat.objects.filter(
                Q(from_user=room.user1) & Q(to_user=room.user2) | Q(from_user=room.user2) & Q(
                    to_user=room.user1) | Q(room=room)).order_by('timestamp')
            chat_list = []
            if chats:
                for chat in chats:
                    chat.is_read = True
                    chat.read_by.add(user)
                    chat.save()

                for msg in chats:
                    chat_list.append({
                        "id": msg.id,
                        "room_type": room.type,
                        "sender_id": msg.from_user.id,
                        "from_user": f"{msg.from_user.first_name} {msg.from_user.last_name}",
                        "receiver_id": msg.to_user.id if msg.to_user else '',
                        "to_user": f"{msg.to_user.first_name} {msg.to_user.last_name}" if msg.to_user else '',
                        "message": msg.message,
                        "type": msg.msg_type,
                        "file": msg.file.name if msg.file else '',
                        "is_read": msg.is_read,
                        "room_name": room.name,
                        "group_name": room.group_name if room.group_name else '',
                        "group_avatar": group_avatar(room) if room.group_image else "",
                        "created_at": convert_to_local_time(msg.timestamp, timezone)
                    })
            response = {
                "message": "Chat data",
                "success": True,
                "data": chat_list,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateEvent(APIView):
    def post(self, request):
        print("Creating a new event session")
        # # print(request.data)
        serializer = AddEventSerializer(data=request.data)
        if serializer.is_valid():
            try:
                channel = Channel.objects.get(id=request.data['journey_id'])
            except Channel.DoesNotExist:
                return Response({"message": "Journey does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                mentor = User.objects.get(id=request.data['mentor_id'], userType__type="Mentor")
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            # start_time = request.data['start_time']
            # end_time = request.data['end_time']
            #2023-04-29T12:00:00.000Z
            start_time = request.data['start_time']
            end_time = request.data['end_time']
            start_time = convert_to_utc(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"), self.request.data['timezone'])
            end_time = convert_to_utc(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"), self.request.data['timezone'])
            title = request.data['title']
            if mentorcal := mentorCalendar.objects.filter(Q(start_time__exact=start_time) | (Q(start_time__gt=start_time) & Q(start_time__lt=end_time)), mentor=mentor, is_cancel=False):
                # # print("kjfks", title)
                return Response({"message": "Slot time already exist", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # # print("fsjs", title)
                mentorcal = mentorCalendar.objects.create(mentor=mentor, title=title, start_time=start_time, journey=channel, company=channel.company,
                                                          end_time=end_time, created_by="Mentor", created_by_id=mentor.pk)

            assign_mentor_to_user = AssignMentorToUser.objects.filter(mentor=mentor, is_assign=True, is_revoked=False, journey=channel)
            for assign_mentor in assign_mentor_to_user:
                mentee = assign_mentor.user
                description = f"""Hi {mentee.first_name} {mentee.last_name}!
                Your mentor has opened time slots for this week. Don't forget to schedule time with your mentor!"""
                context = {
                    "screen": "Mentor Call",
                }
                send_push_notification(mentee, 'Schedule Mentor Call', description, context)
            data = {
                "id": mentorcal.id,
                "title": title,
                "journey_id": mentorcal.journey.id,
                "journey_title": mentorcal.journey.title,
                # "start": mentorcal.start_time,
                # "end": mentorcal.end_time,
                "start": convert_to_local_time(mentorcal.start_time, self.request.data['timezone']),
                "end": convert_to_local_time(mentorcal.end_time, self.request.data['timezone']),
                "is_cancel": mentorcal.is_cancel,
                "call_type": mentorcal.call_type,
                "slot_status": mentorcal.slot_status,
                "status": mentorcal.status,
                "created_by": mentorcal.created_by,
                "cancel_by_id": mentorcal.cancel_by_id,
                "created_at": convert_to_local_time(mentorcal.created_at, self.request.data['timezone'])

            }
            response = {
                "message": "slot created successfully",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateEvent(APIView):
    def post(self, request):
        # # print(request.data)
        serializer = UpdateEventSerializer(data=request.data)
        if serializer.is_valid():
            try:
                mentor = User.objects.get(id=request.data['mentor_id'], userType__type="Mentor")
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            start_time = request.data['start_time']
            end_time = request.data['end_time']
            start_time = convert_to_utc(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"), self.request.data['timezone'])
            end_time = convert_to_utc(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"), self.request.data['timezone'])
            title = request.data['title']
            mentorcal_id = request.data['mentorcal_id']
            mentorCal = mentorCalendar.objects.filter(pk=mentorcal_id)
            mentorCal.update(start_time=start_time, end_time=end_time, title=title)
            mentorcal = mentorCal.first()
            if mentorcal.url:
                participants = mentorcal.participants
                send_update_booking_mail(participants, mentorcal.mentor,  mentorcal.mentor.first_name,
                                         mentor.first_name, url_shortner(mentorcal.url, BASE_URL), mentorcal.start_time, title, self.request.data['timezone'])
            data = {
                "id": mentorcal.id,
                "title": title,
                "start": convert_to_local_time(mentorcal.start_time, self.request.data['timezone']).isoformat(),
                "end": convert_to_local_time(mentorcal.end_time, self.request.data['timezone']).isoformat(),
                "is_cancel": mentorcal.is_cancel,
                "call_type": mentorcal.call_type,
                "slot_status": mentorcal.slot_status,
                "status": mentorcal.status,
                "created_by": mentorcal.created_by,
                "created_at": mentorcal.created_at

            }
            response = {
                "message": "slot details updated successfully",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteEvent(APIView):
    def post(self, request):
        # # print(request.data)
        serializer = DeleteEventSerializer(data=request.data)
        if serializer.is_valid():
            try:
                mentor = Mentor.objects.filter(id=request.data['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "Mentor does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentorcal_id = request.data['mentorcal_id']
            mentorCalendar.objects.filter(pk=mentorcal_id).delete()
            return Response({"message": "slot deleted successfully", "success": True}, status=status.HTTP_200_OK)
        return Response({"message": "slot deleted successfully", "success": False}, status=status.HTTP_400_BAD_REQUEST)


class LearningJournalPostComment(APIView):
    def post(self, request):
        data = request.data
        serializer = LearningJournalPostCommentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=request.data['mentor_id'])
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            learning_journal_id = request.data['learningjournal_id']
            try:
                learningjournal = LearningJournals.objects.get(pk=learning_journal_id)
            except LearningJournals.DoesNotExist:
                return Response({"message": "learning journal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            comment = request.data['answer']
            user_name = f"{user.first_name} {user.last_name}"
            learning_journal_comment = LearningJournalsComments.objects.create(learning_journal=learningjournal,
                                                                               user_email=user.email, user_name=user_name, user_id=user.pk, body=comment)
            data = {
                "id": learning_journal_comment.id,
                "user_id": learning_journal_comment.user_id,
                "user_name": learning_journal_comment.user_name,
                "comment": learning_journal_comment.body,
                "profile_image": avatar(user),
                "created_at": learning_journal_comment.created_at,
                "parent_comment_id": learning_journal_comment.parent_comment_id.id if learning_journal_comment.parent_comment_id else ''
            }

            response = {
                "message": "Commented successfully",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditProfileAssessmentQues(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        type = self.request.query_params.get('type') or "Learner"
        assesst_answer = UserProfileAssest.objects.filter(user=user, assest_question__question_for=type)
        question_option_list = []
        for question in assesst_answer:
            question_option_list.append({
                "question_id": question.assest_question.id,
                "question": question.assest_question.question,
                "options": question.assest_question.options,
                "question_type": question.assest_question.question_type,
                "question_for": question.assest_question.question_for,
                "answer_id": question.id,
                "response": question.response,
                "description": question.description,
                "is_active": question.assest_question.is_active,
                "is_delete": question.assest_question.is_delete,
                "is_multichoice": question.assest_question.is_multichoice,
                "user": user.id,
            })
        response = {
            "message": "Assessment question and response",
            "success": True,
            "data": question_option_list
        }
        return Response(response, status=status.HTTP_200_OK)


class WeeklyJournalPostAPI(APIView):
    def get(self, request, *args, **kwargs):
        try:
            mentor = User.objects.get(id=self.kwargs['mentor_id'])
        except User.DoesNotExist:
            return Response({"message": "User doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            learning_journals = LearningJournals.objects.get(pk=self.kwargs['journal_id'])
        except LearningJournals.DoesNotExist:
            return Response({"message": "learning journals not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        # # print("learning_journals", learning_journals)
        learning_journals_attachments = LearningJournalsAttachment.objects.filter(
            post=learning_journals, upload_for="Post")
        comments = LearningJournalsComments.objects.filter(learning_journal=learning_journals)
        comment_list = []
        for comment in comments:
            commentor = User.objects.filter(id=comment.user_id)
            comment_list.append({'id': comment.id, 'user_email': comment.user_email, 'user_name': comment.user_name, "profile_image": avatar(commentor.first()) if commentor else "",
                                 'user_id': comment.user_id, 'body': comment.body, 'parend_comment_id': comment.parent_comment_id, "created_at": comment.created_at})
        attachments_list = []
        for attachment in learning_journals_attachments:
            attachments_list = ({
                "id": attachment.id,
                "learning_jounrnal_id": attachment.post.id,
                "learning_jounrnal_name": attachment.post.name,
                "image_upload": post_comment_images(attachment) if attachment.image_upload else "",
                "file_upload": post_comment_file(attachment) if attachment.file_upload else "",
                "upload_for": attachment.upload_for
            })
        user = User.objects.filter(id=learning_journals.user_id)
        learning_journals_list = {
            "id": learning_journals.id,
            "is_weekly_journal": learning_journals.is_weekly_journal,
            "weekly_journal_id": learning_journals.weekely_journal_id if learning_journals.is_weekly_journal else '',
            "name": learning_journals.name if learning_journals else "",
            "learning_journal": learning_journals.learning_journal if learning_journals else "",
            "user_name": learning_journals.user_name if learning_journals else "",
            "profile_image": avatar(user.first()) if user else "",
            "created_at": learning_journals.created_at if learning_journals else "",
            "comments": comment_list,
            "attachments": attachments_list
        }
        response = {
            "message": "Weekly learning journals data",
            "success": True,
            "data": learning_journals_list
        }
        return Response(response, status=status.HTTP_200_OK)


class CreateChatGroup(APIView):
    serializer_class = CreateChatGroupSerializer

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if request.data['user_type'] not in ["Mentor", "ProgramManager"]:
                return Response({"message": "You are not authorised to create group!", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user = User.objects.get(pk=request.data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            # # # print(request.data)
            name = request.data['group_name']
            description = request.data['description']
            # members = request.data.getlist('members')
            member_list = request.data['members']
            # # # print("image group", image)
            group_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

            group = AllRooms.objects.create(name=group_id, group_name=name, description=description,
                                            type='OneToMany', created_by=user)
            if data.get('group_avatar'):
                image = request.FILES['group_avatar']
                group.group_image = image

            member_list = member_list.split(",")
            print("members", member_list)
            if str(user.id) in member_list:
                return Response({"message": "user_id cannot be in group member list", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            for member in member_list:
                print(member)
                if request.data['user_type'] == "Mentor":
                    if User.objects.filter(id=member, userType__type__in=["Learner", "Mentor"]).exists():
                        group.members.add(member)
                elif request.data['user_type'] == "ProgramManager":
                    if User.objects.filter(id=member, userType__type__in=["Learner", "Mentor", "ProgramManager"]).exists():
                        group.members.add(member)
            group.members.add(user)
            group.group_admin.add(user)
            group.save()
            response = {
                "message": " data",
                "success": True,
                "data": "data"
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if "Mentor" or "ProgramManager" not in request.data['user_type']:
                return Response({"message": "You are not authorised to create group!", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user = User.objects.get(pk=request.data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

            group = AllRooms.objects.filter(name=request.data['room_name'])
            if not group:
                return Response({"message": "Group doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

            name = request.data['group_name']
            description = request.data['description']
            members = request.data['members']

            group.update(group_name=name, description=description)
            members = members.split(",")

            chat_group = group.first()
            if data.get('group_avatar'):
                image = request.FILES['group_avatar']
                group.group_image = image
            member_list = [member.id for member in chat_group.members.all()]
            for member in member_list:
                if request.data['user_type'] == "Mentor":
                    User.objects.filter(~Q(id=user.id) and Q(id=member), userTypes__type__in=["Learner", "Mentor"])
                elif request.data['user_type'] == "ProgramManager":
                    User.objects.filter(~Q(id=user.id) and Q(id=member), userTypes__type__in=[
                                        "Learner", "Mentor", "ProgramManager"])
                if member not in members:
                    chat_group.members.remove(member)

            for member in members:
                if request.data['user_type'] == "Mentor":
                    User.objects.filter(~Q(id=user.id) and Q(id=member), userTypes__type__in=["Learner", "Mentor"])
                elif request.data['user_type'] == "ProgramManager":
                    User.objects.filter(~Q(id=user.id) and Q(id=member), userTypes__type__in=[
                                        "Learner", "Mentor", "ProgramManager"])
                if member not in member_list:
                    chat_group.members.add(member)
            chat_group.save()

            response = {
                "message": "data",
                "success": True,
                "data": chat_group.id
            }
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class RemoveGroupMembers(APIView):
    def post(self, request):
        serializer = RemoveGroupMembersSerializer(data=request.data)
        if serializer.is_valid():
            if request.data['user_type'] != "Mentor":
                return Response({"message": "You are not authorised to create group!", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                mentor = User.objects.get(pk=request.data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

            members = request.data['members']
            group = AllRooms.objects.filter(name=request.data['room_name'])
            if not group:
                return Response({"message": "Group doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            chat_group = group.first()
            member_list = [member.id for member in chat_group.members.all()]
            for member in members:
                if member in member_list:
                    chat_group.members.remove(member)
            chat_group.save()
            response = {
                "message": "member successfully removed",
                "success": True,
                "data": "data"
            }
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class Journal(APIView):
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            type = UserTypes.objects.get(type=self.kwargs['type'])
        except User.DoesNotExist:
            return Response({"message": "User type does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=self.kwargs['user_id'], userType=type)
            # # print("user", user)
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if not self.request.query_params.get('timezone'):
            return Response({"message": "Timezone is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        timezone = self.request.query_params.get('timezone')
        journeys = company_journeys(type, user, company.id)
        journey_ids = [str(journey.id) for journey in journeys]
        output_data = []
        learning_journal = []
        private_journal = []
        data = []
        if type.type == "Mentor":
            user_list = AssignMentorToUser.objects.filter(mentor=user, journey__in=journeys, is_assign=True, is_revoked=False)
            # # # print("user_list", user_list)
            for user_list in user_list:
                # users.append(user_list.user.email)
                # journey.append(str(user_list.journey.id))
                # # print("journey", journey)
                data1 = LearningJournals.objects.filter(
                    email=user_list.user.email, journey_id=user_list.journey.id, is_draft=False, is_private=False).order_by("-created_at")
                data.extend(list(data1))
            data2 = LearningJournals.objects.filter(
                email=user.email, is_draft=False, is_private=True).order_by("-created_at")
            data.extend(list(data2))
        else:
            data = LearningJournals.objects.filter(Q(journey_id__in=journey_ids) | Q(is_private=True), email=user.email).order_by("-created_at")
        for journal in data:
            journal_user = User.objects.filter(id=journal.user_id).first()
            # # print(user.id, journal.user_id)

            if str(journal.user_id) == str(user.id):
                is_edit_delete = True
            else:
                is_edit_delete = False
            comments_list = []
            comments = LearningJournalsComments.objects.filter(
                learning_journal=journal).order_by("-created_at")
            for comment in comments:
                commentor = User.objects.filter(id=comment.user_id).first()
                if str(comment.user_id) == str(user.id):
                    is_edit_delete_comment = True
                else:
                    is_edit_delete_comment = False
                comments_list.append({
                    'id': comment.id,
                    'user_email': comment.user_email,
                    'user_name': comment.user_name,
                    'user_id': comment.user_id,
                    'body': comment.body,
                    'parend_comment_id': comment.parent_comment_id,
                    'is_edit_delete': is_edit_delete_comment,
                    "profile_image": avatar(commentor) if commentor else '',
                    "created_at": strf_format(convert_to_local_time(comment.created_at, timezone)),
                })
            # # print(comments)
            if journal.is_private == True:
                private_journal.append({
                    'id': journal.id,
                    'name': journal.name,
                    'email': journal.email,
                    'is_draft': journal.is_draft,
                    'microskill_id': journal.microskill_id,
                    'skill_data_id': journal.skill_data_id,
                    'learning_journal': journal.learning_journal,
                    'is_weekly_journal': journal.is_weekly_journal,
                    'weekely_journal_id': journal.weekely_journal_id,
                    'journey_id': journal.journey_id,
                    'user_name': journal.user_name,
                    'user_id': journal.user_id,
                    "profile_image": avatar(journal_user) if journal_user else '',
                    "comment": comments_list,
                    "is_private": True,
                    "created_at": strf_format(convert_to_local_time(journal.created_at, timezone)),
                    "is_edit_delete": is_edit_delete
                })
            else:
                attachments_list = []
                attachments = LearningJournalsAttachment.objects.filter(post=journal)
                for attachment in attachments:
                    attachments_list.append({
                        'id': attachment.id,
                        'image_upload': post_comment_images(attachment),
                        'file_upload': post_comment_file(attachment),
                        'upload_for': attachment.upload_for
                    })
                learning_journal.append({
                    'id': journal.id,
                    'name': journal.name,
                    'email': journal.email,
                    'is_draft': journal.is_draft,
                    'microskill_id': journal.microskill_id,
                    'skill_data_id': journal.skill_data_id,
                    'learning_journal': journal.learning_journal,
                    'is_weekly_journal': journal.is_weekly_journal,
                    'weekely_journal_id': journal.weekely_journal_id,
                    'journey_id': journal.journey_id,
                    'user_name': journal.user_name,
                    'user_id': journal.user_id,
                    "profile_image": avatar(journal_user) if journal_user else '',
                    "created_at": strf_format(convert_to_local_time(journal.created_at, timezone)),
                    "comment": comments_list,
                    "attachments": attachments_list,
                    "is_private": False,
                    "is_edit_delete": is_edit_delete

                })
            # # # print("learning", learning_jouranl)
            # # # print("comments", comments)

        output_data = {
            "learning_journals": learning_journal,
            "private_journals": private_journal
        }

        response = {
            "message": "Success",
            "success": True,
            "type": "journal",
            "data": output_data
        }
        return Response(response, status=status.HTTP_200_OK)


class CreateJournal(APIView):
    def post(self, request):
        data = request.data
        serializer = CreateJournalSerializer(data=request.data)
        user_type = self.request.query_params.get('user_type') or "Learner"
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=request.data['user_id'], userType__type=user_type)
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

            name = request.data['title']
            user_name = f"{user.first_name} {user.last_name}"
            body = request.data['body']
            is_private = update_boolean(data.get('is_private'))
            journey_id = ""
            if not is_private:
                try:
                    journey = Channel.objects.get(id=data.get('journey_id'),
                                                  parent_id=None, is_active=True, is_delete=False)
                    journey_id = journey.pk
                except Channel.DoesNotExist:
                    return Response({"message": "journey_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            journal = LearningJournals.objects.create(
                name=name, user_name=user_name, user_id=user.pk, email=user.email, learning_journal=body, is_private=is_private, journey_id=journey_id)

            data = {
                "id": journal.id,
                "user_id": journal.user_id,
                "user_name": journal.user_name,
                "title": journal.name,
                "body": journal.learning_journal,
                "journey_id": journal.journey_id,
                "profile_image": avatar(user),
                "created_at": journal.created_at
            }

            response = {
                "message": "Journal created successfully",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateJournal(APIView):
    def post(self, request):
        serializer = EditJournalSerializer(data=request.data)
        if serializer.is_valid():
            data = request.data
            try:
                user = User.objects.get(pk=request.data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                journal = LearningJournals.objects.get(id=request.data['id'])
            except LearningJournals.DoesNotExist:
                return Response({"message": "Journal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            if str(journal.user_id) != str(user.id):
                return Response({"message": "You are not authorised to update the journal", "success": False}, status=status.HTTP_404_NOT_FOUND)

            body = request.data['body']
            if data.get('is_private'):
                is_private = update_boolean(data.get('is_private'))
            else:
                is_private = False
            journey_id = ""
            if not is_private:
                if data.get('journey_id'):
                    journey_id = request.data['journey_id']
            # # print("1514", is_private, journey_id)
            journal.learning_journal = body
            journal.is_private = is_private
            journal.journey_id = journey_id
            journal.save()

            data = {
                "id": journal.id,
                "user_id": journal.user_id,
                "user_name": journal.user_name,
                "title": journal.name,
                "body": journal.learning_journal,
                "is_private": journal.is_private,
                "journey_id": journal.journey_id,
                "profile_image": avatar(user),
                "created_at": journal.created_at
            }

            response = {
                "message": "Journal updated successfully",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateJournalComment(APIView):
    def post(self, request):
        serializer = EditJournalCommentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=request.data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                comment = LearningJournalsComments.objects.get(id=request.data['id'])
            except LearningJournalsComments.DoesNotExist:
                return Response({"message": "Comment does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            if str(comment.user_id) != str(user.id):
                return Response({"message": "You are not authorised to update the comment", "success": False}, status=status.HTTP_404_NOT_FOUND)

            body = request.data['body']

            comment.body = body
            comment.save()

            data = {
                "id": comment.id,
                "user_id": comment.user_id,
                "user_name": comment.user_name,
                "profile_image": avatar(user),
                "created_at": comment.created_at,
                "body": comment.body
            }

            response = {
                "message": "Comment updated successfully",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmitProfileAssessment(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SubmitProfileAssessmentSerilizer(data=request.data)
        user_type = self.request.query_params.get("user_type") or "Learner"
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=request.data['user_id'], userType__type=user_type)
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            assessment = request.data['assessment']
            data = []
            for assess in assessment:
                try:
                    question = ProfileAssestQuestion.objects.get(id=assess['question']) 
                except ProfileAssestQuestion.DoesNotExist:
                    return Response({"message": "Question does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

                profile_assesst = UserProfileAssest.objects.filter(
                    user=user, assest_question=question, question_for=user_type).first()
                if profile_assesst:
                    profile_assesst.response = assess['response']
                    profile_assesst.save()
                else:
                    profile_assesst = UserProfileAssest.objects.create(question_for=user_type,
                                                                       user=user, assest_question=question, response=assess['response'])

                data.append({
                    "id": profile_assesst.id,
                    "question_id": profile_assesst.assest_question.id,
                    "question": profile_assesst.assest_question.question,
                    "response": profile_assesst.response,
                    "user_id": profile_assesst.user.id
                })

            response = {
                "message": "Assessment Submitted successfully",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JournalDetail(APIView):
    def get(self, request, *args, **kwargs):

        journal_detail = []
        try:
            journal = LearningJournals.objects.get(id=self.kwargs['id'])
        except User.DoesNotExist:
            return Response({"message": "Journal does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=request.user.id)
            # # print("user", user)
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        # # print("data learner", journal)

        # # print(user.id, journal.user_id)

        if str(journal.user_id) == str(user.id):
            is_edit_delete = True
        else:
            is_edit_delete = False
        comments_list = []
        comments = LearningJournalsComments.objects.filter(
            learning_journal=journal).order_by("-created_at")
        journal_user = User.objects.filter(id=journal.user_id).first()
        for comment in comments:
            commentor = User.objects.filter(id=comment.user_id).first()
            if str(comment.user_id) == str(user.id):
                is_edit_delete_comment = True
            else:
                is_edit_delete_comment = False
            comments_list.append({
                'id': comment.id,
                'user_email': comment.user_email,
                'user_name': comment.user_name,
                'user_id': comment.user_id,
                'body': comment.body,
                'profile_image': avatar(commentor) if commentor else '',
                'parend_comment_id': comment.parent_comment_id,
                'is_edit_delete': is_edit_delete_comment,
                "created_at": comment.created_at
            })
        # # print(comments)

        attachments_list = []
        attachments = LearningJournalsAttachment.objects.filter(post=journal)
        for attachment in attachments:
            attachments_list.append({
                'id': attachment.id,
                'post': attachment.post,
                'image_upload': attachment.image_upload,
                'file_upload': attachment.file_upload,
                'upload_for': attachment.upload_for
            })
        journal_detail.append({
            'id': journal.id,
            'name': journal.name,
            'email': journal.email,
            'is_draft': journal.is_draft,
            'microskill_id': journal.microskill_id,
            'skill_data_id': journal.skill_data_id,
            'learning_journal': journal.learning_journal,
            'is_weekly_journal': journal.is_weekly_journal,
            'weekely_journal_id': journal.weekely_journal_id,
            'journey_id': journal.journey_id,
            'user_name': journal.user_name,
            'user_id': journal.user_id,
            "comment": comments_list,
            "profile_image": avatar(journal_user) if journal_user else '',
            "attachments": attachments_list,
            "is_private": journal.is_private,
            "created_at": journal.created_at,
            "is_edit_delete": is_edit_delete

        })
        # # # print("learning", learning_jouranl)
        # # # print("comments", comments)

        response = {
            "message": "Success",
            "success": True,
            "journal": journal_detail
        }
        return Response(response, status=status.HTTP_200_OK)
