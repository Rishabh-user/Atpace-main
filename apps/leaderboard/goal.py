from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from apps.leaderboard.models import UserGoalLog, UserDrivenGoal, SystemDrivenGoal, AutoApproveGoal
from datetime import date, datetime
from apps.content.models import Channel
from ..users.utils import aware_time


@login_required
def user_goal_log(request):
    if request.method == "POST":
        id = request.POST['id']
        status = request.POST['status']
        try:
            goal = UserDrivenGoal.objects.get(id=id)
        except UserDrivenGoal.DoesNotExist:
            return HttpResponse('Goal does not exist')
        print("goal_type", goal.goal_type, status)
        # print(goal_auto_approve(request.user, goal.created_by))
        if(goal.goal_type == 'Mentorship' and status == '100'):
            is_auto_approve = goal_auto_approve(request.user, goal.created_by)
            if is_auto_approve == False:
                goal.approve_request.add(request.user)
                goal_status = "RequestForApprove"
            else:
                goal_status = "Completed"
            try:
                userGoal = UserGoalLog.objects.get(user=request.user, goal=goal)
                print("usergoal", userGoal)
                userGoal.status = goal_status
                userGoal.progress_percentage = status
                userGoal.updated_by = request.user
                userGoal.save()
            except:
                UserGoalLog.objects.create(user=request.user, goal=goal,
                                           status=goal_status, progress_percentage=status, created_by=request.user)

        elif goal.goal_type == 'Mentorship':
            try:
                userGoal = UserGoalLog.objects.get(user=request.user, goal=goal)
                print("usergoal", userGoal)
                userGoal.status = "Started"
                userGoal.progress_percentage = status
                userGoal.updated_by = request.user
                userGoal.save()
            except:
                UserGoalLog.objects.create(user=request.user, created_by=request.user,
                                           goal=goal, progress_percentage=status, status="Started")

            return HttpResponse('Success')
        else:
            try:
                userGoal = UserGoalLog.objects.get(user=request.user, goal=goal, created_at__date=date.today())
                print("usergoal 54", userGoal, status)
                if status.isnumeric():
                    print("numeric")
                    userGoal.progress_percentage = status
                    if status == '100':
                        userGoal.status ="Completed"
                else:
                    userGoal.status = status
                userGoal.updated_by = request.user
                userGoal.save()
            except:
                if status.isnumeric():
                    UserGoalLog.objects.create(user=request.user, goal=goal,
                                               progress_percentage=status, created_by=request.user)
                else:
                    UserGoalLog.objects.create(user=request.user, goal=goal, status=status, created_by=request.user)
            return HttpResponse('Success')


@login_required
def assign_journey_to_goal(request):
    if request.method == "POST":
        channel = request.POST['channel']
        content = request.POST.getlist('content[]')
        goal_id = request.POST['goal_id']
        print("channel content", channel, content, goal_id)

        goal = SystemDrivenGoal.objects.get(id=goal_id)
        channel = Channel.objects.get(pk=channel)
        print("goal", goal, channel)
        goal.journey = channel
        if content:
            goal.content = content
        goal.save()
        context = {
            "msg": "Success"
        }
        print("context", context)
        return JsonResponse(context)


# @login_required
def user_progress_chart(goal):
    chart_list = []
    for learner in goal.learners.all():
        try:
            goal_log = UserGoalLog.objects.filter(goal=goal, user=learner).first()
            progress = goal_log.progress_percentage
        except:
            progress = 0

        chart_list.append({
            "progress": progress,
            "learner": learner.first_name + " " + learner.last_name
        })
    print("chart list", chart_list)

    return chart_list


def individual_goal_progress_chart(goalLog):
    data = []
    for log in goalLog:
        # print(log.status, log.created_at)
        gdate = log.created_at.strftime("%d")
        month = log.created_at.strftime("%m")
        year = log.created_at.strftime("%Y")
        if(log.status == 'Completed'):
            data.append({
                "date": year+"-"+month+"-"+gdate,
                "completed": "1",
                "skipped": "0",
                "failed": "0"
            })

        elif(log.status == 'Failed'):
            data.append({
                "date": year+"-"+month+"-"+gdate,
                "completed": "0",
                "skipped": "0",
                "failed": "1"
            })
        elif(log.status == 'Skipped'):
            data.append({
                "date": year+"-"+month+"-"+gdate,
                "completed": "0",
                "skipped": "1",
                "failed": "0"
            })
    return data


def user_goal_bar_chart(user, goals):
    goal_log_list = []
    for goal in goals:
        goalLog = UserGoalLog.objects.filter(user=user, goal=goal)
        # print("goal_log", goal_log)
        completed = 0
        failed = 0
        skipped = 0
        for log in goalLog:
            if(log.status == 'Completed'):
                completed = completed + 1

            elif(log.status == 'Failed'):
                failed = failed + 1

            elif(log.status == 'Skipped'):
                skipped = skipped + 1

        goal_log_list.append({
            "name": goal.heading,
            "completed": completed,
            "skipped": skipped,
            "failed": failed,
        })
    return goal_log_list


def user_goal_donut_chart(goals):
    # Donut Chart Data
    Gain_Clarity = 0
    Learn = 0
    Follow_Through = 0
    Health = 0

    for goal in goals:
        if goal.goal_type == 'Mentorship' and goal.complete_till > aware_time(datetime.now()):
            if(goal.category == 'Gain Clarity'):
                Gain_Clarity = Gain_Clarity + 1
            elif(goal.category == 'Learn'):
                Learn = Learn + 1
            elif(goal.category == 'Health'):
                Health = Health + 1
            else:
                Follow_Through = Follow_Through + 1
        elif goal.goal_type == 'User Driven':
            if(goal.category == 'Gain Clarity'):
                Gain_Clarity = Gain_Clarity + 1
            elif(goal.category == 'Learn'):
                Learn = Learn + 1
            elif(goal.category == 'Health'):
                Health = Health + 1
            else:
                Follow_Through = Follow_Through + 1

    category_list = (
        {
            "label": 'Gain Clarity',
            "value": Gain_Clarity
        },
        {
            "label": 'Learn',
            "value": Learn
        },
        {
            "label": 'Health',
            "value": Health
        },
        {
            "label": 'Follow Through',
            "value": Follow_Through
        },
    )
    return category_list


def mentorship_goal_status_chart(user, goals):
    # Status Donut Chart Data
    Requested = 0
    Rejected = 0
    Approved = 0

    for goal in goals:
        if goal.complete_till > aware_time(datetime.now()):
            goal_log = UserGoalLog.objects.filter(user=user, goal=goal).first()
            if goal_log:
                if(goal_log.status == 'RequestForApprove'):
                    Requested = Requested + 1
                elif(goal_log.status == 'RejectedByMentor'):
                    Rejected = Rejected + 1
                elif(goal_log.status == 'ApprovedByMentor'):
                    Approved = Approved + 1

    status_chart = (
        {
            "label": 'Requested',
            "value": Requested
        },
        {
            "label": 'Rejected',
            "value": Rejected
        },
        {
            "label": 'Approved',
            "value": Approved
        },
    )
    return status_chart


def mentorship_goal_progress_chart(user, goals):
    goal_progress_chart = []
    for goal in goals:
        if goal.complete_till > aware_time(datetime.now()):
            goalLog = UserGoalLog.objects.filter(user=user, goal=goal).first()
            if goalLog:
                goal_progress_chart.append({
                    "name": goal.heading,
                    "progress": goalLog.progress_percentage,
                })
    return goal_progress_chart


def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3


def goal_auto_approve(learner, mentor):
    # print("learenr mentor", learner, mentor)
    learner_company = learner.company.all()
    mentor_company = mentor.company.all()
    # print(learner_company, mentor_company)
    company = intersection(learner_company, mentor_company)
    company = company[0]
    # print(company)
    auto_approve_obj = AutoApproveGoal.objects.filter(company=company).first()
    if auto_approve_obj:
        is_auto_approve = auto_approve_obj.is_auto_approve
    else:
        is_auto_approve = False
    # print(is_auto_approve)
    return is_auto_approve
