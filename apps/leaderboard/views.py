from enum import Flag
from logging import exception
from multiprocessing import context
from unicodedata import category
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from requests import request
from apps.content.models import SkillConfig, UserCourseStart, ContentData, SkillConfig, Channel, MentoringJourney, \
    UserReadContentData, Content, TestAttempt, ChannelGroupContent, ChannelGroup, UserChannel
from apps.leaderboard.forms import BadgeCreateForm, SystemGoalCreationFrom, PointsCreateForm, StreakPointsForm, \
    GoalCreateForm
from apps.leaderboard.models import BadgeDetails, AutoApproveGoal, MentorshipGoalComment, SystemDrivenGoal, UserGoalLog, \
    PointsTable, UserDrivenGoal, UserBadgeDetails, UserEngagement, UserPoints, StreakPoints, UserStreakCount, \
    UserStreak, UserStreakHistory
from notifications.signals import notify
from apps.mentor.models import PoolMentor
from apps.push_notification.views import send_notification
from apps.users.models import Company, FirebaseDetails, UserEarnedPoints, User, UserTypes
from apps.leaderboard.goal import user_progress_chart, mentorship_goal_progress_chart, individual_goal_progress_chart, \
    user_goal_bar_chart, mentorship_goal_status_chart, user_goal_donut_chart
from ..users.utils import aware_time
from user_visit.models import UserVisit
from django.views.generic import (
    ListView,
    UpdateView,
    CreateView,
)
import math
from apps.test_series.models import TestSeries
from apps.survey_questions.models import Survey, SurveyAttempt, SurveyLabel
from apps.community.models import LearningJournals, WeeklyLearningJournals
from datetime import date, timedelta, datetime
from apps.content.utils import is_parent_channel, generate_certificate
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.contrib import messages
from ravinsight.decorators import allowed_users
from apps.content.utils import Journey, get_display_content
from django.db.models.query_utils import Q


# from apps.users.templatetags.tags import get_mentor_mentees

# Create your views here.


def send_push_notification(user, title, description, context):
    if firebase := FirebaseDetails.objects.filter(user=user):
        resgistration = [token.firebase_token for token in firebase]
        send_notification(resgistration, title, description, context)
        return True
    return False


def NotificationAndPoints(user, title):
    try:
        points = PointsTable.objects.get(label=title)

        UserPoints.objects.create(user=user, point=points.points, label=points, comment=points.comment)
        user_points = check_user_points(user)

        task_badge = BadgeDetails.objects.filter(label=points).first()
        reward_badge = False
        badge_name = ""
        if task_badge is not None:
            UserBadgeDetails.objects.create(user=user, current_badge=task_badge, points_earned=user_points.total_points,
                                            badge_acquired=True)
            reward_badge = True
            badge_name = task_badge.name

        badge = BadgeDetails.objects.filter(points_required__lte=user_points.total_points).first()
        if badge:
            max_points = badge.points_required
            current_badge = BadgeDetails.objects.get(points_required=max_points)
            if current_badge is not None:
                UserBadgeDetails.objects.create(user=user, current_badge=current_badge,
                                                points_earned=user_points.total_points,
                                                badge_acquired=True)
                reward_badge = True
                badge_name = badge.name
        else:
            max_points = user_points.total_points
        if reward_badge:
            description = f"""Hi {user.get_full_name()}!
                    Great job! You have earned {badge_name}.
                    Come check out the badge!!"""

            context = {
                "screen": "Reward"
            }
            send_push_notification(user, "Unlocked a new badge", description, context)

        description = f"""Hi {user.get_full_name()}!
                    Way to go! You earned {points.points} points from {title}.
                    Keep up the good work! Check out your progress here!"""
        context = {
            "screen": "Reward"
        }
        send_push_notification(user, f"Received {points.points} points", description, context)
        notify.send(user, recipient=user, verb=points.name, description=points.comment)

        return True
    except PointsTable.DoesNotExist:
        return False


def check_user_points(user):
    try:
        user_points = UserEarnedPoints.objects.get(user=user)
    except UserEarnedPoints.DoesNotExist:
        user_points = UserEarnedPoints.objects.create(user=user)
    return user_points


def UserSiteVisit(user):
    user_visit_count = UserVisit.objects.filter(user=user).count()
    print("uservisit", user_visit_count)
    if user_visit_count == 1:
        NotificationAndPoints(user=user, title="first login points")
        return True
    else:
        return False


def SubmitPreFinalAssessment(user, test_attempt, channel, userType=None):
    if test_attempt in ["journey_pre_assessment", "pre_assessment"]:
        NotificationAndPoints(user, test_attempt)
        return True

    elif test_attempt == "post_assessment":
        NotificationAndPoints(user, test_attempt)
        CheckEndOfJourney(user, channel, userType=userType)
        return True

    else:
        return False


def CourseCompletion(user, channel):
    # user_course = UserCourseStart.objects.filter(user=user, channel=channel, status="Complete")
    # if user_course is not None:
    # NotificationAndPoints(user, "journey completion claim")
    if UserCourseStart.objects.filter(user=user, status="Complete").count() > 3:
        NotificationAndPoints(user, "consistent course completion")
        return True


@method_decorator(login_required, name='dispatch')
class BadgeCreate(CreateView):
    form_class = BadgeCreateForm
    success_url = reverse_lazy('leaderboard:badges_list')
    template_name = "create_badge.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super().form_valid(form)


# @method_decorator(login_required, name='dispatch')
# class Goals(CreateView):
#     form_class = GoalCreateForm
#     # success_url = reverse_lazy('leaderboard:badges_list')
#     template_name = "goals.html"

#     def form_valid(self, form):
#         f = form.save(commit=False)
#         f.created_by = self.request.user
#         f.save()
#         return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class BadgeList(ListView):
    model = BadgeDetails
    context_object_name = "badges"
    template_name = "badges_list.html"

    def get_queryset(self):
        return BadgeDetails.objects.filter(is_active=True)


@method_decorator(login_required, name='dispatch')
class EditBadge(UpdateView):
    model = BadgeDetails
    form_class = BadgeCreateForm
    template_name = "create_badge.html"

    def get_success_url(self) -> str:
        if self.request.session['user_type'] == "ProgramManager":
            return reverse_lazy('program_manager:setup')
        return reverse_lazy('leaderboard:badges_list')


def DeleteBadge(request, id):
    BadgeDetails.objects.filter(id=id).update(is_active=False)
    return redirect(reverse('leaderboard:badges_list'))


@method_decorator(login_required, name='dispatch')
class CreatePoints(CreateView):
    form_class = PointsCreateForm
    success_url = reverse_lazy('leaderboard:points_list')
    template_name = "create_points.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ALLPointsList(ListView):
    model = PointsTable
    context_object_name = "all_points"
    template_name = "all_points.html"

    def get_queryset(self):
        return PointsTable.objects.filter(is_active=True)


@method_decorator(login_required, name='dispatch')
class EditPoints(UpdateView):
    model = PointsTable
    form_class = PointsCreateForm
    template_name = "create_points.html"

    def get_success_url(self) -> str:
        if self.request.session['user_type'] == "ProgramManager":
            return reverse_lazy('program_manager:setup')
        return reverse_lazy('leaderboard:points_list')


@login_required
def DeletePoints(request, pk):
    PointsTable.objects.filter(id=pk).update(is_active=False)
    return redirect(reverse('leaderboard:points_list'))


@method_decorator(login_required, name='dispatch')
class ALLStreakPointsList(ListView):
    model = StreakPoints
    context_object_name = "all_streak_points"
    template_name = "all_streak_points.html"

    def get_queryset(self):
        return StreakPoints.objects.filter(is_active=True)


@login_required
def DeleteStreakPoints(request, pk):
    StreakPoints.objects.filter(id=pk).update(is_active=False)
    return redirect(reverse('leaderboard:streak_points_list'))


@method_decorator(login_required, name='dispatch')
class CreateStreakPoints(CreateView):
    form_class = StreakPointsForm
    success_url = reverse_lazy('leaderboard:streak_points_list')
    template_name = "create_streak_points.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class EditStreakPoints(UpdateView):
    model = StreakPoints
    form_class = StreakPointsForm
    success_url = reverse_lazy('leaderboard:streak_points_list')
    template_name = "create_streak_points.html"


def UpdateUserStreakCount(user):
    yesterday = date.today() - timedelta(hours=24)
    uservisit = UserVisit.objects.filter(user=user, created_at__date=yesterday).last()
    print("uservisit", uservisit)
    if uservisit is not None:
        try:
            userStreak = UserStreakCount.objects.get(user=user)
            print("userStreak", userStreak.streak_count)
            updated_time = userStreak.updated_at.strftime('%Y-%m-%d')
            today = date.today().strftime('%Y-%m-%d')
            if (updated_time == today):
                print("updated today")
                return True
            else:
                print("updating today")
                userStreak.streak_count = userStreak.streak_count + 1
                userStreak.save()
                streak_points = StreakPoints.objects.filter(duration_in_days=userStreak.streak_count + 1).first()
                if streak_points is not None:
                    UserPoints.objects.create(user=user, point=streak_points.points,
                                              comment="Points for achieving streaks target")
                    description = f"""Hi {user.get_full_name()}!
                    Way to go! You earned {streak_points.points} points from updating streak.
                    Keep up the good work! Check out your progress here!"""
                    context = {
                        "screen": "Reward"
                    }
                    send_push_notification(user, "Points Earned", description, context)

        except:
            print("except")
            userStreak = UserStreakCount(user=user, streak_count=1, streak_count_start_date=datetime.now())
            userStreak.save()
        return True
    else:
        print("user streak is none")
        lastuservisit = UserVisit.objects.filter(user=user).last()
        try:
            userStreak = UserStreakCount.objects.get(user=user)
            print("else user streak", userStreak)
            UserStreakHistory.objects.create(user=user, streak=userStreak.streak_count,
                                             start_date=userStreak.streak_count_start_date,
                                             end_date=lastuservisit.created_at)
            userStreak.streak_count = 1
            user.streak_count_start_date = datetime.now()
            userStreak.save()
        except:
            userStreak = UserStreakCount(user=user, streak_count=1, streak_count_start_date=datetime.now())
            userStreak.save()
        return True


def AddUserStreak(user):
    try:
        UserStreak.objects.get(user=user, created_at__date=date.today())
        return True
    except:
        userStreak = UserStreak(user=user, is_streak_done=True)
        userStreak.save()
        return True


def CheckEndOfJourney(user, channel, send_notification=True, userType=None):
    journey = EndOfJourney(user, channel)
    if journey['status'] == "Journey Not Found":
        return False
    print("joewfwef", journey)
    
    if journey['content_complete_count'] == journey['content_count'] and send_notification==False:
        print("IN THE NEW CONDITION")
        parent_check = is_parent_channel(channel)
        file_url = generate_certificate(user.id, user.get_full_name(), parent_check['channel_id'], userType)
        return file_url
    
    if send_notification:
        print("IN THE OLD CONDITION")
        NotificationAndPoints(user, "journey completion claim")
        parent_check = is_parent_channel(channel)
        user_channel = UserChannel.objects.get(user=user, Channel_id=parent_check['channel_id'])
        user_channel.is_completed = True
        user_channel.save()
        description = f"""Hi {user.first_name} {user.last_name}!
        Great job! You have earned Journey Completion Certificate!"""
        context = {
            "screen": "Journey",
        }
        send_push_notification(user, 'Journey Completion Certificate', description, context)
        file_url = generate_certificate(user.id, user.get_full_name(), parent_check['channel_id'], userType)
        return file_url
    return None


def EndOfJourney(user, channel):

    channel = Channel.objects.filter(pk=channel, is_delete=False, is_active=True)

    channel = channel.first()
    if channel:
        parent_check = is_parent_channel(channel.pk)
        data = []
        read_status = ""
        channel_group = ChannelGroup.objects.filter(channel=channel, is_delete=False)
        if parent_check['channel'].channel_type == "onlyCommunity":

            channel_content = ChannelGroupContent.objects.filter(channel_group__in=channel_group, status="Live",
                                                                 is_delete=False)

            for channel_content in channel_content:
                read_content = channel_content.content
                try:
                    user_read_status = UserCourseStart.objects.get(
                        user=user, content=read_content, channel_group=channel_content.channel_group,
                        channel=channel.pk)
                    read_status = user_read_status.status
                except UserCourseStart.DoesNotExist:
                    read_status = ""

                data.append({
                    "read_status": read_status
                })

        elif parent_check['channel'].channel_type == "SkillDevelopment":
            skill_config = SkillConfig.objects.filter(channel=parent_check['channel'])
            print("skill_config", skill_config.values())
            for channel_group in channel_group:
                channel_group_content = ChannelGroupContent.objects.filter(
                    channel_group=channel_group, is_delete=False)
                for channel_group_content in channel_group_content:
                    course_start = UserCourseStart.objects.filter(
                        user=user, content=channel_group_content.content, channel_group=channel_group,
                        channel=channel).first()
                    quest = channel_group_content.content.pk
                    if course_start:
                        data.append({
                            "read_status": "Complete"
                        })

                    if channel_group_content.channel_group.post_assessment:
                        assessment = channel_group_content.channel_group.post_assessment.id
                        test_attempt = TestAttempt.objects.filter(
                            test_id=assessment, user=user, channel=channel.parent_id, type="post_assessment",
                            skill_id=channel.id, quest_id=quest)
                        if test_attempt.count() > 0:
                            data.append({
                                "read_status": "Complete"
                            })

            for skill_config in skill_config:
                if skill_config.journey_pre_assessment_id:
                    assessment = TestSeries.objects.get(id=skill_config.journey_pre_assessment_id)
                    test_attempt = TestAttempt.objects.filter(
                        test=assessment, user=user, channel=channel.parent_id, type="journey_pre_assessment")
                    if test_attempt.count() > 0:
                        data.append({
                            "read_status": "Complete"
                        })

                if skill_config.pre_assessment_id:
                    assessment = TestSeries.objects.get(id=skill_config.pre_assessment_id)
                    test_attempt = TestAttempt.objects.filter(skill_id=channel.id, user=user,
                                                              channel=channel.parent_id, test=channel.test_series)
                    if test_attempt.count() > 0:
                        data.append({
                            "read_status": "Complete"
                        })

        elif parent_check['channel'].channel_type == "MentoringJourney":
            mentoring_journey = MentoringJourney.objects.filter(
                journey=parent_check['channel'], is_delete=False).order_by('display_order')
            for mentoring_journey in mentoring_journey:
                type = mentoring_journey.meta_key
                # print("type",type)
                read_status = ""
                if type == "quest":
                    content = Content.objects.get(pk=mentoring_journey.value)
                    # print(content)
                    try:
                        user_read_status = UserCourseStart.objects.get(
                            user=user, content=content, channel_group=mentoring_journey.journey_group,
                            channel=channel.pk)
                        # print(user_read_status)
                        read_status = user_read_status.status
                    except UserCourseStart.DoesNotExist:
                        read_status = ""
                elif type == "assessment":
                    test_series = TestSeries.objects.get(pk=mentoring_journey.value)
                    test_attempt = TestAttempt.objects.filter(
                        test=test_series, user=user, channel=mentoring_journey.journey)
                    if test_attempt.count() > 0:
                        read_status = "Complete"
                elif type == "survey":
                    survey = Survey.objects.get(pk=mentoring_journey.value)
                    survey_attempt = SurveyAttempt.objects.filter(
                        survey=survey, user=user)
                    if survey_attempt.count() > 0:
                        read_status = "Complete"

                elif type == "journals":
                    weekely_journals = WeeklyLearningJournals.objects.get(
                        pk=mentoring_journey.value, journey_id=channel.pk)
                    learning_journals = LearningJournals.objects.filter(
                        weekely_journal_id=weekely_journals.pk, journey_id=channel.pk, email=user.email)
                    if learning_journals.count() > 0:
                        if learning_journals.first().is_draft:
                            read_status = "InProgress"
                        else:
                            read_status = "Complete"

                data.append({
                    "read_status": read_status
                })
        else:
            data.append({
                "read_status": read_status
            })
        # print("data",data)
        count = 0
        data_count = len(data)
        for data in data:
            # print("read_status",data['read_status'])
            if data['read_status'] == 'Complete':
                count = count + 1
        # print("count", count, data_count)
        return {
            "status": "completed" if count == data_count else "inprogress",
            "content_complete_count": count,
            "content_count": data_count
        }
        # return data

        # else:
        #     data = {
        #         "status": "inprogress",
        #         "content_complete_count": count,
        #         "content_count": data_count
        #     }
        #     return data

    # else:
    data = {
        "status": "Journey Not Found"
    }
    return data


def UserBestStreak(user):
    bestStreakObj = UserStreakHistory.objects.filter(user=user).order_by('-streak').first()

    currentStreakCount = UserStreakCount.objects.filter(user=user).first()
    # print("currentStreak", currentStreakCount.streak_count)
    if bestStreakObj:
        # print("beststreak", bestStreakObj.streak)
        if (bestStreakObj.streak < currentStreakCount.streak_count):
            return currentStreakCount.streak_count
        return bestStreakObj.streak
    return currentStreakCount.streak_count


def UserNextGoal(user, type, journey_from="user_channel"):
    # print(journey_from, "441", journey_from == "pool_Mentor", "demo")
    context = []
    is_grayedout = False
    if journey_from == "pool_mentor":
        # print("tesign")
        journeys = PoolMentor.objects.filter(
            mentor=user, pool__journey__is_active=True, pool__journey__is_delete=False, pool__journey__closure_date__gt=datetime.now())
        journey_list = list(set([journey.pool.journey for journey in journeys]))
        for journey in journey_list:
            channell = journey
            parent_check = is_parent_channel(channell.pk)
            channel_group = ChannelGroup.objects.filter(channel=channell, is_delete=False)
            if channel_group:
                group_id = channel_group[0].id
            else:
                group_id = ""

            mentoring_journey = MentoringJourney.objects.filter(
                journey=parent_check['channel'], is_delete=False).order_by('display_order')
            for mentoring_journey in mentoring_journey:
                type = mentoring_journey.meta_key
                read_status = ""
                is_grayedout = mentoring_journey.is_checked 
                if type == "quest":
                    content = Content.objects.get(pk=mentoring_journey.value)
                    try:
                        user_read_status = UserCourseStart.objects.get(
                            user=user, content=content, channel_group=mentoring_journey.journey_group,
                            channel=channell.pk)
                        read_status = user_read_status.status
                    except UserCourseStart.DoesNotExist:
                        read_status = ""
                elif type == "assessment":
                    test_series = TestSeries.objects.get(pk=mentoring_journey.value)
                    test_attempt = TestAttempt.objects.filter(
                        test=test_series, user=user, channel=mentoring_journey.journey)
                    if test_attempt.count() > 0:
                        read_status = "Complete"
                elif type == "survey":
                    survey = Survey.objects.get(pk=mentoring_journey.value)
                    survey_attempt = SurveyAttempt.objects.filter(
                        survey=survey, user=user)
                    if survey_attempt.count() > 0:
                        read_status = "Complete"

                elif type == "journals":
                    weekely_journals = WeeklyLearningJournals.objects.get(
                        pk=mentoring_journey.value, journey_id=channell.pk)
                    learning_journals = LearningJournals.objects.filter(
                        weekely_journal_id=weekely_journals.pk, journey_id=channell.pk, email=user.email)
                    if learning_journals.count() > 0:
                        if learning_journals.first().is_draft:
                            read_status = "InProgress"
                        else:
                            read_status = "Complete"

                if read_status != "Complete":

                    try:
                        content_data = ContentData.objects.filter(
                            content=mentoring_journey.value).order_by("display_order")
                        total_content = content_data.count()
                        complete = 0
                        progress = 0
                        for content_data in content_data:
                            try:
                                read_content = UserReadContentData.objects.get(user=user, content_data=content_data)
                                status = read_content.status
                            except:
                                status = "Start"
                            if status == "Complete":
                                complete = complete + 1

                            try:
                                progress = math.ceil((complete / total_content) * 100)

                            except:
                                progress = 0
                        if progress != 100:
                            context.append({
                                "type": type,
                                "id": mentoring_journey.value,
                                "type": type,
                                "channel_group": group_id,
                                "title": mentoring_journey.name,
                                "journey_id": mentoring_journey.journey.pk,
                                "progress": progress,
                                "is_grayedout": is_grayedout
                            })
                        # print("contentt type", type)
                    except:
                        pass
    else:
        user_channel = UserChannel.objects.filter(
            Channel__closure_date__gt=datetime.now(), user=user, status='Joined', is_completed=False)
        is_grayedout = False
        # print("user_channel", user_channel)
        # display_content = []
        for channel in user_channel:
            parent_check = is_parent_channel(channel.Channel.pk)
            # print("channel_type", parent_check['channel'].channel_type, channel.Channel.title)
            channel_group = ChannelGroup.objects.filter(channel=channel.Channel, is_delete=False)
            if channel_group:
                # print("channel_group", channel_group, channel_group[0].id)
                group_id = channel_group[0].id
            else:
                group_id = ""
            if (parent_check['channel'].channel_type == "MentoringJourney"):
                mentoring_journey = MentoringJourney.objects.filter(
                    journey=parent_check['channel'], is_delete=False).order_by('display_order')
                # print("mentoring_journey", mentoring_journey)
                for mentoring_journey in mentoring_journey:
                    # print("570", mentoring_journey.name)
                    type = mentoring_journey.meta_key
                    read_status = ""
                    is_grayedout = mentoring_journey.is_checked
                    if type == "quest":
                        content = Content.objects.get(pk=mentoring_journey.value)
                        try:
                            user_read_status = UserCourseStart.objects.get(
                                user=user, content=content, channel_group=mentoring_journey.journey_group,
                                channel=channel.Channel.pk)
                            read_status = user_read_status.status
                        except UserCourseStart.DoesNotExist:
                            read_status = ""
                    elif type == "assessment":
                        test_series = TestSeries.objects.get(pk=mentoring_journey.value)
                        test_attempt = TestAttempt.objects.filter(
                            test=test_series, user=user, channel=mentoring_journey.journey)
                        if test_attempt.count() > 0:
                            read_status = "Complete"
                    elif type == "survey":
                        survey = Survey.objects.get(pk=mentoring_journey.value)
                        survey_attempt = SurveyAttempt.objects.filter(
                            survey=survey, user=user)
                        if survey_attempt.count() > 0:
                            read_status = "Complete"

                    elif type == "journals":
                        weekely_journals = WeeklyLearningJournals.objects.get(
                            pk=mentoring_journey.value, journey_id=channel.Channel.pk)
                        learning_journals = LearningJournals.objects.filter(
                            weekely_journal_id=weekely_journals.pk, journey_id=channel.Channel.pk, email=user.email)
                        if learning_journals.count() > 0:
                            if learning_journals.first().is_draft:
                                read_status = "InProgress"
                            else:
                                read_status = "Complete"
                    else:
                        pass

                    if read_status != "Complete":

                        try:
                            content_data = ContentData.objects.filter(
                                content=mentoring_journey.value).order_by("display_order")
                            total_content = content_data.count()
                            complete = 0
                            progress = 0
                            for content_data in content_data:
                                try:
                                    read_content = UserReadContentData.objects.get(
                                        user=user, content_data=content_data)
                                    status = read_content.status
                                except:
                                    status = "Start"
                                if status == "Complete":
                                    complete = complete + 1

                                try:
                                    progress = math.ceil((complete / total_content) * 100)

                                except:
                                    progress = 0
                            if progress != 100:
                                context.append({
                                    "type": type,
                                    "id": mentoring_journey.value,
                                    "type": type,
                                    "journey_id": mentoring_journey.journey.pk,
                                    "channel_group": group_id,
                                    "title": mentoring_journey.name,
                                    "journey_id": mentoring_journey.journey.pk,
                                    "progress": progress,
                                    "is_grayedout": is_grayedout
                                })
                                # print("content type 636", type, mentoring_journey.name)
                            # print("context", context)
                        except:
                            pass

            elif (parent_check['channel'].channel_type == "onlyCommunity"):
                is_grayedout = False
                channel_content = ChannelGroupContent.objects.filter(channel_group__in=channel_group, status="Live",
                                                                     is_delete=False)
                # print("channel_content",channel_content)
                for channel_content in channel_content:

                    read_content = channel_content.content
                    # print("read_contnet", read_content.pk)
                    try:
                        user_read_status = UserCourseStart.objects.get(
                            user=user, content=read_content, channel_group=channel_content.channel_group,
                            channel=channel.Channel.pk)
                        read_status = user_read_status.status
                    except UserCourseStart.DoesNotExist:
                        read_status = ""
                    # print("read_status", read_status)

                    if read_status != "Complete":

                        try:
                            content_data = ContentData.objects.filter(
                                content=read_content.pk).order_by("display_order")
                            total_content = content_data.count()
                            complete = 0
                            progress = 0
                            for content_data in content_data:
                                # print("content_data", content_data)
                                try:
                                    read_contents = UserReadContentData.objects.get(
                                        user=user, content_data=content_data)
                                    status = read_contents.status
                                except:
                                    status = "Start"
                                if status == "Complete":
                                    complete = complete + 1

                                try:
                                    progress = math.ceil((complete / total_content) * 100)

                                except:
                                    progress = 0
                            if progress != 100:
                                # print("progress", progress, read_content.title)

                                context.append({
                                    "type": "quest",
                                    "id": read_content.pk,
                                    "type": "quest",
                                    "channel_group": group_id,
                                    "journey_id": channel.pk,
                                    "title": read_content.title,
                                    "journey_id": channel.pk,
                                    "progress": progress,
                                    "is_grayedout": is_grayedout
                                })
                            # print("context", context)
                        except:
                            pass

            elif (parent_check['channel'].channel_type == "SkillDevelopment"):
                is_grayedout = False
                skills = SkillConfig.objects.filter(channel=channel.Channel)
                # print("skill", skills)
                for skill in skills:
                    channel = Channel.objects.get(pk=skill.sub_channel.pk)
                    channel_group = ChannelGroup.objects.filter(channel=channel, is_delete=False)

                    # print("channelvb", channel)
                    if channel.is_test_required:
                        # print(channel.test_series)
                        assessment_attempt = TestAttempt.objects.filter(
                            user=user, channel=channel, test=channel.test_series)
                        # print("assessmentsa", assessment_attempt)
                        if len(assessment_attempt) > 0:
                            assessment_attempt = assessment_attempt.first()

                            try:
                                assessment_attempt_marks = math.ceil(
                                    (assessment_attempt.total_marks / assessment_attempt.test_marks) * 100)

                            except:
                                assessment_attempt_marks = assessment_attempt.total_marks

                            channel_group = channel_group.filter(
                                start_mark__lte=assessment_attempt_marks, end_marks__gte=assessment_attempt_marks)
                            if channel.parent_id is not None:
                                channel = []
                        else:
                            channel_group = []
                    else:
                        assessment_attempt = TestAttempt.objects.filter(
                            user=user, channel=channel, test=channel.test_series)
                        # print("assessmentggjhj", assessment_attempt)
                        level = "Level 1"
                        if len(assessment_attempt) > 0:
                            assessment_attempt = assessment_attempt.first()
                            level = assessment_attempt.user_skill

                        level = SurveyLabel.objects.get(label=level)
                        # print("level", level)

                        channel_group = channel_group.filter(channel_for=level)
                    # print("channel", channel_group)
                    for group in channel_group:
                        tes = ChannelGroupContent.objects.filter(channel_group=group, is_delete=False).first()
                        # print("eferf", tes.content.title)

                        try:
                            content_data = ContentData.objects.filter(
                                content=tes.content.pk).order_by("display_order")
                            total_content = content_data.count()
                            complete = 0
                            progress = 0
                            for content_data in content_data:
                                try:
                                    read_content = UserReadContentData.objects.get(
                                        user=user, content_data=content_data)
                                    status = read_content.status
                                except:
                                    status = "Start"
                                if status == "Complete":
                                    complete = complete + 1

                                try:
                                    progress = math.ceil((complete / total_content) * 100)

                                except:
                                    progress = 0
                            if progress != 100:
                                context.append({
                                    "type": "quest",
                                    "id": tes.content.pk,
                                    "type": "quest",
                                    "journey_id": channel.pk,
                                    "channel_group": group_id,
                                    "title": tes.content.title,
                                    "journey_id": channel.pk,
                                    "progress": progress,
                                    "is_grayedout": is_grayedout
                                })
                            # print("context", context)
                        except:
                            pass

            # print("display_content", context)

    return context


@login_required
def start_engagement(request):
    if request.method == "POST":
        UserEngagement.objects.create(user=request.user, login_time=datetime.now())
        return JsonResponse({"Success": True})


@login_required
def end_engagement(request):
    if request.method == "POST":
        user_engagement = UserEngagement.objects.filter(user=request.user).first()
        if user_engagement:
            user_engagement.logout_time = datetime.now()
            user_engagement.save()
            return JsonResponse({"Success": True})
        return JsonResponse({"Success": False})


@method_decorator(login_required, name='dispatch')
class Goals(View):
    def get(self, request, pk=None):
        print(pk, "pk is")
        try:
            UserTypes.objects.get(type=request.session['user_type'])
        except Exception:
            return redirect(reverse('user:logout'))
        if request.session['user_type'] == "Learner" or request.session.get('UserDashboardView') == True:
            goal_list = []
            if pk is None:
                userId = request.user.id
                goals = UserDrivenGoal.objects.filter(created_by=request.user, is_deleted=False,
                                                      goal_type="User Driven")
                for goal in goals:
                    try:
                        goal_log = UserGoalLog.objects.get(user=request.user, goal=goal, created_at__date=date.today())
                        goal_list.append({
                            "goal": goal,
                            "status": goal_log.status,
                        })
                    except UserGoalLog.DoesNotExist:
                        goal_list.append({
                            "goal": goal,
                            "status": '',
                            "userId": userId,
                        })
                        # Mentorship Goals
                mentorship_goals = mentorshipGoal(request.user)
                goal_log_list = user_goal_bar_chart(request.user, goals)
            else:
                userId = pk
                user = User.objects.get(id=pk)
                goals = UserDrivenGoal.objects.filter(created_by=user, is_deleted=False, goal_type="User Driven")
                for goal in goals:
                    try:
                        goal_log = UserGoalLog.objects.get(user=user, goal=goal, created_at__date=date.today())
                        goal_list.append({
                            "goal": goal,
                            "status": goal_log.status,
                            "userId": userId,
                        })
                    except UserGoalLog.DoesNotExist:
                        goal_list.append({
                            "goal": goal,
                            "status": ''
                        })
                mentorship_goals = mentorshipGoal(user)
                goal_log_list = user_goal_bar_chart(user, goals)

            user_goal_category_list = user_goal_donut_chart(goals)
            print(goal_list)
            context = {
                "data": goal_list,
                "mentorship_goals": mentorship_goals['mentorship_goal_list'],
                "goal_log": goal_log_list,
                "category_list": user_goal_category_list,
                "mentorship_goal_category_chart": mentorship_goals['mentorship_goal_category_chart'],
                "mentorship_goal_status_chart": mentorship_goals['mentorship_goal_status_chart'],
                "mentorship_goal_progress_chart": mentorship_goals['mentorship_goal_progress_chart']
            }

            # print("goal_list", context)

            return render(request, "goals.html", context)

        else:
            goals = UserDrivenGoal.objects.filter(created_by=request.user, is_deleted=False, goal_type="Mentorship")
            goal_log_list = []
            goal_list = []
            # mentees = get_mentor_mentees(request.user)
            # for mentee in mentees:
            #     print("meentee", mentee.user.first_name)
            for goal in goals:
                # print("goal line 930", goal.learners)
                if (goal.complete_till > aware_time(datetime.now())):
                    expired = "No"
                else:
                    expired = "Yes"

                requested = UserGoalLog.objects.filter(goal=goal, status='RequestForApprove').count()
                rejected = UserGoalLog.objects.filter(goal=goal, status='RejectedByMentor').count()
                approved = UserGoalLog.objects.filter(goal=goal, status='ApprovedByMentor').count()

                goal_log_list.append({
                    "name": goal.heading,
                    "requested": requested,
                    "rejected": rejected,
                    "approved": approved
                })
                goal_list.append({
                    "goal": goal,
                    "is_expired": expired
                })

            # print("goal log list", goal_log_list)

            context = {
                "date": datetime.now(),
                "data": goal_list,
                "goal_log": goal_log_list
            }

            # print("goal_list", context)

            return render(request, "mentor_goal.html", context)

    def post(self, request):
        if request.method == "POST":
            heading = request.POST['heading']
            # print("heading", heading)
            description = request.POST['description']
            category = request.POST['category']
            priority = request.POST['priority']
            duration_number = request.POST['duration_number']
            duration_time = request.POST['duration_time']
            goal_type = request.POST['goal_type']
            # print("complete_by", complete_by)
            if (goal_type == 'Mentorship'):
                learners = request.POST.getlist('learners[]')
                for learner in learners:
                    try:
                        user = User.objects.get(pk=learner, userType__type='Learner')
                        notify.send(user, recipient=user, verb=heading,
                                    description='A new mentorship goal ' + heading + ' has been assigned to you!')
                    except User.DoesNotExist:
                        pass
                complete_by = request.POST['complete_by']

                complete_by = complete_by.split("-")
                # print("complete_by", complete_by)

                complete_till = date(int(complete_by[0]), int(complete_by[1]), int(complete_by[2]))
                # print("complete_TILL", complete_till)

                goal = UserDrivenGoal.objects.create(created_by=request.user, heading=heading,
                                                     complete_till=complete_till,
                                                     description=description, goal_type=goal_type,
                                                     duration_number=duration_number, duration_time=duration_time,
                                                     category=category, priority_level=priority)
                for learner in learners:
                    goal.learners.add(learner)
                goal.save()

            else:
                frequency = request.POST['frequency']

                goal = UserDrivenGoal.objects.create(created_by=request.user, heading=heading,
                                                     description=description, goal_type=goal_type,
                                                     duration_number=duration_number, duration_time=duration_time,
                                                     category=category, priority_level=priority, frequency=frequency)

            return redirect("/leaderboard/goal")
        else:
            return render(request, "goals.html")


@login_required
def view_goal(request):
    if request.method == "GET":
        # print('request', request.GET['id'])
        id = request.GET['id']
        try:
            goal = UserDrivenGoal.objects.get(id=id)
        except UserDrivenGoal.DoesNotExist:
            goal = ""

        print("line 9999", goal.learners.all())
        learners = []
        for learner in goal.learners.all():
            learners.append(learner.pk)

        context = {
            "id": goal.id,
            "heading": goal.heading,
            "description": goal.description,
            "category": goal.category,
            "type": goal.goal_type,
            "learners": learners,
            "duration_number": goal.duration_number,
            "duration_time": goal.duration_time,
            "priority": goal.priority_level,
            "frequency": goal.frequency,
            "complete_by": goal.complete_till
        }
        # print("context", context)
        return JsonResponse(context)

    if request.method == "POST":
        try:
            id = request.POST['id']
            heading = request.POST['heading']
            # if(heading == ""):
            # messages.error(request, 'Please enter goal heading')
            # return redirect(reverse('leaderboard:goal'))
            print("heading", heading)
            description = request.POST['description']
            priority = request.POST['priority']
            category = request.POST['category']
            duration_number = request.POST['duration_number']
            duration_time = request.POST['duration_time']
            goal_type = request.POST['goal_type']
            goal = UserDrivenGoal.objects.get(id=id)

            if (goal_type == 'Mentorship'):
                learners = request.POST.getlist('learners[]')
                for learner in learners:
                    try:
                        user = User.objects.get(pk=learner, userType__type='Learner')
                        notify.send(user, recipient=user, verb=heading,
                                    description='Mentorship Goal ' + heading + ' has been edited!')
                    except User.DoesNotExist:
                        pass

                complete_by = request.POST['complete_by']

                complete_by = complete_by.split("-")
                print("complete_by", complete_by)

                complete_till = date(int(complete_by[0]), int(complete_by[1]), int(complete_by[2]))
                # print("complete_TILL", complete_till)

                goal.complete_till = complete_till
                for learne in goal.learners.all():
                    print("1020", learner)
                    goal.learners.remove(learne)
                for learn in learners:
                    goal.learners.add(learn)

            else:
                frequency = request.POST['frequency']
                goal.frequency = frequency
            if heading != "":
                goal.heading = heading
            if description != "":
                goal.description = description
            goal.priority_level = priority
            goal.category = category
            if duration_number != "":
                goal.duration_number = duration_number
            goal.duration_time = duration_time
            goal.save()
            print("line 960")
            return redirect(reverse('leaderboard:goal'))
        except Exception as e:
            print("Exception edit goal", e)
            return HttpResponse('Failed')


@login_required
def delete_goal(request):
    if request.method == "POST":
        try:
            id = request.POST['id']
            goal = UserDrivenGoal.objects.get(id=id)
            goal.is_active = False
            goal.is_deleted = True
            goal.save()
            return HttpResponse('Success')
        except:
            return HttpResponse('Failed')


@method_decorator(login_required, name='dispatch')
class Leaderboard(View):
    def get(self, request):
        points = UserEarnedPoints.objects.filter().order_by('-total_points')[:10]
        context = {
            "points": points
        }

        return render(request, "leaderboard.html", context)


@method_decorator(login_required, name='dispatch')
class UserGoalProgress(View):
    def get(self, request, pk):
        # print(pk)
        try:
            user_goal = UserDrivenGoal.objects.get(id=pk)
        except UserDrivenGoal.DoesNotExist:
            context = {
                "msg": "no data"
            }
            return render(request, "goal_progress.html", context)
        goalLog = UserGoalLog.objects.filter(user=request.user, goal=user_goal).order_by('created_at')
        complete = 0
        failed = 0
        skipped = 0
        for goal in goalLog:
            if (goal.status == 'Completed'):
                complete = complete + 1

            elif (goal.status == 'Failed'):
                failed = failed + 1

            elif (goal.status == 'Skipped'):
                skipped = skipped + 1

        data = individual_goal_progress_chart(goalLog)
        try:
            goal_log = UserGoalLog.objects.filter(user=request.user, goal=user_goal,
                                                  created_at__date=date.today()).first()

            status = goal_log.status if goal_log else ""
            progress_percentage = goal_log.progress_percentage if goal_log else 0

        except UserGoalLog.DoesNotExist:
            status = ''
            progress_percentage = 0
        # print("data", data)
        context = {
            "goal": user_goal,
            "progress_percentage": progress_percentage,
            "status": status,
            "name": user_goal.heading,
            "complete": complete,
            "skipped": skipped,
            "failed": failed,
            "data": data,
        }
        # print("context", context)
        return render(request, "goal_progress.html", context)


@method_decorator(login_required, name='dispatch')
@method_decorator(allowed_users(allowed_roles=["Admin", "ProgramManager"]), name="dispatch")
class SystemGoals(View):
    template_name = "system_goals.html"

    def get(self, request, **kwargs):
        channel = Channel.objects.filter(parent_id=None, is_delete=False, is_active=True)
        goals = SystemDrivenGoal.objects.filter(is_deleted=False)
        return render(request, self.template_name, {"channel": channel, "goals": goals})


@method_decorator(login_required, name='dispatch')
class DeleteSystemGoal(View):
    def post(self, request, **kwargs):
        goal_id = self.request.POST['pk']

        SystemDrivenGoal.objects.filter(pk=goal_id).update(is_deleted=True)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class CreateSystemGoal(CreateView):
    model = SystemDrivenGoal
    form_class = SystemGoalCreationFrom
    template_name = "create_system_goal.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('leaderboard:system_goals')


@method_decorator(login_required, name='dispatch')
class JourneyContent(View):
    def post(self, request):
        id = request.POST['channel']
        channel = Channel.objects.filter(pk=id)
        # print("channel",channel)
        channel = channel.first()
        # print("channel", channel)
        parent_check = is_parent_channel(channel.pk)
        # print("channel.channel_type", channel.channel_type)

        display_content = []

        # channel = parent_check['channel']
        channel_group = ChannelGroup.objects.filter(channel=channel, is_delete=False)

        if channel.channel_type == "SkillDevelopment":
            channel = Channel.objects.get(pk=id)

        if parent_check['channel'].channel_type == "onlyCommunity":

            display_content = get_display_content(channel, channel_group, request.user)
            # print(display_content)
        elif parent_check['channel'].channel_type == "MentoringJourney":

            mentoring_journey = MentoringJourney.objects.filter(
                journey=parent_check['channel'], is_delete=False).order_by('display_order')
            for mentoring_journey in mentoring_journey:

                type = mentoring_journey.meta_key
                # print("type",type)
                read_status = ""
                content_image = ""
                output_key = ""
                if type == "quest":
                    content = Content.objects.get(pk=mentoring_journey.value)
                    try:
                        user_read_status = UserCourseStart.objects.get(
                            user=request.user, content=content, channel_group=mentoring_journey.journey_group,
                            channel=channel.pk)
                        # print(user_read_status)
                        read_status = user_read_status.status
                    except UserCourseStart.DoesNotExist:
                        read_status = ""
                elif type == "assessment":
                    test_series = TestSeries.objects.get(pk=mentoring_journey.value)
                    test_attempt = TestAttempt.objects.filter(
                        test=test_series, user=request.user, channel=mentoring_journey.journey)
                    if test_attempt.count() > 0:
                        read_status = "Complete"
                elif type == "survey":
                    survey = Survey.objects.get(pk=mentoring_journey.value)
                    survey_attempt = SurveyAttempt.objects.filter(
                        survey=survey, user=request.user)
                    if survey_attempt.count() > 0:
                        read_status = "Complete"

                elif type == "journals":
                    weekely_journals = WeeklyLearningJournals.objects.get(
                        pk=mentoring_journey.value, journey_id=channel.pk)
                    learning_journals = LearningJournals.objects.filter(
                        weekely_journal_id=weekely_journals.pk, journey_id=channel.pk, email=self.request.user.email)
                    if learning_journals.count() > 0:
                        if learning_journals.first().is_draft:
                            read_status = "InProgress"
                        else:
                            read_status = "Complete"
                    data = weekely_journals
                    output_key = learning_journals.first()
                else:
                    content_image = ""

                # print("read_status", read_status)

                display_content.append({
                    "type": type,
                    "title": mentoring_journey.name,
                    "id": mentoring_journey.value,
                    "channel_group": mentoring_journey.journey_group.pk,
                    "journey_id": mentoring_journey.journey.pk,
                    "read_status": read_status,
                    "read_data": output_key
                })
            # print("display_content", display_content)

        elif parent_check['channel'].channel_type == "SkillDevelopment":

            if channel.parent_id is None:
                skill = Channel.objects.filter(parent_id=channel)
                for skill in skill:
                    display_content.append({
                        "type": "skills",
                        "title": skill.title,
                        "id": "",
                        "channel_group": "",
                        "journey_id": skill.id,
                        "read_status": ""
                    })

            else:
                if parent_check['channel'].is_test_required:
                    test_series = TestSeries.objects.filter(pk=channel.test_series.pk)
                    for test_series in test_series:
                        display_content.append({
                            "type": "assessment",
                            "title": test_series.name,
                            "id": test_series.pk,
                            "channel_group": "",
                            "journey_id": parent_check['channel'].pk,
                            "read_status": ""
                        })

                    assessment_attempt = TestAttempt.objects.filter(
                        user=request.user, channel=channel, test=channel.test_series)
                    if len(assessment_attempt) > 0:
                        # print(assessment_attempt)
                        assessment_attempt = assessment_attempt.first()

                        try:
                            assessment_attempt_marks = math.ceil(
                                (assessment_attempt.total_marks / assessment_attempt.test_marks) * 100)

                        except:
                            assessment_attempt_marks = assessment_attempt.total_marks

                        channel_group = channel_group.filter(
                            start_mark__lte=assessment_attempt_marks, end_marks__gte=assessment_attempt_marks)
                        marks = assessment_attempt.total_marks
                        display_content = get_display_content(channel, channel_group, request.user)
                        if channel.parent_id is not None:
                            channel = []
                    else:

                        channel_group = []

                    # print("display_content", display_content)

                else:
                    assessment_attempt = TestAttempt.objects.filter(
                        user=request.user, channel=channel, test=channel.test_series)

                    level = "Level 1"
                    if len(assessment_attempt) > 0:
                        assessment_attempt = assessment_attempt.first()
                        level = assessment_attempt.user_skill

                    level = SurveyLabel.objects.get(label=level)

                    channel_group = channel_group.filter(channel_for=level)
                    # print(channel_group)
                    display_content = get_display_content(channel, channel_group, request.user)
                    # print("display_content", display_content)

        return JsonResponse(display_content, safe=False)


# @method_decorator(login_required, name='dispatch')
# class ViewSystemGoal(View):
#     def get(self, request, **kwargs):
#         goal = SystemDrivenGoal.objects.get(pk=self.kwargs['pk'])
#         context = {
#             "goal":goal
#         }

#         return render(request, 'view_system_goal.html', context)


# @login_required
def mentorshipGoal(user):
    mentorship_goal_list = []
    mentorship_goals = UserDrivenGoal.objects.filter(
        learners__in=[user], is_deleted=False, goal_type="Mentorship")
    for goal in mentorship_goals:
        if (goal.complete_till > aware_time(datetime.now())):
            expired = "No"
        else:
            expired = "Yes"
        try:
            goal_log = UserGoalLog.objects.filter(user=user, goal=goal).first()
            mentorship_goal_list.append({
                "goal": goal,
                "status": goal_log.status if goal_log else "",
                "is_expired": expired,
                "progress_percentage": goal_log.progress_percentage if goal_log else 0
            })
        except UserGoalLog.DoesNotExist:
            mentorship_goal_list.append({
                "goal": goal,
                "status": '',
                "is_expired": expired,
                "progress_percentage": 0
            })

    data = {
        "mentorship_goal_list": mentorship_goal_list,
        "mentorship_goal_category_chart": user_goal_donut_chart(mentorship_goals),
        "mentorship_goal_status_chart": mentorship_goal_status_chart(user, mentorship_goals),
        "mentorship_goal_progress_chart": mentorship_goal_progress_chart(user, mentorship_goals)
    }
    # print(data)

    return data


def dashboardMentorshipGoal(user, type):
    mentorship_goal_list = []
    category_list = []

    if type == 'Mentor':
        mentorship_goals = UserDrivenGoal.objects.filter(
            created_by=user, is_deleted=False, goal_type="Mentorship", complete_till__gte=datetime.now())
    else:
        mentorship_goals = UserDrivenGoal.objects.filter(
            learners__in=[user], is_deleted=False, goal_type="Mentorship", complete_till__gte=datetime.now())
    for goal in mentorship_goals:
        try:
            goal_log = UserGoalLog.objects.filter(user=user, goal=goal).first()
            mentorship_goal_list.append({
                "goal": goal,
                "status": goal_log.status if goal_log else ""
            })
        except UserGoalLog.DoesNotExist:
            mentorship_goal_list.append({
                "goal": goal,
                "status": ''
            })

        if goal.category not in category_list:
            category_list.append(goal.category)

    data = {
        "category_list": category_list,
        "mentorship_goal_list": mentorship_goal_list,
    }
    # print(data)

    return data


def dashboardUserGoal(user, type):
    user_goal_list = []
    category_list = []

    if type == 'Learner':
        user_goals = UserDrivenGoal.objects.filter(
            created_by=user, is_deleted=False, goal_type="User Driven", is_active=True)

    for goal in user_goals:
        # print("category", goal.category)
        try:
            goal_log = UserGoalLog.objects.filter(user=user, goal=goal, created_at__date=date.today()).first()
            user_goal_list.append({
                "goal": goal,
                "status": goal_log.status if goal_log else ""
            })
        except UserGoalLog.DoesNotExist:
            user_goal_list.append({
                "goal": goal,
                "status": ''
            })

        if goal.category not in category_list:
            category_list.append(goal.category)

    data = {
        "category_list": category_list,
        "user_goal_list": user_goal_list,
    }
    # print("user_goal_data", data)

    return data


@login_required
def mentorship_goal_comment(request):
    if request.method == "POST":
        id = request.POST['goal_id']
        comment = request.POST['comment']
        comment = MentorshipGoalComment.objects.create(created_by=request.user, comment=comment)
        try:
            goal = UserDrivenGoal.objects.get(pk=id)
        except UserDrivenGoal.DoesNotExist:
            return HttpResponse('Goal does not exist')
        goal.comment.add(comment)
        if request.session['user_type'] == 'Mentor':
            return redirect(reverse('leaderboard:view_comment', kwargs={'pk': id}))
        else:
            return redirect(reverse('leaderboard:mentorship_goal_detail', kwargs={'pk': id}))


@method_decorator(login_required, name='dispatch')
class ViewComment(View):
    def get(self, request, pk):
        goal = UserDrivenGoal.objects.get(pk=pk)
        # comment_list = goal.comment.all()
        # print("id", comment_list)
        request_list = []
        # for learner in goal.learners.all():
        #     learner_comment = ""
        #     approve_request = ""
        #     for comment in goal.comment.all():
        #         if comment.created_by == learner:
        #             learner_comment = comment.comment
        #     for approve in goal.approve_request.all():
        #         if learner == approve:
        #             approve_request = "Yes"

        #     learner_list.append({
        #         "goal_id": pk,
        #         "user_id": learner.pk,
        #         "learner": learner.first_name+" "+learner.last_name,
        #         "comment": learner_comment,
        #         "approve_request": approve_request
        #     })

        for approve_req in goal.approve_request.all():
            if approve_req.company.filter(id=request.session['company_id']).exists():
                request_list.append({
                    "goal_id": pk,
                    "user_id": approve_req.pk,
                    "learner": f"{approve_req.first_name} {approve_req.last_name}",
                })

        comment_list = []
        for comment in goal.comment.all():
            print("created_by", comment.created_by, goal.learners.all())
            if comment.created_by == request.user:
                comment_list.append(comment)
            for learner in goal.learners.all():
                if comment.created_by == learner:
                    comment_list.append(comment)

        context = {
            "goal": goal,
            "request_list": request_list,
            "comment": comment_list,
            "user_progress_chart": user_progress_chart(goal)

        }
        # print("context", context)

        # print("learner_list", learner_list)

        return render(request, 'view_request.html', context)


@login_required
def approve_learner_goal(request):
    if request.method == "POST":
        goal_id = request.POST['goal_id']
        user_id = request.POST['user_id']
        status = request.POST['status']
        print(goal_id, user_id, status)
        try:
            goal = UserDrivenGoal.objects.get(id=goal_id)
        except UserDrivenGoal.DoesNotExist:
            return HttpResponse('Goal does not exist')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponse('User does not exist')

        userGoal = UserGoalLog.objects.get(user=user, goal=goal)
        print("usergoal line 1556", userGoal)
        userGoal.status = status
        userGoal.save()
        goal.approve_request.remove(user)
        goal.save()

        if (status == 'ApprovedByMentor'):
            notify.send(user, recipient=user, verb=goal.heading, description="Mentorship Goal " +
                                                                             goal.heading + " has been approved by mentor")
        else:
            notify.send(user, recipient=user, verb=goal.heading, description="Mentorship Goal " +
                                                                             goal.heading + " has been rejected by mentor")

        return HttpResponse('Success')


@login_required
def suggested_goals_data(request):
    if request.method == "GET":
        heading = request.GET.get('name')
        try:
            goal = UserDrivenGoal.objects.get(heading__iexact=heading)
        except UserDrivenGoal.DoesNotExist:
            return JsonResponse({"success": False})
        response = {
            "success": True,
            "heading": goal.heading,
            "description": goal.description,
            "duration_number": goal.duration_number,
            "duration_time": goal.duration_time,
            "category": goal.category,
            "type": goal.goal_type,
            "difficulty_level": goal.difficulty_level,
            "priority_level": goal.priority_level,
            "frequency": goal.frequency
        }
        return JsonResponse(response)


@method_decorator(login_required, name='dispatch')
class MentorshipGoalDetail(View):
    def get(self, request, pk):
        goal = UserDrivenGoal.objects.get(pk=pk)
        # print("goal", goal)
        comment_list = []
        for comment in goal.comment.all():
            if comment.created_by == request.user or comment.created_by == goal.created_by:
                comment_list.append(comment)

        try:
            goal_log = UserGoalLog.objects.filter(user=request.user, goal=goal).first()

            status = goal_log.status if goal_log else ""
            progress_percentage = goal_log.progress_percentage if goal_log else 0

        except UserGoalLog.DoesNotExist:
            status = ''
            progress_percentage = 0

        context = {
            "date": datetime.now(),
            "is_expired": 'False' if goal.complete_till > aware_time(datetime.now()) else 'True',
            "goal": goal,
            "comment": comment_list,
            "status": status,
            "progress_percentage": progress_percentage

        }
        print("context", context)
        return render(request, 'mentorship_goal_detail.html', context)


@method_decorator(login_required, name='dispatch')
class GoalSetting(View):
    def get(self, request):
        program_manager = User.objects.get(pk=request.user.id)
        company_list = []
        for company in program_manager.company.all():
            auto_approve = AutoApproveGoal.objects.filter(company=company).first()
            if auto_approve:
                is_approve = auto_approve.is_auto_approve
            else:
                is_approve = False
            company_list.append({
                "company": company,
                "is_approve": is_approve
            })

        print("company", company_list)
        context = {
            "company_list": company_list
        }
        return render(request, 'goal_setting.html', context)

    def post(self, request):
        companys = request.POST.getlist('company')
        try:
            is_true = request.POST['is_true']
        except:
            is_true = False
        print("data", companys, is_true)
        for company in companys:
            comp = Company.objects.get(pk=company)
            print("company", comp)
            try:
                auto_approve_goal = AutoApproveGoal.objects.get(company=comp)
                auto_approve_goal.is_auto_approve = is_true
                auto_approve_goal.updated_by = request.user
                auto_approve_goal.save()
            except:
                AutoApproveGoal.objects.create(company=comp, is_auto_approve=is_true, created_by=request.user)

        return redirect(reverse('leaderboard:goal_setting'))
