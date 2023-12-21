from apps.community.models import LearningJournals
from apps.test_series.models import TestSeries
from apps.survey_questions.models import Survey, SurveyAttempt
from django import template
import datetime
from django.db.models import Q
from apps.mentor.models import PoolMentor, AssignMentorToUser, mentorCalendar
from apps.leaderboard.models import UserEarnedPoints
from apps.content.models import Channel, Content, TestAttempt, UserChannel, MentoringJourney
from apps.users.models import Collabarate, User

register = template.Library()


# Journy

@register.filter(name="total_journy")
def total_journy(user):
    total_channel = Channel.objects.filter(is_delete=False, parent_id=None).count()

    return total_channel


@register.filter(name="new_journy")
def new_journy(user):
    last_date = datetime.date.today() - datetime.timedelta(days=1)
    new_channel = Channel.objects.filter(is_delete=False, parent_id=None, created_at__gte=last_date).count()

    return new_channel


@register.filter(name="joined_journy")
def joined_journy(user):
    new_enrollment = UserChannel.objects.filter(status="Joined").count()
    return new_enrollment


@register.filter(name="last_7_days_journy")
def last_7_days_journy(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    new_channel = Channel.objects.filter(is_delete=False, parent_id=None, created_at__gte=last_date).count()

    return new_channel


# skill

@register.filter(name="total_skill")
def total_skill(user):
    channel = Channel.objects.filter(~Q(parent_id=None), is_delete=False, is_active=True).count()
    return channel


@register.filter(name="new_skill")
def new_skill(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    channel = Channel.objects.filter(~Q(parent_id=None), is_delete=False, is_active=True,
                                     created_at__gte=last_date).count()
    return channel


@register.filter(name="last_7_days_skill")
def last_7_days_skill(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    channel = Channel.objects.filter(~Q(parent_id=None), is_delete=False, is_active=True,
                                     created_at__gte=last_date).count()
    return channel


# microskill

@register.filter(name="total_microskill")
def total_microskill(user):
    total_course = Content.objects.filter(is_delete=False).count()
    return total_course


@register.filter(name="new_microskill")
def new_microskill(user):
    last_date = datetime.date.today() - datetime.timedelta(days=1)
    total_course = Content.objects.filter(is_delete=False, created_at__gte=last_date).count()

    return total_course


@register.filter(name="pending_microskill")
def pending_microskill(user):
    total_course = Content.objects.filter(is_delete=False, status="Pending").count()

    return total_course


@register.filter(name="draft_microskill")
def draft_microskill(user):
    total_course = Content.objects.filter(is_delete=False, status="Draft").count()

    return total_course


@register.filter(name="live_microskill")
def live_microskill(user):
    total_course = Content.objects.filter(is_delete=False, status="live").count()

    return total_course


@register.filter(name="last_7_days_micro_skill")
def last_7_days_micro_skill(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    total_course = Content.objects.filter(is_delete=False, created_at__gte=last_date).count()

    return total_course


# survey


@register.filter(name="total_survey")
def total_survey(user):
    total_survey = Survey.objects.filter(is_delete=False).count()
    return total_survey


@register.filter(name="new_survey")
def new_survey(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    total_survey = Survey.objects.filter(is_delete=False, created_at__gte=last_date).count()
    return total_survey


@register.filter(name="last_7_days_survey")
def last_7_days_survey(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    total_survey = Survey.objects.filter(is_delete=False, created_at__gte=last_date).count()
    return total_survey


@register.filter(name="total_survey_attempt")
def total_survey_attempt(user):
    total_survey = SurveyAttempt.objects.all().count()
    return total_survey


@register.filter(name="new_survey_attempt")
def new_survey_attempt(user):
    last_date = datetime.date.today() - datetime.timedelta(days=1)
    total_survey = SurveyAttempt.objects.filter(created_at__gte=last_date).count()
    return total_survey


@register.filter(name="last_7_days_survey_attempt")
def last_7_days_survey_attempt(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    total_survey = SurveyAttempt.objects.filter(created_at__gte=last_date).count()
    return total_survey


# survey

@register.filter(name="total_assessment")
def total_assessment(user):
    total_survey = TestSeries.objects.all().count()
    return total_survey


@register.filter(name="new_assessment")
def new_assessment(user):
    last_date = datetime.date.today() - datetime.timedelta(days=1)
    total_survey = TestSeries.objects.filter(created_at__gte=last_date).count()
    return total_survey


@register.filter(name="last_7_days_assessment")
def last_7_days_assessment(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    total_survey = TestSeries.objects.filter(created_at__gte=last_date).count()
    return total_survey


@register.filter(name="total_assessment_attempt")
def total_assessment_attempt(user):
    total_survey = TestAttempt.objects.all().count()
    return total_survey


@register.filter(name="new_assessment_attempt")
def new_assessment_attempt(user):
    last_date = datetime.date.today() - datetime.timedelta(days=1)
    total_survey = TestAttempt.objects.filter(created_at__gte=last_date).count()
    return total_survey


@register.filter(name="last_7_days_assessment_attempt")
def last_7_days_assessment_attempt(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    total_survey = TestAttempt.objects.filter(created_at__gte=last_date).count()
    return total_survey


@register.filter(name="mentor_journeys")
def mentor_journeys(userId):
    user = User.objects.get(id=userId)
    joined_channel = []
    pool_mentor = PoolMentor.objects.filter(mentor=user)
    for pools in pool_mentor:
        channel = pools.pool.journey
        if channel.is_active == True and channel.is_delete == False:
            joined_channel.append(channel)
    return len(joined_channel)


@register.filter(name="total_mentee")
def total_mentee(userId):
    user = User.objects.get(id=userId)
    mentee = AssignMentorToUser.objects.filter(mentor=user).count()
    return mentee


@register.filter(name="today_sessions")
def today_sessions(userId):
    user = User.objects.get(id=userId)
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    print(current_date)
    mentor_session = mentorCalendar.objects.filter(mentor=user, is_cancel=False, slot_status="Booked",
                                                   start_time__date=current_date).count()
    all_mettings = Collabarate.objects.filter(speaker=user, start_time__date=current_date).count()
    total = mentor_session + all_mettings
    return total


@register.filter(name="total_sessions")
def total_sessions(userId):
    user = User.objects.get(id=userId)
    mentor_session = mentorCalendar.objects.filter(mentor=user, is_cancel=False, slot_status="Booked").count()
    all_mettings = Collabarate.objects.filter(speaker=user).count()
    total = mentor_session + all_mettings
    return total


@register.filter(name="total_assign_survey")
def total_assign_survey(userId):
    user = User.objects.get(id=userId)
    survey_id_list = []
    joined_channel = []
    pool_mentor = PoolMentor.objects.filter(mentor=user)
    for pools in pool_mentor:
        channel = pools.pool.journey
        if channel.is_active is True and channel.is_delete is False and channel not in joined_channel:
            surveys_ids = MentoringJourney.objects.filter(journey=channel, meta_key="survey", is_delete=False).values(
                "value")
            survey_id_list = [ids['value'] for ids in surveys_ids]
    return len(survey_id_list)


@register.filter(name="get_weekly_journal")
def get_weekly_journal(userId):
    user = User.objects.get(id=userId)
    users_list = []
    journey = []
    data = []
    user_list = AssignMentorToUser.objects.filter(mentor=user)
    for user_list in user_list:
        users_list.append(user_list.user.email)
        journey.append(str(user_list.journey.id))
    print(journey)
    print(user)
    data = LearningJournals.objects.filter(
        email__in=users_list, journey_id__in=journey, is_weekly_journal=True).order_by("-created_at")
    return data


@register.filter(name="get_total_points")
def get_total_points(user):
    try:
        user_points = UserEarnedPoints.objects.get(user=user)
        user_points = user_points.total_points
    except:
        user_points = 0
    return user_points
