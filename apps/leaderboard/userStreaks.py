from .models import UserStreakCount
from apps.content.models import UserCourseStart, TestAttempt, SurveyChannel
from datetime import datetime, timedelta
from apps.atpace_community.models import Post, SpaceJourney
from apps.community.models import LearningJournals, WeeklyLearningJournals
from apps.survey_questions.models import SurveyAttempt
from apps.content.utils import company_journeys
from django.db.models.query_utils import Q


def userStreakCount(user):
    streak_count = UserStreakCount.objects.filter(user=user).first()
    if not streak_count:
        streak_count = UserStreakCount.objects.create(
            user=user, streak_count=1, streak_count_start_date=datetime.now())
    # print("streak_count", streak_count)
    return streak_count.streak_count


def userStreakActivity(user):
    streak_count = userStreakCount(user)
    start_date = UserStreakCount.objects.filter(user=user).first().streak_count_start_date
    completion = 0
    CourseStart = userStreakCourseStart(user, streak_count, start_date)
    # print("CourseStart", CourseStart)
    testAttempts = userStreakTestAttempts(user, streak_count, start_date)
    # print("testAttempts", testAttempts)
    post = userStreakPost(user, streak_count, start_date)
    # print("post", post)
    learningJournals = userStreakLearningJournals(user, streak_count, start_date)
    # print("learningJournals", learningJournals)
    weeklyLearningJournals = userStreakWeeklyLearningJournals(user, streak_count, start_date)
    # print("weeklyLearningJournals", weeklyLearningJournals)
    surveyAttempt = userStreakSurveyAttempt(user, streak_count, start_date)
    # print("surveyAttempt", surveyAttempt['total_completion'])
    completion = CourseStart['total_completion'] + testAttempts['total_completion'] + post['total_completion'] + \
        learningJournals['total_completion'] + \
        weeklyLearningJournals['total_completion'] + surveyAttempt['total_completion']
    data = {
        "CourseStart": CourseStart,
        "testAttempts": testAttempts,
        "post": post,
        "learningJournals": learningJournals,
        "weeklyLearningJournals": weeklyLearningJournals,
        "surveyAttempt": surveyAttempt,
        "total_completion": completion

    }
    # print("data", data)
    # chartData = lineChartData(user, streak_count, start_date)
    return data


def userStreakCourseStart(user, streak_count, start_date):
    # days = datetime.today() - timedelta(days=streak_count)
    # print("streak_count", streak_count)
    # print("days", days)
    # completion = 0
    # user_course = UserCourseStart.objects.filter(
    #     user=user, created_at__lte=datetime.today(), created_at__gte=days, status='Complete')
    # for course in user_course:
    #     completion = completion + 1
    i = 0
    data = []
    total_completion = 0
    for i in range(streak_count + 1):
        completion = 0
        days = start_date + timedelta(days=i)
        date = days.strftime("%d")
        month = days.strftime("%m")
        year = days.strftime("%Y")

        # print("date", date)
        # print("month", month)
        # print("year", year)
        user_course = UserCourseStart.objects.filter(
            user=user, created_at__day=date, created_at__month=6, created_at__year=2022, status='Complete')
        # print("user_course", user_course)

        for course in user_course:
            completion = completion + 1
            total_completion = total_completion + 1

        data.append({
            "date": date+"/"+month+"/"+year,
            "complete": completion
        })
    data = {
        "data": data,
        "total_completion": total_completion
    }

    return data


def userStreakTestAttempts(user, streak_count, start_date):
    # days = datetime.today() - timedelta(days=streak_count)
    # completion = 0
    # testAttempt = TestAttempt.objects.filter(
    #     user=user, created_at__lte=datetime.today(), created_at__gte=days)
    # for test in testAttempt:
    #     completion = completion + 1
    i = 0
    data = []
    total_completion = 0
    for i in range(streak_count + 1):
        completion = 0
        days = start_date + timedelta(days=i)
        date = days.strftime("%d")
        month = days.strftime("%m")
        year = days.strftime("%Y")

        # print("date", date)
        # print("month", month)
        # print("year", year)
        testAttempt = TestAttempt.objects.filter(
            user=user, created_at__day=date, created_at__month=6, created_at__year=2022)
        # print("testAttempt", testAttempt)

        for test in testAttempt:
            completion = completion + 1
            total_completion = total_completion + 1

        data.append({
            "date": date+"/"+month+"/"+year,
            "complete": completion
        })
    data = {
        "data": data,
        "total_completion": total_completion
    }
    return data


def userStreakPost(user, streak_count, start_date):
    # days = datetime.today() - timedelta(days=streak_count)
    # completion = 0

    # posts = Post.objects.filter(
    #     created_by=user, created_at__lte=datetime.today(), created_at__gte=days)
    # for post in posts:
    #     completion = completion + 1
    i = 0
    data = []
    total_completion = 0
    for i in range(streak_count + 1):
        completion = 0
        days = start_date + timedelta(days=i)
        date = days.strftime("%d")
        month = days.strftime("%m")
        year = days.strftime("%Y")

        # print("date", date)
        # print("month", month)
        # print("year", year)
        posts = Post.objects.filter(inappropriate_content=False,
            created_by=user, created_at__day=date, created_at__month=6, created_at__year=2022)
        # print("posts", posts)

        for post in posts:
            completion = completion + 1
            total_completion = total_completion + 1

        data.append({
            "date": date+"/"+month+"/"+year,
            "complete": completion
        })
    data = {
        "data": data,
        "total_completion": total_completion
    }
    return data


def userStreakLearningJournals(user, streak_count, start_date):
    # days = datetime.today() - timedelta(days=streak_count)
    # completion = 0

    # learningJournals = LearningJournals.objects.filter(
    #     user_id=user.id, created_at__lte=datetime.today(), created_at__gte=days)
    # for journal in learningJournals:
    #     completion = completion + 1
    i = 0
    data = []
    total_completion = 0
    for i in range(streak_count + 1):
        completion = 0
        days = start_date + timedelta(days=i)
        date = days.strftime("%d")
        month = days.strftime("%m")
        year = days.strftime("%Y")

        # print("date", date)
        # print("month", month)
        # print("year", year)
        learningJournal = LearningJournals.objects.filter(
            user_id=user.id, created_at__day=date, created_at__month=6, created_at__year=2022)
        # print("learningJournal", learningJournal)

        for journal in learningJournal:
            completion = completion + 1
            total_completion = total_completion + 1

        data.append({
            "date": date+"/"+month+"/"+year,
            "complete": completion
        })
    data = {
        "data": data,
        "total_completion": total_completion
    }
    return data


def userStreakWeeklyLearningJournals(user, streak_count, start_date):
    # days = datetime.today() - timedelta(days=streak_count)
    # completion = 0

    # weeklyLearningJournals = WeeklyLearningJournals.objects.filter(
    #     created_by=user, created_at__lte=datetime.today(), created_at__gte=days)
    # for journal in weeklyLearningJournals:
    #     completion = completion + 1
    i = 0
    data = []
    total_completion = 0
    for i in range(streak_count + 1):
        completion = 0
        days = start_date + timedelta(days=i)
        date = days.strftime("%d")
        month = days.strftime("%m")
        year = days.strftime("%Y")

        # print("date", date)
        # print("month", month)
        # print("year", year)
        weeklyLearningJournals = WeeklyLearningJournals.objects.filter(
            created_by=user, created_at__day=date, created_at__month=6, created_at__year=2022)
        # print("weeklyLearningJournals", weeklyLearningJournals)

        for journal in weeklyLearningJournals:
            completion = completion + 1
            total_completion = total_completion + 1

        data.append({
            "date": date+"/"+month+"/"+year,
            "complete": completion
        })
    data = {
        "data": data,
        "total_completion": total_completion
    }
    return data


def userStreakSurveyAttempt(user, streak_count, start_date):
    # days = datetime.today() - timedelta(days=streak_count)
    # completion = 0

    # surveyAttempt = SurveyAttempt.objects.filter(
    #     user=user, created_at__lte=datetime.today(), created_at__gte=days)
    # for survey in surveyAttempt:
    #     completion = completion + 1

    i = 0
    data = []
    total_completion = 0
    for i in range(streak_count + 1):
        completion = 0
        days = start_date + timedelta(days=i)
        date = days.strftime("%d")
        month = days.strftime("%m")
        year = days.strftime("%Y")

        # print("date", date)
        # print("month", month)
        # print("year", year)
        surveyAttempt = SurveyAttempt.objects.filter(
            user=user, created_at__day=date, created_at__month=6, created_at__year=2022)
        # print("surveyAttempt", surveyAttempt)

        for survey in surveyAttempt:
            completion = completion + 1
            total_completion = total_completion + 1

        data.append({
            "date": date+"/"+month+"/"+year,
            "complete": completion
        })
    data = {
        "data": data,
        "total_completion": total_completion
    }
    return data


def lineChartData(user, user_type=None, company_id=None):
    streak_count = userStreakCount(user)
    start_date = UserStreakCount.objects.filter(user=user).first().streak_count_start_date
    i = 0
    data = []
    for i in range(streak_count + 1):
        content = 0
        lJournal = 0
        wlJournal = 0
        test = 0
        post = 0
        survey = 0
        days = start_date + timedelta(days=i)
        date = days.strftime("%d")
        month = days.strftime("%m")
        year = days.strftime("%Y")

        # print("date", date)
        # print("month", month)
        # print("year", year)
        journeys = company_journeys(user_type, user, company_id)
        journey_list = []
        for journey in journeys:
            journey_list.append(journey.id)
        user_course = UserCourseStart.objects.filter(
            user=user, created_at__day=date, created_at__month=month, created_at__year=year, channel__in=journeys, status='Complete')
        # print("user_course", user_course)

        for course in user_course:
            content = content + 1

        learningJournal = LearningJournals.objects.filter(
            user_id=user.id, created_at__day=date, created_at__month=month, created_at__year=year, journey_id__in=journey_list)
        # print("learningJournal", learningJournal)

        for journal in learningJournal:
            lJournal = lJournal + 1

        weeklyLearningJournals = WeeklyLearningJournals.objects.filter(
            created_by=user, created_at__day=date, created_at__month=month, created_at__year=year, journey_id__in=journey_list)
        # print("weeklyLearningJournals", weeklyLearningJournals)

        for wjournal in weeklyLearningJournals:
            wlJournal = wlJournal + 1

        testAttempt = TestAttempt.objects.filter(
            user=user, created_at__day=date, created_at__month=month, created_at__year=year, channel__in=journeys)
        # print("testAttempt", testAttempt)

        for tests in testAttempt:
            test = test + 1

        space_channel = SpaceJourney.objects.filter(journey__in=journeys)
        space_list = []
        for space in space_channel:
            space_list.append(space.space)

        posts = Post.objects.filter(Q(space__in=space_list) | Q(space__privacy='Private'), inappropriate_content=False,
                                    created_by=user, created_at__day=date, created_at__month=month, created_at__year=year)
        # print("posts", posts)
        if posts:
            for posts in posts:
                post = post + 1

        survey_channel = SurveyChannel.objects.filter(channel__in=journeys)
        # print("survey", survey_channel)
        survey_list = []
        for sur in survey_channel:
            survey_list.append(sur.survey)
        # print("survey_list", survey_list)

        surveyAttempt = SurveyAttempt.objects.filter(
            user=user, created_at__day=date, created_at__month=month, created_at__year=year, survey__in=survey_list)
        # print("surveyAttempt", surveyAttempt)

        for surveys in surveyAttempt:
            survey = survey + 1

        data.append({
            "date": f"{year}-{month}-{date}",
            "quest": content,
            "learning_journal": lJournal,
            "weekly_learning_journal": wlJournal,
            "test": test,
            "post": post,
            "survey": survey

        })
    print("final data", data)
    return data
