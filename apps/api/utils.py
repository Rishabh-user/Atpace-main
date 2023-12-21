import ast
from threading import Thread
import ast
import pandas as pd
from apps.utils.utils import url_shortner
from googletrans import Translator
import asyncio
from asgiref.sync import sync_to_async
from io import BytesIO
import random
from pytz import UTC as utc
import string
from django.core import files
from django.db.models.query_utils import Q
from werkzeug.utils import secure_filename
import boto3
from django.utils.timezone import localtime
from datetime import date, datetime, timedelta
import json
import math
import requests
from ravinsight.web_constant import BASE_URL
from rest_framework.authtoken.models import Token
from apps.atpace_community.utils import avatar, default_space_join_user, strf_format
from apps.content.models import Channel, ChannelGroup, ChannelGroupContent, Content, ContentData, SkillConfig, TestAttempt, UserChannel, UserCourseStart, UserTestAnswer
from apps.leaderboard.models import UserBadgeDetails, UserDrivenGoal, UserGoalLog, UserEngagement, UserStreakHistory
from apps.leaderboard.userStreaks import userStreakCount
from apps.leaderboard.views import AddUserStreak, EndOfJourney, NotificationAndPoints, UpdateUserStreakCount, UserNextGoal, UserBestStreak, UserSiteVisit, send_push_notification
from apps.mentor.models import AssignMentorToUser, PoolMentor, mentorCalendar, DyteAuthToken
from apps.survey_questions.models import SurveyLabel
from apps.test_series.models import TestOptions, TestQuestion, TestSeries
from apps.users.models import Collabarate, FirebaseDetails, Mentor, User, UserEarnedPoints, UserTypes, Company
from apps.users.utils import aware_time, local_time, register_email, send_call_booking_mail, clean_text, send_cancel_booking_mail, convert_to_local_time, convert_to_utc
from apps.video_calling.models import Room, RoomProperties
# from apps.video_calling.views import API_KEY
from ravinsight.settings import API_KEY
import jwt
from apps.vonage_api.utils import appointment_update_reminder, send_chat_info, appointment_cancel_reminder
from rest_framework.response import Response
from rest_framework import status
from ravinsight.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DYTE_ORG_ID, DYTE_API_KEY,DYTE_BASE_URL, DYTE_APP_URL
from apps.leaderboard.goal import user_progress_chart 
private_key = '5GqRnQc2a/XWAu3RJB46J+sYvsIHH6FbAYAtp5Y9WqwElKvp9aARBLSlaksGAhV/CAHBKFZ0kkmYMCb4r9kv/ohHP1Rvq7D8G4ZI1jT2xg1JS2rz8AESVwUl+GMsvZMp5LH7MUjKBZ29Jis4GkEW59HTcz/dpxGyWIIfp6SyWYKIv3cVhG1bWwFmzf7PD7fGCYU+m1FX29upU6njtS3dEBDEk2+5HzgqkaZWCVHsj7YuX8iNAtAKER+uwxcRKXwMS63Q9GFalIeaVflFoDflaJBdv0FnSis0LQamj35YZ4RN3/SpL6B3E9/ceHOoKgQd/i97P+eiCgdMAzegG6wZ3A=='


def get_user_profile_data(user):
    industry_list = []
    expertize_list = []
    user_type = ",".join(str(type.type) for type in user.userType.all())
    for industry in user.industry.all():
        industry_list.append(industry.name)
    for expertize in user.expertize.all():
        expertize_list.append(expertize.name)
    response = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': str(user.phone),
        'gender': user.gender,
        'age': user.age,
        'user_type': user_type,
        'private_profile': user.private_profile,
        'about_us': user.about_us,
        'profile_heading': user.profile_heading,
        'prefer_not_say': user.prefer_not_say,
        'organization': user.organization,
        'current_status': user.current_status,
        'position': user.position,
        'expertize': expertize_list,
        "avatar": user.avatar.url,
        "user_profile_image": avatar(user),
        'industry': industry_list,
        'linkedin_profile': user.linkedin_profile,
        "favourite_way_to_learn": user.favourite_way_to_learn,
        "interested_topic": user.interested_topic,
        "upscaling_reason": user.upscaling_reason,
        "time_spend": user.time_spend,
        "city": user.city,
        "state": user.state,
        "country": user.country,
        "is_email_private":user.is_email_private,        
        "is_phone_private":user.is_phone_private,
        "is_linkedin_private":user.is_linkedin_private,        
    }
    return response


def assessment_attempt_channel(user, journey, channel_group):
    channel_group = channel_group
    test_attempt = TestAttempt.objects.filter(user=user, channel=journey.parent_id, test=channel_group.post_assessment)
    if len(test_attempt) > 0:
        assessment_attempt = test_attempt.first()

        try:
            assessment_attempt_marks = math.ceil(
                (assessment_attempt.total_marks / assessment_attempt.test_marks) * 100)
        except Exception:
            assessment_attempt_marks = assessment_attempt.total_marks

        if assessment_attempt_marks < channel_group.end_marks:
            channel_group = channel_group
        else:
            channel_group = ChannelGroup.objects.filter(channel=journey,
                                                        start_mark__lte=assessment_attempt_marks, end_marks__gte=assessment_attempt_marks)
    return channel_group


def get_journey_content(journey, user):
    channel_group = ChannelGroup.objects.filter(channel=journey, is_delete=False)
    if journey.channel_type == "SkillDevelopment":
        if journey.is_test_required:
            assessment_attempt = TestAttempt.objects.filter(
                user=user, channel=journey.parent_id, test=journey.test_series)
            if len(assessment_attempt) > 0:
                assessment_attempt = assessment_attempt.first()

                try:
                    assessment_attempt_marks = math.ceil(
                        (assessment_attempt.total_marks / assessment_attempt.test_marks) * 100)
                except Exception:
                    assessment_attempt_marks = assessment_attempt.total_marks

                channel_group = channel_group.filter(
                    start_mark__lte=assessment_attempt_marks, end_marks__gte=assessment_attempt_marks)
                marks = assessment_attempt.total_marks
                if journey.parent_id is not None:
                    channel = []
            else:
                channel_group = []
        else:
            assessment_attempt = TestAttempt.objects.filter(
                user=user, channel=journey, test=journey.test_series)

            level = "Level 1"
            if len(assessment_attempt) > 0:
                assessment_attempt = assessment_attempt.first()
                level = assessment_attempt.user_skill

            level = SurveyLabel.objects.get(label=level)
            channel_group = ChannelGroup.objects.filter(channel=journey, channel_for=level, is_delete=False)
    channel_group_content_list = []
    InProgress = 0
    Complete = 0
    temp = 0
    for channel_group in channel_group:
        channel_group_content = ChannelGroupContent.objects.filter(channel_group=channel_group, content__status="Live", is_delete=False)
        for channel_group_content in channel_group_content:
            content_data_list = []
            content_data = ContentData.objects.filter(content=channel_group_content.content)
            course_start = UserCourseStart.objects.filter(
                user=user, content=channel_group_content.content, channel_group=channel_group, channel=journey).first()
            if course_start is not None:
                read_status = course_start.status

                if read_status == "InProgress":
                    InProgress = InProgress + 1
                elif read_status == "Complete":
                    Complete = Complete + 1
                else:
                    temp = temp + 1

            else:
                read_status = ""

            # if read_status != "":
            for content_data in content_data:
                content_data_list.append({
                    "id": content_data.id,
                    "title": content_data.title,
                    "read_status": read_status,
                    "time": content_data.time
                })

            channel_group_content_list.append({
                "id": channel_group_content.content.pk,
                "level": channel_group.channel_for.label if channel_group.channel_for else "",
                "journey_group": channel_group.pk,
                "content": channel_group_content.content.title,
                "data": content_data_list,
                "read_status": read_status,
                "post_assessment": channel_group.post_assessment.pk if channel_group.post_assessment else "",
            })

    content = channel_group_content_list
    if InProgress > Complete:
        skill_status = "InProgress"
    elif Complete > InProgress:
        skill_status = "Complete"
    else:
        skill_status = ""

    return content, skill_status


def skill_assessment(journey, assessment_id, user, channel_group, type, quest=None):
    status = time = ''
    assessment = TestSeries.objects.get(id=assessment_id)
    if type == "journey_pre_assessment":
        test_attempt = TestAttempt.objects.filter(test=assessment, user=user, channel=journey, type=type)
    else:
        test_attempt = TestAttempt.objects.filter(
            test=assessment, user=user, channel=journey.parent_id, type=type, skill_id=journey.id, quest_id=quest)
    if test_attempt.count() > 0:
        status = "Complete"
        time = test_attempt.first().created_at

    progress = {
        "content": assessment.name,
        "status": status,
        "type": type,
        "start_time": time,
        "week_delayed": "",
        "display_order": 1,
        "journey_group": journey.id if type == "journey_pre_assessment" else channel_group.pk,
        "quest_id": assessment.id
    }
    return progress


def get_journey_progress(journey, user):
    channel_group = ChannelGroup.objects.filter(channel=journey, is_delete=False)
    progress = []
    type = status = time = quest_id = ''

    if journey.channel_type == "SkillDevelopment":
        try:
            user_channel = UserChannel.objects.get(Channel=journey.parent_id, user=user, status="Joined")
            alloted = user_channel.is_alloted
        except Exception:
            alloted = ""
        if journey.is_test_required:
            skill_config = SkillConfig.objects.filter(channel=journey.parent_id)
            for skill in skill_config:
                if skill.journey_pre_assessment_id and not alloted:
                    type = "journey_pre_assessment"
                    progress.append(skill_assessment(journey.parent_id,
                                                     skill.journey_pre_assessment_id, user, channel_group.first(), type))
            assessment_attempt = TestAttempt.objects.filter(skill_id=journey.id,
                                                            user=user, channel=journey.parent_id, test=journey.test_series)
            type = "pre_assessment"
            if len(assessment_attempt) > 0:
                status = "Complete"
                assessment_attempt = assessment_attempt.first()

                try:
                    assessment_attempt_marks = math.ceil(
                        (assessment_attempt.total_marks / assessment_attempt.test_marks) * 100)
                except Exception:
                    assessment_attempt_marks = assessment_attempt.total_marks

                channel_group = channel_group.filter(
                    start_mark__lte=assessment_attempt_marks, end_marks__gte=assessment_attempt_marks)
                marks = assessment_attempt.total_marks
                if journey.parent_id is not None:
                    channel = []
            else:
                channel_group = []
            progress.append({
                "content": journey.test_series.name,
                "status": status,
                "type": type,
                "start_time": assessment_attempt.created_at if assessment_attempt else '',
                "week_delayed": "",
                "display_order": 1,
                "journey_group": journey.id,
                "quest_id": journey.test_series.id
            })

        else:
            assessment_attempt = TestAttempt.objects.filter(
                user=user, channel=journey, test=journey.test_series)

            level = "Level 1"
            if len(assessment_attempt) > 0:
                assessment_attempt = assessment_attempt.first()
                level = assessment_attempt.user_skill

            level = SurveyLabel.objects.get(label=level)
            channel_group = ChannelGroup.objects.filter(channel=journey, channel_for=level, is_delete=False)

    for channel_group in channel_group:
        # if journey.channel_type == "SkillDevelopment":
        #     channel_group=assessment_attempt_channel(user, journey, channel_group).first()
        channel_group_content = ChannelGroupContent.objects.filter(channel_group=channel_group, content__status="Live", is_delete=False)
        for channel_group_content in channel_group_content:
            course_start = UserCourseStart.objects.filter(
                user=user, content=channel_group_content.content, channel_group=channel_group, channel=journey).first()
            quest_id = channel_group_content.content.pk
            type = "quest"
            if not course_start:
                content = channel_group_content.content.title
                status = ""
                time = ""
            elif course_start:
                content = course_start.content.title
                status = course_start.status
                time = course_start.created_at

            progress.append({
                "content": content,
                "status": status,
                "type": type,
                "start_time": time,
                "week_delayed": "",
                "display_order": channel_group_content.display_order,
                "journey_group": channel_group.pk,
                "quest_id": quest_id
            })

            if channel_group_content.channel_group.post_assessment:
                type = "post_assessment"
                progress.append(skill_assessment(journey, channel_group_content.channel_group.post_assessment.id,
                                                 user, channel_group, type, quest=channel_group_content.content.pk))

    return progress


def User_firebase_details(user, id, token):
    try:
        firebase_details = FirebaseDetails.objects.get(user=user, device_id=id)
        firebase_details.firebase_token = token
        firebase_details.save()
    except FirebaseDetails.DoesNotExist:
        return FirebaseDetails.objects.create(user=user, device_id=id, firebase_token=token)
    return False

def call_slot_status(slots, offset):
    current_time = utc.localize(datetime.combine(datetime.now(), datetime.min.time()))
    current_time = convert_to_local_time(current_time, offset)
    end_time = convert_to_local_time(slots.end_time, offset)
    if slots.is_cancel:
        return "Cancelled"
    elif slots.slot_status == "Booked" and end_time < current_time:
        if slots.status == "Completed":
            return "Completed"
        return "Expired"
    elif slots.slot_status == "Available" and end_time < current_time:
        return "Not Available"
    else:
        return slots.slot_status

def call_status(slots, offset):
    current_time = utc.localize(datetime.combine(datetime.now(), datetime.min.time()))
    current_time = convert_to_local_time(current_time, offset)
    end_time = convert_to_local_time(slots.end_time, offset)
    if slots.is_cancel and slots.slot_status == "Booked":
        return "Cancelled"
    elif (not slots.is_cancel and slots.slot_status == "Booked") and (end_time > current_time):
        return "Upcoming"
    elif (not slots.is_cancel and slots.slot_status == "Booked") and (end_time < current_time):
        return "Completed"
    elif slots.slot_status == "Available":
        return ""

def available_slots(participant, date, mentor=None, company=None, offset=None):
    slot = []
    avaliable_slot = []
    mentor_list = [mentor]
    if not mentor:
        mentors = Mentor.objects.filter(company=company)
        assign_mentors = AssignMentorToUser.objects.filter(user=participant, mentor__in=mentors, is_assign=True, is_revoked=False, journey__closure_date__gt=datetime.now())
        mentor_list = [assign_mentor.mentor for assign_mentor in assign_mentors]
    if date == "":
        available_slots = mentorCalendar.objects.filter(mentor__in=mentor_list, slot_status="Available",
                                                        start_time__gte=datetime.now()).order_by('-start_time')
        booked_slots = mentorCalendar.objects.filter(mentor__in=mentor_list, slot_status="Booked", participants=participant).order_by('-start_time')
    else:
        available_slots = mentorCalendar.objects.filter(mentor__in=mentor_list, slot_status="Available", start_time__date=date).order_by('-start_time')
        booked_slots = mentorCalendar.objects.filter(mentor__in=mentor_list, slot_status="Booked", participants=participant,
                                                     start_time__date=date, status="Upcoming").order_by('-start_time')
    if len(booked_slots) > 0:
        for slots in booked_slots:
            slot.append({
                "id": slots.pk,
                "title": slots.title,
                "description": slots.description,
                "mentor_id": slots.mentor.id,
                "mentor_name": f"{slots.mentor.first_name} {slots.mentor.last_name}",
                "start_time": convert_to_local_time(slots.start_time, offset).isoformat(),
                "end_time": convert_to_local_time(slots.end_time, offset).isoformat(),
                "status": call_slot_status(slots, offset),
                "call_status": call_status(slots, offset),
                "is_cancel": slots.is_cancel,
            })
    if len(available_slots) > 0:
        for slots in available_slots:
            slot.append({
                "id": slots.pk,
                "title": slots.title,
                "description": slots.description,
                "mentor_id": slots.mentor.id,
                "mentor_name": f"{slots.mentor.first_name} {slots.mentor.last_name}",
                "start_time": convert_to_local_time(slots.start_time, offset).isoformat(),
                "end_time": convert_to_local_time(slots.end_time, offset).isoformat(),
                "status": call_slot_status(slots, offset),
                "call_status": call_status(slots, offset),
                "is_cancel": slots.is_cancel,
            })

    if len(slot) == 0:
        data = {
            "message": "No slots available, Please comeback later",
            "Success": True
        }
        return data

    data = {
        "message": "Available Slots",
        "response": slot,
        "Success": True
    }
    return data


#  dyte integration for book appointment 
def book_appointment(id, title, user, mentor, offset):
    payload = json.dumps({
        "title": str(title),
        "preferred_region":"ap-southeast-1",
        "record_on_start": False,
	    "live_stream_on_start": False
    })

    # create meeting
    url = f"{DYTE_BASE_URL}/meetings"
    response = requests.request("POST", url, data=payload, auth=(DYTE_ORG_ID, DYTE_API_KEY), headers={"Content-Type": "application/json"})
    if response.status_code == 400 or response.status_code == 422:
        data = {"message": "Bad request or Unprocessable Entity", "success": False, }
        return data
    # generate the meet url after creating meeting
    if response.status_code == 200 or response.status_code == 201:
        meet_id = response.json()['data']['id']
        meet_url = f"{BASE_URL}/config/dyte/{meet_id}"

    mentorcal = mentorCalendar.objects.get(id=id)
    mentorCal = mentorCalendar.objects.filter(pk=mentorcal.pk)
    mentorCal.update(url=meet_url, slot_status="Booked", url_title=meet_id)
    mentorCal = mentorCal.first()
    if user.phone and user.is_whatsapp_enable:
        meeting_notification(user, "Meeting with coach", "New meeting scheduled")
        meeting_notification(mentorCal.mentor, "Meeting with coache", "New meeting scheduled")
        appointment_update_reminder(user, user, mentorCal.mentor, convert_to_local_time(mentorCal.start_time, offset), url_shortner(meet_url, BASE_URL))
    if mentorCal is not None:
        mentorCal.participants.add(user)
    else:
        data = {"message": "Please Verify Mentor Available Slots", "success": False}
        return data
    NotificationAndPoints(user=user, title="meeting with coach")
    output_response = {
        "message": "Booked",
        "meeting_url": url_shortner(meet_url, BASE_URL),
        "success": True,
        }
    return output_response, meet_id

def meeting_notification(user, title, description):
    context = {
        "screen": "Calendar",
    }
    send_push_notification(user, title, description, context)
    return True

def cancel_appointment(id, user, mentor, offset):
    mentorCal = mentorCalendar.objects.filter(pk=id)

    mentorcal = mentorCal.first()
    mentorCal.update(cancel_by=user.username, cancel_by_id=user.id, is_cancel=True, status="Cancelled")
    mentor_details = mentorcal.mentor
    if user.phone and user.is_whatsapp_enable:
        context = {
            "screen": "AppointmentScheduling",
            "navigationPayload":{
                "mentor_id": str(mentorcal.mentor.id)
            }
        }
        send_push_notification(user, "Appointment Cancelled", mentorcal.title, context)
        appointment_cancel_reminder(user, user, mentorcal.mentor, convert_to_local_time(mentorcal.start_time, offset))
        send_cancel_booking_mail(user, mentor_details, user.email, mentor_details.first_name, user.first_name,
                                 convert_to_local_time(mentorcal.start_time, offset), mentorcal.title, offset)
    data = {
        "message": "Cancelled",
        "success": True
    }

    return data


# def create_token(user):
#     name = f"{user.first_name} {user.last_name}"
#     user_data = {
#         'sub': str(user.id),
#         'email': user.email,
#         'name': name,
#         'password': user.password,
#     }
#     return jwt.encode(user_data, private_key, algorithm='HS256')


def survey_upload(file, bucket):
    file_name = secure_filename(file.name)
    s3 = boto3.client('s3', AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    response = s3.upload_file(file_name, bucket, f"surveys/{file_name}")
    return response


def badge_image(current_badge):
    if current_badge.image:
        avatar = str(current_badge.image.url)
        avatar = avatar.split('?')
        return avatar[0]
    else:
        return ''


def journey_image(journey):
    if journey.image:
        journey_image = str(journey.image.url)
        journey_image = journey_image.split('?')
        return journey_image[0]
    else:
        return ''


def user_journey_data(user, journey):
    result = EndOfJourney(user, journey.id)
    if result['status'] != 'Journey Not Found':
        try:
            progress = math.ceil(
                (int(result['content_complete_count'])/int(result['content_count']))*100)
        except Exception:
            progress = 0

        return {
            "id": journey.id,
            "name": journey.title,
            "progress": progress,
            "thumbnail": journey_image(journey)
        }
    return ''


def user_dashboard_api(user, type, company_id=None):
    if company_id:
        company = user.company.filter(id=company_id)
    try:
        user_points = UserEarnedPoints.objects.get(user=user)
        user_points = user_points.total_points
    except Exception:
        user_points = 0

    rank = UserEarnedPoints.objects.filter(total_points__gt=user_points).count()

    badges = UserBadgeDetails.objects.filter(user=user)
    badges_list = [{"current_badge": badge.current_badge.name, "badge_image": badge_image(badge.current_badge), "badge_label": badge.current_badge.label.label,
                    "points_earned": badge.points_earned, "badge_acquired": badge.badge_acquired, "badge_revoked": badge.badge_revoked} for badge in badges]

    calendars = mentorCalendar.objects.filter(Q(participants__in=[user]) | Q(
        mentor=user), is_cancel=False, start_time__gte=datetime.combine(date.today(), datetime.min.time()), company=company.first())
    calendar_list = []
    for calendar in calendars:
        participants = [{"participant_name": f"{participant.first_name} {participant.last_name}", "participant_id": participant.id,
                         "participant_avatar": avatar(participant)} for participant in calendar.participants.all()]
        calendar_list.append({
            "id": calendar.id,
            "title": calendar.title,
            "start_time": local_time(calendar.start_time).isoformat(),
            "end_time": local_time(calendar.end_time).isoformat(),
            "speaker": f"{calendar.mentor.first_name} {calendar.mentor.last_name}",
            "speaker_id": calendar.mentor.id,
            "meet_url": calendar.url,
            "slot_status": calendar.slot_status,
            "call_type": "Mentor Meeting",
            "status": calendar.status,
            "is_bookmark": calendar.bookmark,
            "participant": participants,
            "created_by": calendar.created_by,
            "created_by_id": calendar.created_by_id,
            "feedback_type":"MentorCall"
        })
    collabarate = Collabarate.objects.filter(Q(participants__in=[user]) | Q(
                company=company.first()) | Q(speaker=user), is_active=True).distinct()
    # print(collabarate)
    schedule_count = calendars.count() + collabarate.count()
    for collaborate in collabarate:
        participants = [{"participant_name": f"{participant.first_name} {participant.last_name}", "participant_id": participant.id,
                         "participant_avatar": avatar(participant)} for participant in collaborate.participants.all()]
        current_time = aware_time(datetime.combine(date.today(), datetime.min.time()))
        if collaborate.is_cancel:
            event_status = "Cancelled"
        elif collaborate.start_time >= current_time:
            event_status = "Upcoming"
        else:
            event_status = "Completed"
        calendar_list.append({
            "id": collaborate.id,
            "title": collaborate.title,
            "start_time": local_time(collaborate.start_time).isoformat(),
            "end_time": local_time(collaborate.end_time).isoformat(),
            "speaker": f"{collaborate.speaker.first_name} {collaborate.speaker.last_name}",
            "speaker_id": collaborate.speaker.id,
            "meet_url": collaborate.custom_url,
            "slot_status": "",
            "call_type": collaborate.type,
            "status": event_status,
            "is_bookmark": "",
            "participant": participants,
            "created_by": f"{collaborate.created_by.first_name} {collaborate.created_by.last_name}",
            "created_by_id": collaborate.created_by.id,
            "feedback_type": collaborate.type
        })
    journey_from = ""
    journey_data = []
    user_journeys = UserChannel.objects.filter(user=user, is_completed=False, status='Joined', Channel__company__in=company,
                                               Channel__is_active=True, Channel__is_delete=False,  is_removed=False)
    if type == "Learner" and user_journeys.count() > 0:
        journey_from = "user_channel"
        for journey in user_journeys:
            journey_data.append(user_journey_data(user, journey.Channel))
    elif type == "Mentor":
        mentor_journeys = PoolMentor.objects.filter(pool__journey__company__in=company,
            mentor=user, pool__journey__is_active=True, pool__journey__is_delete=False)
        journey_from = "pool_mentor"
        for journey in mentor_journeys:
            journey_data.append(user_journey_data(user, journey.pool.journey))
    else:
        journey_from = "user_channel"
        for journey in user_journeys:
            journey_data.append(user_journey_data(user, journey.Channel))
  
    streak = Thread(target=userStreakCount, args=[user,])
    streak.start()
    streak_count = streak.join()

    best = Thread(target=UserBestStreak, args=[user,])
    best.start()
    best_streak = best.join()

    goal = Thread(target=UserNextGoal, args=[user,type,journey_from,])
    goal.start()
    nextGoal = goal.join()

    engagement_seconds = 0
    login_time = date.today() - timedelta(days=7)
    user_engagement = UserEngagement.objects.filter(user=user, login_time__date__gte=login_time)
    for engage in user_engagement:
        seconds = (engage.logout_time - engage.login_time).seconds
        engagement_seconds = engagement_seconds + int(seconds)

    engagement_time_hr = int(engagement_seconds/3600)
    engagement_time_week = int((engagement_seconds/3600)/7)

    if ((engagement_seconds/3600)/7 < 1):
        engagement_time = str(engagement_time_hr) + " Hours"
    else:
        engagement_time = str(engagement_time_week) + " Hours/Weekly"

    return {
        "user_id": user.id,
        "user_roles": [user_type.type for user_type in user.userType.all()],
        "name": f"{user.first_name} {user.last_name}",
        "total_points": user_points,
        "user_rank": rank+1,
        "badges": badges_list,
        "streak_count": streak_count,
        "best_streak": best_streak,
        "schedule_count": schedule_count,
        "schedules": calendar_list,
        "today": date.today(),
        "journey_data": journey_data,
        "engagement_time": engagement_time,
        "nextGoal": nextGoal
    }


def survey_file(obj):
    if obj.upload_file:
        avatar = str(obj.upload_file.url)
        avatar = avatar.split('?')
        return avatar[0]
    else:
        return ''


def survey_upload_file(file):
    response = requests.get(file)
    response.raw.decode_content = True
    file_name = str(file).split('/')[-1]
    if response.status_code == 200:
        fp = BytesIO()
        fp.write(response.content)
        return file_name, files.File(fp)
    return None


def mentorship_goal_list(user, type, company=None):
    mentorship_goal_list = []
    mentorship_goal_chart = []

    if type == "Mentor":
        mentorship_goals = UserDrivenGoal.objects.filter(
            created_by=user, is_deleted=False, goal_type="Mentorship", is_active=True)

        for goal in mentorship_goals:
            assigned_to = []
            comment_list = []
            approve_request_list = []
            for learner in goal.learners.all():
                assigned_to.append({
                    "id": learner.id,
                    "name": f"{learner.first_name} {learner.last_name}",
                    "avatar": avatar(learner)

                })
            for comment in goal.comment.all():
                comment_list.append({
                    "id": comment.id,
                    "comment": comment.comment,
                    "created_by_id": comment.created_by.pk,
                    "created_by": f"{comment.created_by.first_name} {comment.created_by.last_name}",
                    "avatar": avatar(comment.created_by),
                    "created_at": comment.created_at
                })

            for req in goal.approve_request.all():
                approve_request_list.append({
                    "id": req.pk,
                    "name": f"{req.first_name} {req.last_name}",
                    "avatar": avatar(req)

                })

            if (goal.complete_till > aware_time(datetime.now())):
                expired = False
            else:
                expired = True

            mentorship_goal_list.append({
                "goal_id": goal.id,
                "heading": goal.heading,
                "description": goal.description,
                "assigned_to": assigned_to,
                "duration_number": goal.duration_number,
                "duration_time": goal.duration_time,
                "category": goal.category,
                "priority": goal.priority_level,
                "due_date": goal.complete_till,
                "comment": comment_list,
                "goal_type": goal.goal_type,
                "difficulty_level": goal.difficulty_level,
                "approve_request": approve_request_list,
                "is_expired": expired,
                "created_by": f"{goal.created_by.first_name} {goal.created_by.last_name}",
                "created_by_id": goal.created_by.id
            })

            requested = UserGoalLog.objects.filter(goal=goal, status='RequestForApprove').count()
            rejected = UserGoalLog.objects.filter(goal=goal, status='RejectedByMentor').count()
            approved = UserGoalLog.objects.filter(goal=goal, status='ApprovedByMentor').count()

            mentorship_goal_chart.append({
                "goal_heading": goal.heading,
                "requested": requested,
                "rejected": rejected,
                "approved": approved
            })

        data = {
            "mentorship_goal_list": mentorship_goal_list,
            "mentorship_goal_chart": mentorship_goal_chart
        }

        return data

    elif type == "Learner":
        assign_users = AssignMentorToUser.objects.filter(user=user, mentor__company__in=[company])
        mentor_list = [assign_user.mentor for assign_user in assign_users]
        mentorship_goals = UserDrivenGoal.objects.filter(created_by__in=mentor_list,
            learners__in=[user], is_deleted=False, goal_type="Mentorship", is_active=True)

        for goal in mentorship_goals:
            comment_list = []

            for comment in goal.comment.all():
                comment_list.append({
                    "id": comment.id,
                    "comment": comment.comment,
                    "created_by_id": comment.created_by.pk,
                    "created_by": f"{comment.created_by.first_name} {comment.created_by.last_name}",
                    "avatar": avatar(comment.created_by),
                    "created_at": comment.created_at
                })

            if (goal.complete_till > aware_time(datetime.now())):
                expired = False
            else:
                expired = True

            goal_log = UserGoalLog.objects.filter(user=user, goal=goal).first()

            mentorship_goal_list.append({
                "goal_id": goal.id,
                "heading": goal.heading,
                "description": goal.description,
                "duration_number": goal.duration_number,
                "duration_time": goal.duration_time,
                "category": goal.category,
                "priority": goal.priority_level,
                "due_date": goal.complete_till,
                "comment": comment_list,
                "goal_type": goal.goal_type,
                "difficulty_level": goal.difficulty_level,
                "status": goal_log.status if goal_log else "Not Started",
                "progress": goal_log.progress_percentage if goal_log else 0,
                "is_expired": expired,
                "created_by": f"{goal.created_by.first_name} {goal.created_by.last_name}",
                "created_by_id": goal.created_by.id
            })

        return mentorship_goal_list


def mentorship_goal_detail(goal, user, type):
    mentorship_goal = []

    if type == "Mentor":

        assigned_to = []
        comment_list = []
        approve_request_list = []
        for learner in goal.learners.all():
            assigned_to.append({
                "id": learner.id,
                "name": f"{learner.first_name} {learner.last_name}",
                "avatar": avatar(learner)
            })
        for comment in goal.comment.all():
            comment_list.append({
                "id": comment.id,
                "comment": comment.comment,
                "created_by_id": comment.created_by.pk,
                "created_by": f"{comment.created_by.first_name} {comment.created_by.last_name}",
                "avatar": avatar(comment.created_by),
                "created_at": comment.created_at

            })

        for req in goal.approve_request.all():
            approve_request_list.append({
                "id": req.pk,
                "name": f"{req.first_name} {req.last_name}",
                "avatar": avatar(req)
            })

        if (goal.complete_till > aware_time(datetime.now())):
            expired = False

        else:
            expired = True

        mentorship_goal = {
            "goal_id": goal.id,
            "heading": goal.heading,
            "description": goal.description,
            "assigned_to": assigned_to,
            "duration_number": goal.duration_number,
            "duration_time": goal.duration_time,
            "category": goal.category,
            "priority": goal.priority_level,
            "due_date": goal.complete_till,
            "comment": comment_list,
            "goal_type": goal.goal_type,
            "difficulty_level": goal.difficulty_level,
            "approve_request": approve_request_list,
            "is_expired": expired,
            "user_goal_progress_chart": user_progress_chart(goal)

        }

        return mentorship_goal

    elif type == "Learner":

        comment_list = []

        for comment in goal.comment.all():
            comment_list.append({
                "id": comment.id,
                "comment": comment.comment,
                "created_by_id": comment.created_by.pk,
                "created_by": f"{comment.created_by.first_name} {comment.created_by.last_name}",
                "avatar": avatar(comment.created_by),
                "created_at": comment.created_at

            })

        goal_log = UserGoalLog.objects.filter(user=user, goal=goal).first()

        if (goal.complete_till > aware_time(datetime.now())):
            expired = False

        else:
            expired = True

        mentorship_goal = {
            "goal_id": goal.id,
            "heading": goal.heading,
            "description": goal.description,
            "duration_number": goal.duration_number,
            "duration_time": goal.duration_time,
            "category": goal.category,
            "priority": goal.priority_level,
            "due_date": goal.complete_till,
            "comment": comment_list,
            "goal_type": goal.goal_type,
            "difficulty_level": goal.difficulty_level,
            "status": goal_log.status if goal_log else "Not Started",
            "progress": goal_log.progress_percentage if goal_log else 0,
            "is_expired": expired

        }

        return mentorship_goal


def update_boolean(value):
    if value == "true":
        return True
    elif value == "false":
        return False
    else:
        return value


def social_type(user, social_login_type, google_account_id=None, facebook_account_id=None):
    user.social_login_type = social_login_type
    user.is_social_login = True
    if not user.is_active:
        user.is_active = True
    if social_login_type == "Facebook":
        user.facebook_account_id = facebook_account_id
    elif social_login_type == "Google":
        user.google_account_id = google_account_id
        if not user.is_email_verified:
            user.is_email_verified = True
    user.save()
    return user


def get_or_create_user(first_name, last_name, email, social_login_type, user_type, avatar, google_account_id=None, facebook_account_id=None):
    if user := User.objects.filter(email__iexact=email).first():
        if user.is_social_login:
            if user.social_login_type != social_login_type:
                return f"You're already registered with {user.social_login_type}. Please try to Login with {user.social_login_type} or using Email & Password"
            return user
        return social_type(user, social_login_type, google_account_id, facebook_account_id)
    else:
        user = User.objects.create(first_name=first_name, last_name=last_name, email=email,
                                   username=email, is_term_and_conditions_apply=True)
        user.is_active = True
        if avatar:
            user.avatar = avatar
        password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
        # print(password)
        user.set_password(password)
        user.save()
        social_type(user, social_login_type, google_account_id, facebook_account_id)
        user_type = UserTypes.objects.filter(type=user_type).first()
        if not user_type:
            return f"Invalid user_type"
        user.userType.add(user_type.id)
        default_space_join_user(user)
        NotificationAndPoints(user, "registration")
        register_email(user, password)
    UserSiteVisit(user)
    UpdateUserStreakCount(user)
    AddUserStreak(user)
    return user


def check_valid_user(user_id):
    try:
        user = User.objects.get(pk=user_id)
        #  # print(user)
    except User.DoesNotExist:
        return False
    return user


@sync_to_async
def chat_notification(to_user, message, room):
    context = {
        "screen":"ChatScreen",
        "navigationPayload":{
            "room_name": room.name,
            "recipient_avatar": avatar(to_user),
            "recipient_name": f"{to_user.first_name} {to_user.last_name}"
        }
    }
    context = {
        "screen":"ChatScreen"
    }
    send_push_notification(to_user, "New Message Received", message, context)
    if to_user.phone and to_user.is_whatsapp_enable:
        send_chat_info(to_user, message)


@sync_to_async
def room_members(room, from_user):
    members = room.members.filter(~Q(pk=from_user.id))
    return members


class AsyncIter:
    def __init__(self, items):
        self.items = items

    async def __aiter__(self):
        for item in self.items:
            yield item

def translate_data(to_lang, text, from_lang="auto"):
    translator = Translator()
    translate = translator.translate(text, src=from_lang, dest=to_lang)
    return [text.text for text in translate]

def assessment_data_sheet(journey):
    test_attempt = TestAttempt.objects.filter(channel=journey)
    user_test_answer = UserTestAnswer.objects.filter(test_attempt__in=test_attempt).order_by('created_at')
    data_list = []
    for test_answer in user_test_answer:
        quest_name = ""
        if test_answer.test_attempt.quest_id:
            microskill = Content.objects.get(id=test_answer.test_attempt.quest_id)
            quest_name = microskill.title
        attempt_response = test_answer.response
        if test_answer.question.type == "checkbox":
            try:
                ids = ast.literal_eval(test_answer.response)
                if not isinstance(test_answer.response, str):
                    # print(f"test_answer.response: {test_answer.response}")
                    temp = TestOptions.objects.filter(pk__in=ids)
                    attempt_response = ",".join(temp.option for temp in temp)
            except Exception as e:
                print(e)
                attempt_response = test_answer.response
        data_list.append([test_answer.test_attempt.id, test_answer.test_attempt.test.name, test_answer.question.title, attempt_response, test_answer.question_marks, test_answer.total_marks, journey.title, test_answer.test_attempt.type, strf_format(test_answer.test_attempt.created_at), test_answer.user.username, quest_name, test_answer.question.pk])

    return data_list
