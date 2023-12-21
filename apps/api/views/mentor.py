import pytz
import datetime
from datetime import date
from apps.api.serializers import AvailableSlotSerializer, BookAppoinmentSerializer, CancelAppoinmentSerializer, \
    MentorCalendarSerializer, MentorsScheduedSessionSerializer, UserIdSerializer, addFavouriteSerializer
from apps.atpace_community.utils import avatar, convert_to_utc
from django.db.models.query_utils import Q
from apps.content.utils import company_journeys
from rest_framework import status
from apps.api.utils import available_slots, book_appointment, call_slot_status, cancel_appointment
from apps.community.models import LearningJournals
from apps.mentor.models import AssignMentorToUser, BookmarkMentor, PoolMentor, mentorCalendar
from apps.users.models import Collabarate, Learner, User, Mentor, UserTypes, Company
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.users.templatetags.dashboard import get_weekly_journal, mentor_journeys, today_sessions, total_mentee, \
    total_sessions, get_total_points
from apps.users.templatetags.tags import get_chat_room
from ...users.utils import aware_time, local_time, convert_to_local_time
from apps.users.utils import add_participant_for_mentor_mentee_call
utc = pytz.UTC

class MentorProfile(APIView):
    def post(self, request, ):
        data = request.data
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            try:
                mentor = Mentor.objects.get(pk=request.data['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "Invalid UUID of mentor"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = Learner.objects.get(pk=request.data['user_id'])
            except Learner.DoesNotExist:
                return Response({"message": "Invalid UUID of user"}, status=status.HTTP_400_BAD_REQUEST)
            appointment = mentorCalendar.objects.filter(
                mentor=mentor, participants=user, start_time__gte=datetime.datetime.now(), is_cancel=False)
            appointments = []
            if appointment.count() > 0:
                for appointment in appointment:
                    appointments.append({
                        "id": appointment.id,
                        "title": appointment.title,
                        "description": appointment.description,
                        "start_time": appointment.start_time,
                        "end_time": appointment.end_time,
                        "url": appointment.url,
                        "bookmark": appointment.bookmark,
                        "created_at": appointment.created_at,
                        "is_favourite": False,
                    })

            industry_list = []
            expertize_list = []
            for industry in mentor.industry.all():
                industry_list.append(industry.name)
            for expertize in mentor.expertize.all():
                expertize_list.append(expertize.name)
            response = {
                "message": "Success",
                "success": True,
                "data": {

                    "id": mentor.id,
                    "email": mentor.email,
                    "first_name": mentor.first_name,
                    "last_name": mentor.last_name,
                    "gender": mentor.gender,
                    "age": mentor.age,
                    "current_status": mentor.current_status,
                    "position": mentor.position,
                    "expertize": expertize_list,
                    "industry": industry_list,
                    "avatar": mentor.avatar.url,
                    "about_us": mentor.about_us,
                    "profile_heading": mentor.profile_heading,
                },
                "appointment": appointments
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class MentorCalendarAPIVIew(APIView):
    def post(self, request):
        data = request.data
        # print(data)
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            try:
                mentor = Mentor.objects.get(pk=request.data['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "Invalid UUID of mentor"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = Learner.objects.get(pk=request.data['user_id'])
            except Learner.DoesNotExist:
                return Response({"message": "Invalid UUID of user"}, status=status.HTTP_400_BAD_REQUEST)
            all_list = mentorCalendar.objects.filter(
                mentor=mentor, start_time__gte=datetime.datetime.now(), slot_status="Available", is_cancel=False)
            
            mentor_list = MentorCalendarSerializer(all_list, many=True)
            response = {
                "message": "Success",
                "success": True,
                "data": mentor_list.data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class NewAppoinment(APIView):
    def get(self, request, user_id):
        data = {"user_id": str(user_id)}
        # print(data)
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            user = User.objects.get(pk=user_id)
            all_list = mentorCalendar.objects.filter(participants=user, is_cancel=False)

            mentor_list = MentorCalendarSerializer(all_list, many=True).data
            collaborator_list = []
            collaborator = Collabarate.objects.filter(participants=user, is_cancel=False)
            for collab in collaborator:
                collaborator_list.append({
                    "id": collab.id,
                    "title": collab.title,
                    "description": collab.description,
                    "start_time": local_time(collab.start_time).isoformat(),
                    "end_time": local_time(collab.end_time).isoformat(),
                    "url": collab.custom_url,
                    "reminder": "",
                    "is_cancel": collab.is_cancel,
                    "call_type": collab.type,
                    "slot_status": "",
                    "status": "",
                    "bookmark": False,
                    "created_at": local_time(collab.created_at).isoformat(),
                    "mentor": collab.speaker.pk,
                    "mentor_name": collab.speaker.first_name + " " + collab.speaker.last_name,
                    "mentor_avatar": collab.speaker.avatar.url,
                })
            collaborator_list.extend(mentor_list)
            response = {
                "message": "Success",
                "success": True,
                "data": collaborator_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class HistoryAppoinment(APIView):
    def get(self, request, user_id ):
        data = {"user_id": str(user_id)}
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            timezone = request.query_params.get('timezone', None)
            if timezone is None:
                return Response({"message": "timezone is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            elif timezone == "undefined":
                return Response({"message": "Please Update Your Application",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            
            
            if not self.request.query_params.get('company_id'):
                return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                company = Company.objects.get(id=self.request.query_params.get('company_id'))
            except Company.DoesNotExist:
                return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user = User.objects.get(pk=user_id)
            journeys = company_journeys("Learner", user, company.id)
            mentor = AssignMentorToUser.objects.filter(journey__closure_date__gt=datetime.datetime.now(),
                user=request.user, journey__in=journeys, is_assign=True, is_revoked=False).values('mentor')
            mentor_calendars = mentorCalendar.objects.filter(participants=user, mentor__in=mentor, is_cancel=False)
            calendar_data = []
            for mentor_calendar in mentor_calendars:
                current_time = utc.localize(datetime.datetime.combine(datetime.datetime.now(), datetime.datetime.min.time()))
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
                    "description": mentor_calendar.description,
                    "start_time":  convert_to_local_time(mentor_calendar.start_time, timezone),
                    "end_time": convert_to_local_time(mentor_calendar.end_time, timezone),
                    "allDay": False,
                    "reminder": 0,
                    "bookmark": mentor_calendar.bookmark,
                    "is_cancel": mentor_calendar.is_cancel,
                    "call_type": mentor_calendar.call_type,
                    "type": "mentor_calendar",
                    "slot_status": call_slot_status(mentor_calendar, timezone),
                    "status": call_status,
                    "backgroundColor": backgroundColor,
                    "borderColor": borderColor,
                    "url": mentor_calendar.url,
                    "participants": participants,
                    "type": "One To One",
                    "mentor": mentor_calendar.mentor.id,
                    "mentor_name": mentor_calendar.mentor.get_full_name(),
                    "mentor_avatar": avatar(mentor_calendar.mentor),
                    "created_by": mentor_calendar.created_by,
                    "created_at": mentor_calendar.created_at,
                    "feedback_type":"MentorCall"
                })
            collaborator_list = []
            # collaborator = Collabarate.objects.filter(Q(participants__in=[user]) | Q(
                # company=company) | Q(speaker=user), is_active=True).distinct()
            collaborator = Collabarate.objects.filter(Q(participants__in=[user]) | Q(speaker=user), company=company, is_active=True, is_cancel=False).distinct()
            current_time = aware_time(datetime.datetime.combine(date.today(), datetime.datetime.min.time()))
            for collab in collaborator:
                if collab.is_cancel:
                    event_status = "Cancelled"
                elif collab.start_time >= current_time:
                    event_status = "Upcoming"
                else:
                    event_status = "Completed"
                collaborator_list.append({
                    "id": collab.id,
                    "title": collab.title,
                    "description": collab.description,
                    "start_time": convert_to_local_time(collab.start_time, timezone),
                    "end_time": convert_to_local_time(collab.end_time, timezone),
                    "url": collab.custom_url,
                    "reminder": "",
                    "is_cancel": collab.is_cancel,
                    "call_type": collab.type,
                    "type": collab.type,
                    "slot_status": "",
                    "status": event_status,
                    "bookmark": False,
                    "created_at": local_time(collab.created_at).isoformat(),
                    "mentor": collab.speaker.pk,
                    "mentor_name": f"{collab.speaker.first_name} {collab.speaker.last_name}",
                    "mentor_avatar": collab.speaker.avatar.url,
                    "backgroundColor":"#3379FF",
                    "borderColor":"#3379FF",
                    "feedback_type":collab.type
                })
            collaborator_list.extend(calendar_data)
            collaborator_list = sorted(collaborator_list, key=lambda k: k['start_time'], reverse=True)
            response = {
                "message": "Success",
                "success": True,
                "data": collaborator_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class BookAppoinment(APIView):
    def post(self, request):
        data = request.data
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            response = {
                "message": "Success",
                "success": True,
                "data": ""
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": "Somthing Went Wrong", "success": False}, status=status.HTTP_400_BAD_REQUEST)


class UserMentor(APIView):
    def get(self, request, user_id):
        data = {"user_id": str(user_id)}
        # print(data)
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            if not self.request.query_params.get('company_id'):
                return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                company = Company.objects.get(id=self.request.query_params.get('company_id'))
            except Company.DoesNotExist:
                return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

            try:
                user = Learner.objects.get(id=user_id)
            except Learner.DoesNotExist:
                return Response({"message": "User not found or Invalid User Id"}, status=status.HTTP_404_NOT_FOUND)

            journeys = company_journeys("Learner", user, company.id)
            mentors_list = []
            assign_mentors = AssignMentorToUser.objects.filter(user=user, journey__in=journeys, journey__closure_date__gt=datetime.datetime.now()).values("mentor_id", "journey__title")
            # print("assin_mentor", assign_mentors)
            for assign_mentor in assign_mentors:
                mentors_list.append(assign_mentor['mentor_id'])
            mentor = Mentor.objects.filter(pk__in=mentors_list)
            mentor_list = []
            for mentor in mentor:
                bookmark = BookmarkMentor.objects.filter(user=user, mentor=mentor).first()
                journey = ""
                for data in assign_mentors:
                    if data['mentor_id'] == mentor.id:
                        journey = data['journey__title']
                industry_list = []
                expertize_list = []
                is_favourite = False

                if bookmark is not None:
                    is_favourite = bookmark.is_favourite

                for industry in mentor.industry.all():
                    industry_list.append(industry.name)
                for expertize in mentor.expertize.all():
                    expertize_list.append(expertize.name)

                mentor_list.append({
                    "id": mentor.id,
                    "email": mentor.email,
                    "first_name": mentor.first_name,
                    "last_name": mentor.last_name,
                    "gender": mentor.gender,
                    "age": mentor.age,
                    "current_status": mentor.current_status,
                    "position": mentor.position,
                    "expertize": expertize_list,
                    "industry": industry_list,
                    "avatar": mentor.avatar.url,
                    "about_us": mentor.about_us,
                    "profile_heading": mentor.profile_heading,
                    "is_favourite": is_favourite,
                    "username": mentor.username,
                    "phone": str(mentor.phone),
                    "room": get_chat_room(mentor, user),
                    "journey": journey
                     })

            response = {
                "message": "Success",
                "success": True,
                "data": mentor_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class add_favourite(APIView):

    def post(self, request):
        data = request.data
        serializer = addFavouriteSerializer(data=data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            mentor = serializer.validated_data['mentor']
            is_favourite = serializer.validated_data['is_favourite']
            bookmark = BookmarkMentor.objects.filter(
                user=user, mentor=mentor)
            if bookmark.count() > 0:
                BookmarkMentor.objects.filter(
                    user=user, mentor=mentor).update(is_favourite=is_favourite)

            else:
                BookmarkMentor.objects.create(
                    user=user, mentor=mentor, is_favourite=is_favourite)

            response = {
                "message": "Updated",
                "success": True,

            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class add_favouritelist(APIView):
    def post(self, request):
        data = request.data
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            user = serializer.validated_data['user_id']
            bookmark = BookmarkMentor.objects.filter(
                user=user, is_favourite=True)
            mentor_list = []
            for bookmark in bookmark:
                mentor = Mentor.objects.filter(pk=bookmark.mentor.pk)

                for mentor in mentor:
                    industry_list = []
                    expertize_list = []
                    for industry in mentor.industry.all():
                        industry_list.append(industry.name)
                    for expertize in mentor.expertize.all():
                        expertize_list.append(expertize.name)
                    mentor_list.append({

                        "id": mentor.id,
                        "email": mentor.email,
                        "first_name": mentor.first_name,
                        "last_name": mentor.last_name,
                        "gender": mentor.gender,
                        "age": mentor.age,
                        "current_status": mentor.current_status,
                        "position": mentor.position,
                        "expertize": expertize_list,
                        "industry": industry_list,
                        "avatar": mentor.avatar.url,
                        "about_us": mentor.about_us,
                        "profile_heading": mentor.profile_heading

                    })

            response = {
                "message": "Success",
                "success": True,
                "data": mentor_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class BookAppoinments(APIView):
    def post(self, request):
        data = request.data
        # print(datetime.datetime.now())
        serializer = BookAppoinmentSerializer(data=data)
        if serializer.is_valid():
            id = request.data['id']
            try:
                mentorCalendar.objects.get(pk=id)
            except mentorCalendar.DoesNotExist:
                return Response({"message": "Invalid Slot UUID or slot does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user_id = request.data['user_id']
            mentor_id = request.data['mentor_id']
            start_date_time = request.data['start_date_time']
            end_date_time = request.data['end_date_time']
            title = request.data['title']
            try:
                mentor = Mentor.objects.get(id=mentor_id)
            except Mentor.DoesNotExist:
                return Response({"message": "Invalid UUID or Mentor does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"message": "Invalid UUID or User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentorcal = mentorCalendar.objects.get(id=id)
            if mentorcal.is_cancel:
                return Response({"message": f"{mentorcal.title} slot is not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            data, meet_id = book_appointment(id, title, user, mentor, self.request.data['timezone'])
            add_participant_for_mentor_mentee_call(mentor, meet_id, host=True)
            add_participant_for_mentor_mentee_call(user, meet_id)
            if data['success'] == True:
                statuss = status.HTTP_200_OK
                return Response(data, status=statuss)
            else:
                statuss = status.HTTP_400_BAD_REQUEST
            return Response(data, status=statuss)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class CancelAppointment(APIView):
    def post(self, request):
        data = request.data
        # print(data)
        serializer = CancelAppoinmentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            timezone=None
            if data.get('timezone'):
                timezone=request.data['timezone']
            elif self.request.query_params.get('timezone'):
                timezone=self.request.query_params.get('timezone')
            id = request.data['id']
            user_id = request.data['user_id']
            mentor_id = request.data['mentor_id']
            # appointment_id = request.data['appointment_id']
            title = request.data['title']
            user = User.objects.get(id=user_id)
            try:
                mentor = Mentor.objects.get(id=mentor_id)
            except Mentor.DoesNotExist:
                return Response({"message": "Invalid UUID or Mentor does not exist"}, status=status.HTTP_404_NOT_FOUND)
            data = cancel_appointment(id, user, mentor, timezone)
            if data['success'] == True:
                statuss = status.HTTP_200_OK
            else:
                statuss = status.HTTP_400_BAD_REQUEST
            return Response(data, status=statuss)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)



class AvailableSlots(APIView):
    def post(self, request):
        data = request.data
        # print(data)
        serializer = AvailableSlotSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = request.data['user_id']
            date = request.data['date']
            mentor_id = request.data['mentor_id']
            try:
                participant = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({"message": "User not found", "Success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                company = Company.objects.get(pk=request.data['company_id'])
            except Company.DoesNotExist:
                return Response({"message": "Company not found", "Success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                mentor = Mentor.objects.get(pk=mentor_id)
            except Mentor.DoesNotExist:
                return Response({"message": "Mentor not found", "Success": False}, status=status.HTTP_404_NOT_FOUND)
            data = available_slots(participant, date, mentor=None, company=company, offset=self.request.data['timezone'])
            if data['Success']==True:
                statuss = status.HTTP_200_OK
            else:
                statuss = status.HTTP_404_NOT_FOUND
            return Response(data, status=statuss)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class WebAvaiableSlots(APIView):
    def post(self, request):
        data=request.data
        serializer = AvailableSlotSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = request.data['user_id']
            date = data.get('date') or ''
            try:
                company = Company.objects.get(pk=request.data['company_id'])
            except Company.DoesNotExist:
                return Response({"message": "Company not found", "Success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                participant = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({"message": "User not found", "Success": False}, status=status.HTTP_404_NOT_FOUND)
            data = available_slots(participant, date, mentor=None, company=company, offset=self.request.data['timezone'])
            if data['Success']==True:
                statuss = status.HTTP_200_OK
            else:
                statuss = status.HTTP_404_NOT_FOUND
            return Response(data, status=statuss)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)