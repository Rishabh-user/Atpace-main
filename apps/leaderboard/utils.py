from datetime import date, timedelta, datetime
import math
from apps.content.models import UserChannel, Channel
from apps.leaderboard.views import EndOfJourney, UserNextGoal, dashboardMentorshipGoal, UserBestStreak, \
    dashboardUserGoal
from apps.mentor.models import mentorCalendar, PoolMentor, AssignMentorToUser
from apps.users.models import Collabarate
from .models import UserBadgeDetails, UserEarnedPoints, UserEngagement, UserStreakHistory
from .userStreaks import userStreakCount
from django.contrib.auth.decorators import login_required
from django.db.models.query_utils import Q
from apps.users.utils import convert_to_local_time


def user_dashboard(user, type, offset=None):
    print(user, "user")
    try:
        user_points = UserEarnedPoints.objects.get(user=user)
        user_points = user_points.total_points
    except Exception:
        user_points = 0

    rank = UserEarnedPoints.objects.filter(total_points__gt=user_points).count()

    badges = UserBadgeDetails.objects.filter(user=user)[:5]

    streak_count = userStreakCount(user)

    assign_mentor = AssignMentorToUser.objects.filter(user=user, journey__closure_date__gt=datetime.now())
    mentor_list = [assign.mentor for assign in assign_mentor]
    calendar = mentorCalendar.objects.filter(mentor__in=mentor_list,
        participants__in=[user], is_cancel=False, start_time__gte=date.today())
    mentor_call_list = [{
        "id": calendar.id,
        "title": calendar.title,
        "url": calendar.url,
        "mentor": calendar.mentor.get_full_name(),
        "start_time": convert_to_local_time(calendar.start_time, offset),
        "end_time": convert_to_local_time(calendar.end_time, offset)
    }
        for calendar in calendar]

    user_company = user.company.all()
    user_channel = UserChannel.objects.filter(user=user, Channel__company__in=user_company, Channel__closure_date__gt=datetime.now())
    channel_id_list = [channel.Channel.id for channel in user_channel]
    collabarate = Collabarate.objects.filter(Q(participants__in=[user]), company__in=user_company, is_cancel=False,
                                            start_time__gte=date.today())
    # print("collabarate", collabarate.values())
    call_list = [{
        "id": collabarate.id,
        "title": collabarate.title,
        "custom_url": collabarate.custom_url,
        "speaker": collabarate.speaker.get_full_name(),
        "start_time": convert_to_local_time(collabarate.start_time, offset),
        "end_time": convert_to_local_time(collabarate.end_time, offset),
        "type": collabarate.type
    }
        for collabarate in collabarate]

    schedule_count = calendar.count() + collabarate.count()

    journeys = UserChannel.objects.filter(user=user, is_completed=False, status='Joined', Channel__is_active=True, 
                                          Channel__is_delete=False, is_removed=False, Channel__closure_date__gt=datetime.now())
    journey_data = []
    if journeys.count() > 0:
        for journey in journeys:
            if journey.Channel:
                result = EndOfJourney(user, journey.Channel.id)
                if result['status'] != 'Journey Not Found':
                    try:
                        progress = math.ceil(
                            (int(result['content_complete_count']) / int(result['content_count'])) * 100)
                    except Exception:
                        progress = 0
                    name = journey.Channel.title
                    journey_type = journey.Channel.channel_type
                    journey_id = journey.Channel.id
                    sub_channel = list(Channel.objects.filter(parent_id=journey_id))
                    for chanel in sub_channel:
                        print(chanel.pk, "sarthak")

                    journey_data.append({
                        "name": name,
                        "journey_type": journey_type,
                        "progress": progress,
                        "sub_channel": sub_channel
                    })

    engagement_seconds = 0
    login_time = date.today() - timedelta(days=7)
    user_engagement = UserEngagement.objects.filter(user=user, login_time__date__gte=login_time)
    for engage in user_engagement:
        seconds = (engage.logout_time - engage.login_time).seconds
        engagement_seconds = engagement_seconds + int(seconds)

    engagement_time_hr = int(engagement_seconds / 3600)
    engagement_time_week = int((engagement_seconds / 3600) / 7)

    if ((engagement_seconds / 3600) / 7 < 1):
        engagement_time = str(engagement_time_hr) + "h"
    else:
        engagement_time = str(engagement_time_week) + "h/Weekly"

    nextGoal = UserNextGoal(user, type)

    mentorship_goal = dashboardMentorshipGoal(user, type)
    user_goal = dashboardUserGoal(user, type)

    data = {
        "total_points": user_points,
        "user_rank": rank + 1,
        "badges": badges,
        "streak_count": streak_count,
        "best_streak": UserBestStreak(user),
        "schedule_count": schedule_count,
        "schedules": mentor_call_list,
        "collabarate": call_list,
        "today": date.today(),
        "journey_data": journey_data,
        "mentorship_goals": mentorship_goal['mentorship_goal_list'],
        "user_goals": user_goal['user_goal_list'],
        "user_goal_category_list": user_goal['category_list'],
        "category_list": mentorship_goal['category_list'],
        "engagement_time": engagement_time,
        "nextGoal": nextGoal,
    }
    return data


def mentor_dashboard(user, type, offset=None):
    try:
        user_points = UserEarnedPoints.objects.get(user=user)
        user_points = user_points.total_points
    except:
        user_points = 0

    rank = UserEarnedPoints.objects.filter(total_points__gt=user_points).count()

    badges = UserBadgeDetails.objects.filter(user=user)[:5]

    streak_count = userStreakCount(user)

    journeys = PoolMentor.objects.filter(pool__journey__closure_date__gt=datetime.now(),
        mentor=user, pool__journey__is_active=True, pool__journey__is_delete=False)
    journey_list = list(set([journey.pool.journey for journey in journeys]))
    journey_ids = list(set([journey.pool.journey.id for journey in journeys]))
    # print(f"journeys {journeys.values()}")
    # print(f"journey_ids {journey_ids}")
    calendar = mentorCalendar.objects.filter(
        mentor=user, is_cancel=False, slot_status="Booked", start_time__gte=date.today())
    mentor_call_list = [{
        "id": calendar.id,
        "title": calendar.title,
        "url": calendar.url,
        "mentor": calendar.mentor.get_full_name(),
        "start_time": convert_to_local_time(calendar.start_time, offset),
        "end_time": convert_to_local_time(calendar.end_time, offset)
    }
        for calendar in calendar]

    schedule_as_speaker = Collabarate.objects.filter(speaker=user,
        is_cancel=False, start_time__gte=date.today()).distinct()
    schedule_as_participants = Collabarate.objects.filter(participants__in=[user],
        is_cancel=False, start_time__gte=date.today()).distinct()
    shedule_list = schedule_as_participants | schedule_as_speaker
    print(shedule_list.values("title", "type"))
    

    # schedule_as_speaker = []
    schedule_as_participant = [{
        "id": collabarate.id,
        "title": collabarate.title,
        "custom_url": collabarate.custom_url,
        "speaker": collabarate.speaker.get_full_name(),
        "speaker_id": collabarate.speaker.id,
        "start_time": convert_to_local_time(collabarate.start_time, offset),
        "end_time": convert_to_local_time(collabarate.end_time, offset),
        "type": collabarate.type
    }
        for collabarate in shedule_list]

    # schedule_as_speakers = [{
    #     "id": collabarate.id,
    #     "title": collabarate.title,
    #     "custom_url": collabarate.custom_url,
    #     "speaker": collabarate.speaker.get_full_name(),
    #     "start_time": convert_to_local_time(collabarate.start_time, offset),
    #     "end_time": convert_to_local_time(collabarate.end_time, offset),
    #     "type": collabarate.type
    # }
    #     for collabarate in schedule_as_speaker]

    schedule_count = calendar.count() + schedule_as_participants.count()

    journey_data = []
    if journeys:
        journey_from = "pool_mentor"
        for journey in journey_list:
            result = EndOfJourney(user, journey.id)
            if result['status'] != 'Journey Not Found':
                try:
                    progress = math.ceil(
                        (int(result['content_complete_count']) / int(result['content_count'])) * 100)
                except:
                    progress = 0
                name = journey.title
                journey_data.append({
                    "name": name,
                    "progress": progress
                })
    else:
        journey_from = "user_channel"
        journeys = UserChannel.objects.filter(Channel__closure_date__gt=datetime.now(),
            user=user, is_completed=False, status='Joined', is_removed=False)
        if journeys:
            for journey in journeys:
                result = EndOfJourney(user, journey.Channel.id)
                if result['status'] != 'Journey Not Found':
                    try:
                        progress = math.ceil(
                            (int(result['content_complete_count']) / int(result['content_count'])) * 100)
                    except:
                        progress = 0
                    name = journey.Channel.title
                    journey_data.append({
                        "name": name,
                        "progress": progress
                    })

    engagement_seconds = 0
    login_time = date.today() - timedelta(days=7)
    user_engagement = UserEngagement.objects.filter(
        user=user, login_time__date__gte=login_time)
    for engage in user_engagement:
        seconds = (engage.logout_time - engage.login_time).seconds
        engagement_seconds = engagement_seconds + int(seconds)

    engagement_time_hr = int(engagement_seconds / 3600)
    engagement_time_week = int((engagement_seconds / 3600) / 7)

    if ((engagement_seconds / 3600) / 7 < 1):
        engagement_time = str(engagement_time_hr) + "h"
    else:
        engagement_time = str(engagement_time_week) + "h/Weekly"

    nextGoal = UserNextGoal(user, type, journey_from)
    mentorship_goal = dashboardMentorshipGoal(user, type)

    data = {
        "total_points": user_points,
        "user_rank": rank + 1,
        "badges": badges,
        "streak_count": streak_count,
        "best_streak": UserBestStreak(user),
        "schedule_count": schedule_count,
        "schedules": mentor_call_list,
        "today": date.today(),
        "journey_data": journey_data,
        "engagement_time": engagement_time,
        "nextGoal": nextGoal,
        "mentorship_goals": mentorship_goal['mentorship_goal_list'],
        "category_list": mentorship_goal['category_list'],
        "schedule_as_participants": schedule_as_participant,
        # "schedule_as_speaker": schedule_as_speakers

    }
    return data
