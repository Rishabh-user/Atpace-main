from django.db.models import Avg, Count
from apps.mentor.models import AssignMentorToUser
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.api.serializers import DashboardSerializer, UserGoalprogressSerializer, UserGoalsSerializer, UserIdSerializer
from apps.api.utils import badge_image, user_dashboard_api, mentorship_goal_list, mentorship_goal_detail
from apps.atpace_community.utils import avatar, certificate_file
from apps.leaderboard.models import UserBadgeDetails, AutoApproveGoal, UserDrivenGoal, MentorshipGoalComment, UserPoints, UserStreakHistory, UserGoalLog
from apps.leaderboard.userStreaks import lineChartData, userStreakCount
from apps.users.models import Company, User, UserEarnedPoints, UserTypes
from datetime import date
from apps.leaderboard.views import UserBestStreak, send_push_notification
from apps.leaderboard.goal import individual_goal_progress_chart, goal_auto_approve, user_goal_bar_chart, user_goal_donut_chart, mentorship_goal_status_chart, mentorship_goal_progress_chart
from apps.users.templatetags.tags import get_mentor_mentees
from rest_framework.permissions import AllowAny
from apps.content.models import UserCertificate, CertificateSignature
from apps.users.utils import send_user_certificate_mail

class Userbadge(APIView):
    def get(self, request, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User does not exist or Invalid Id", "Success": False}, status=status.HTTP_404_NOT_FOUND)
        userbadge = UserBadgeDetails.objects.filter(user=user)
        userbadges = []
        if len(userbadge) > 0:
            for badge in userbadge:
                print(badge)
                userbadges.append({
                    "current_badge": badge.current_badge,
                    "points_earned": badge.points_earned,
                    "badge_acquired": badge.badge_acquired,
                    "badge_revoked": badge.badge_revoked,
                })
            data = {
                "data": userbadges,
                "Success": True,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response({"message": "No data available", "Success": False}, status=status.HTTP_404_NOT_FOUND)


class UserPoint(APIView):
    permission_classes = [AllowAny]
    def get(self, request, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User does not exist or Invalid Id", "Success": False}, status=status.HTTP_404_NOT_FOUND)
        userpoints = UserPoints.objects.filter(user=user)
        badges = UserBadgeDetails.objects.filter(user=user)
        try:
            user_points = UserEarnedPoints.objects.get(user=user)
            total_points = user_points.total_points
        except Exception:
            total_points = 0

        userpoint_list = [{"name": points.label.name if points.label else '', "label": points.label.label if points.label else '',
                           "points": points.point, "comment": points.comment, } for points in userpoints]

        badges_list = [{"current_badge": badge.current_badge.name, "badge_image": badge_image(
            badge.current_badge), "badge_label": badge.current_badge.label.label, "points_earned": badge.points_earned, "badge_acquired": badge.badge_acquired, "badge_revoked": badge.badge_revoked} for badge in badges] if badges else []

        streak_count = userStreakCount(user)
        # try:
        #     best_streak = UserStreakHistory.objects.get(user=user)
        #     best_streak = best_streak.streak
        # except Exception:
        #     best_streak = streak_count
        best_streak = UserBestStreak(user)
        data = {
            "message": "UserBadg Points and Streak details",
            "points": userpoint_list,
            "total_points": total_points,
            "badges": badges_list,
            "streak_count": streak_count,
            "best_streak": best_streak,
            "Success": True,
        }
        return Response(data, status=status.HTTP_200_OK)


class Dashboard(APIView):
    serializer_class = DashboardSerializer
    def post(self, request):
        print(request.data)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                company = Company.objects.get(id=request.data['company_id'])
            except Company.DoesNotExist:
                return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user_type = UserTypes.objects.get(type=request.data['user_type'])
            except UserTypes.DoesNotExist:
                return Response({"message": "User Type required", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user = User.objects.get(id=request.data['user_id'], userType__type=user_type.type)
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

            data = user_dashboard_api(user, user_type.type, company.id)
            response = {
                "message": "User Dashboard Details",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserGoals(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_goals = UserDrivenGoal.objects.filter(created_by=user, is_active=True, is_deleted=False)
        data = []
        for goal in user_goals:
            userGoal = UserGoalLog.objects.filter(user=user, goal=goal, created_at__date=date.today())
            data.append({
                "id": goal.id,
                "heading": goal.heading,
                "description": goal.description,
                "goal_type": "User Driven",
                "duration_number": goal.duration_number,
                "duration_time": goal.duration_time,
                "category": goal.category,
                "priority_level": goal.priority_level,
                "frequency": goal.frequency,
                "today_status": userGoal.first().status if userGoal else "",
                "today_progress": userGoal.first().progress_percentage if userGoal else 0,
                "created_by": f"{user.first_name} {user.last_name}",
                "created_by_id": user.id
            })
        response = {
            "message": "User Goal data",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = UserGoalsSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=self.kwargs['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            heading = request.data['heading']
            description = request.data['description']
            duration_number = request.data['duration_number']
            duration_time = request.data['duration_time']
            category = request.data['category']
            priority_level = request.data['priority_level']
            frequency = request.data['frequency']
            goal = UserDrivenGoal.objects.create(created_by=user, heading=heading, description=description, goal_type="User Driven", duration_number=duration_number,
                                                 duration_time=duration_time, category=category, priority_level=priority_level, frequency=frequency)
            description = f"""Hi {user.first_name} {user.last_name}!
            It's great you set your goals, now let's take some assessments so we can find the right courses to help you grow!"""

            context = {
                "screen": "Assessment",
            }
            send_push_notification(user, 'Take Assessment', description, context)
            data = []
            data.append({
                "id": goal.id,
                "heading": heading,
                "description": description,
                "goal_type": "User Driven",
                "duration_number": duration_number,
                "duration_time": duration_time,
                "category": category,
                "priority_level": priority_level,
                "frequency": frequency,
                "created_by": f"{user.first_name} {user.last_name}",
                "created_by_id": user.id
            })
            response = {
                "message": "User Goal Created",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetDeleteUserGoal(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            goal = UserDrivenGoal.objects.get(id=self.kwargs['goal_id'])
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "goal not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if goal.is_active:
            userGoal = UserGoalLog.objects.filter(user=user, goal=goal, created_at__date=date.today())
            response = {
                "id": goal.id,
                "heading": goal.heading,
                "description": goal.description,
                "goal_type": "User Driven",
                "duration_number": goal.duration_number,
                "duration_time": goal.duration_time,
                "category": goal.category,
                "priority_level": goal.priority_level,
                "frequency": goal.frequency,
                "today_status": userGoal.first().status if userGoal else "",
                "today_progress": userGoal.first().progress_percentage if userGoal else 0,
                "created_by": f"{user.first_name} {user.last_name}",
                "created_by_id": user.id
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": "goal is inactive", "success": False}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            goal = UserDrivenGoal.objects.get(id=self.kwargs['goal_id'])
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "goal not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if goal.created_by != user:
            return Response({"message": "You are not authorized to delete this goal", "success": False}, status=status.HTTP_404_NOT_FOUND)

        if goal.is_active:
            goal.is_active = False
            goal.is_deleted = True
            goal.save()
            response = {
                "message": f"goal {goal.heading} successfully deleted",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": "goal is inactive", "success": False}, status=status.HTTP_404_NOT_FOUND)


class UpdateUserGoal(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserGoalsSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=self.kwargs['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                goal = UserDrivenGoal.objects.get(
                    pk=self.kwargs['goal_id'], created_by=user, is_active=True, is_deleted=False)
            except UserDrivenGoal.DoesNotExist:
                return Response({"message": "goal not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            heading = request.data['heading']
            description = request.data['description']
            duration_number = request.data['duration_number']
            duration_time = request.data['duration_time']
            category = request.data['category']
            priority_level = request.data['priority_level']
            frequency = request.data['frequency']
            UserDrivenGoal.objects.filter(id=goal.id).update(heading=heading, description=description, duration_number=duration_number,
                                                             duration_time=duration_time, category=category, priority_level=priority_level, frequency=frequency)
            response = {
                "id": goal.id,
                "heading": heading,
                "description": description,
                "goal_type": "User Driven",
                "duration_number": duration_number,
                "duration_time": duration_time,
                "category": category,
                "priority_level": priority_level,
                "frequency": frequency,
                "created_by": f"{user.first_name} {user.last_name}",
                "created_by_id": user.id
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserGoalLogProgress(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserGoalprogressSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=self.kwargs['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                goal = UserDrivenGoal.objects.get(pk=request.data['goal_id'])
            except UserDrivenGoal.DoesNotExist:
                return Response({"message": "goal not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            goal_status = request.data['status']
            if goal.is_active and not goal.is_deleted:
                userGoal = UserGoalLog.objects.filter(user=user, goal=goal, created_at__date=date.today())
                print("usergoal", userGoal)
                if not userGoal:
                    if isinstance(goal_status, int):
                        userGoal = UserGoalLog.objects.create(
                            user=user, goal=goal, progress_percentage=goal_status, created_by=user)
                    else:
                        userGoal = UserGoalLog.objects.create(
                            user=user, goal=goal, status=goal_status, created_by=user)
                else:
                    userGoal = userGoal.first()
                    if isinstance(goal_status, int):
                        userGoal.progress_percentage = goal_status
                    else:
                        userGoal.status = goal_status
                    userGoal.updated_by = user
                    userGoal.save()
                return Response({"message": "goal progress updated", "success": True}, status=status.HTTP_200_OK)
            return Response({"message": "goal is inactive or deleted", "success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MentorshipGoals(APIView):
    def get(self, request):
        user_id = self.request.query_params.get('user_id')
        user_type = self.request.query_params.get('user_type')
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user_type = UserTypes.objects.get(type=user_type)
        except UserTypes.DoesNotExist:
            return Response({"message": "User Type does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=user_id, userType__type=user_type.type)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "message": "Mentorship Goal",
            "success": True,
            "mentorship_goals": mentorship_goal_list(user, user_type.type, company)
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        user_id = self.request.query_params.get('user_id')
        user_type = self.request.query_params.get('user_type')
        try:
            user_type = UserTypes.objects.get(type=user_type)
        except UserTypes.DoesNotExist:
            return Response({"message": "User Type does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=user_id, userType__type=user_type.type)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            if(request.data['heading'] and request.data['description'] and request.data['priority'] and request.data['category'] and request.data['duration_number'] and request.data['duration_time'] and request.data['goal_type']):
                heading = request.data['heading']
                description = request.data['description']
                category = request.data['category']
                priority = request.data['priority']
                duration_number = request.data['duration_number']
                duration_time = request.data['duration_time']
                goal_type = request.data['goal_type']
                if(goal_type == 'Mentorship'):
                    learners = request.data['learners']

                    complete_by = request.data['due_date']

                    complete_by = complete_by.split("-")
                    complete_till = date(int(complete_by[0]), int(complete_by[1]), int(complete_by[2]))
                    goal = UserDrivenGoal.objects.create(created_by=user, heading=heading, complete_till=complete_till,
                                                         description=description, goal_type=goal_type, duration_number=duration_number, duration_time=duration_time, category=category, priority_level=priority)
                    if isinstance(learners, str):
                        learners = learners.split(",")
                    for learner in learners:
                        goal.learners.add(learner)

                else:
                    frequency = request.data['frequency']

                    goal = UserDrivenGoal.objects.create(created_by=user, heading=heading,
                                                         description=description, goal_type=goal_type, duration_number=duration_number, duration_time=duration_time, category=category, priority_level=priority, frequency=frequency)
                data = {
                    "id": goal.id,
                    "heading": heading,
                    "description": description,
                    "goal_type": goal_type,
                    "duration_number": duration_number,
                    "duration_time": duration_time,
                    "category": category,
                    "priority_level": priority,
                    "due_date": complete_till,
                    "created_by": f"{user.first_name} {user.last_name}",
                    "created_by_id": user.id
                }

                response = {
                    "message": "Goal created successfully",
                    "Success": True,
                    "Goal": data
                }
                return Response(response, status=status.HTTP_200_OK)
        except:
            return Response({"message": "All fields are required!", "success": False}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            (request.data['heading'] and request.data['due_date'] and request.data['learners'] and request.data['description'] and request.data['priority']
             and request.data['category'] and request.data['duration_number'] and request.data['duration_time'] and request.data['goal_type'])
        except:
            return Response({"message": "All fields are required!", "success": False}, status=status.HTTP_404_NOT_FOUND)

        try:
            id = request.data['id']
            goal = UserDrivenGoal.objects.get(pk=id)
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "Goal does not exist!", "success": False}, status=status.HTTP_404_NOT_FOUND)

        user_id = self.request.query_params.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if user != goal.created_by:
            return Response({"message": "You are not authorized to update this goal", "success": False}, status=status.HTTP_404_NOT_FOUND)

        heading = request.data['heading']
        description = request.data['description']
        category = request.data['category']
        priority = request.data['priority']
        duration_number = request.data['duration_number']
        duration_time = request.data['duration_time']
        goal_type = request.data['goal_type']
        if(goal_type == 'Mentorship'):
            learners = request.data['learners']

            complete_by = request.data['due_date']

            complete_by = complete_by.split("-")
            print("complete_by", learners)

            complete_till = date(int(complete_by[0]), int(complete_by[1]), int(complete_by[2]))
            print("complete_TILL", complete_till)

            goal.updated_by = user
            goal.heading = heading
            goal.complete_till = complete_till
            goal.description = description
            goal.goal_type = goal_type
            goal.duration_number = duration_number
            goal.duration_time = duration_time
            goal.category = category
            goal.priority_level = priority
            if isinstance(learners, str):
                learners = learners.split(",")
            for learner in learners:
                goal.learners.add(learner)
            goal.save()

        else:
            frequency = request.data['frequency']
            goal.updated_by = user
            goal.heading = heading
            goal.frequency = frequency
            goal.description = description
            goal.goal_type = goal_type
            goal.duration_number = duration_number
            goal.duration_time = duration_time
            goal.category = category
            goal.priority_level = priority
            goal.save()

        data = {
            "id": goal.id,
            "heading": heading,
            "description": description,
            "goal_type": goal_type,
            "duration_number": duration_number,
            "duration_time": duration_time,
            "category": category,
            "priority_level": priority,
            "due_date": complete_till,
            "updated_by": f"{goal.updated_by.first_name} {goal.updated_by.last_name}",
            "updated_by_id": goal.updated_by.id
        }

        response = {
            "message": "Goal updated successfully",
            "success": True,
            "goal": data
        }
        return Response(response, status=status.HTTP_200_OK)


class MentorshipGoalDetail(APIView):
    def get(self, request):
        user_id = self.request.query_params.get('user_id')
        goal_id = self.request.query_params.get('goal_id')
        user_type = self.request.query_params.get('user_type')

        try:
            user_type = UserTypes.objects.get(type=user_type)
        except UserTypes.DoesNotExist:
            return Response({"message": "User Type does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=user_id, userType__type=user_type.type)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            goal = UserDrivenGoal.objects.get(id=goal_id, is_active=True)
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "Goal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "data": mentorship_goal_detail(goal, user, user_type.type)
        }
        return Response(data, status=status.HTTP_200_OK)


class DeleteMentorshipGoal(APIView):
    def post(self, request):
        user_id = self.request.query_params.get('user_id')
        user_type = self.request.query_params.get('user_type')
        goal_id = request.data['id']
        try:
            user = User.objects.get(id=user_id, userType__type=user_type)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            goal = UserDrivenGoal.objects.get(id=goal_id)
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "Goal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if user_type != 'Mentor' or user != goal.created_by:
            return Response({"message": "You are not authorized to delete this goal", "success": False}, status=status.HTTP_404_NOT_FOUND)

        goal.is_deleted = True
        goal.is_active = False
        goal.save()

        return Response({"message": "Goal deleted successfully", "success": True}, status=status.HTTP_200_OK)


class GoalCompleteRequest(APIView):
    def post(self, request):
        goal_id = request.data['goal_id']
        user_id = request.data['user_id']
        data = request.data['status']
        mentor_id = request.data['mentor_id']

        try:
            mentor = User.objects.get(id=mentor_id, userType__type='Mentor')
        except User.DoesNotExist:
            return Response({"message": "Mentor does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            goal = UserDrivenGoal.objects.get(id=goal_id)
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "Goal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        userGoal = UserGoalLog.objects.get(user=user, goal=goal)
        print("usergoal line 1556", userGoal)
        userGoal.status = data
        userGoal.updated_by = mentor
        userGoal.save()
        goal.approve_request.remove(user)
        goal.save()

        return Response({"message": "Status logged successfully", "success": True}, status=status.HTTP_200_OK)


class GoalComment(APIView):
    def post(self, request):
        goal_id = request.data['goal_id']
        comment = request.data['comment']
        user_id = request.data['user_id']
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            goal = UserDrivenGoal.objects.get(id=goal_id)
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "Goal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        comment = MentorshipGoalComment.objects.create(created_by=user, comment=comment)

        goal.comment.add(comment)

        return Response({"message": "Comment created successfully", "success": True}, status=status.HTTP_200_OK)


class LogGoalProgress(APIView):
    def post(self, request):
        goal_id = request.data['goal_id']
        data = request.data['status']
        user_id = request.data['user_id']
        print("efefrerf", data, goal_id, user_id)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            goal = UserDrivenGoal.objects.get(id=goal_id)
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "Goal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        print("goal_type", goal.goal_type)
        if(goal.goal_type == 'Mentorship' and data == 100):
            is_auto_approve = goal_auto_approve(user, goal.created_by)
            if is_auto_approve == False:
                goal.approve_request.add(request.user)
                goal_status = "RequestForApprove"
            else:
                goal_status = "Completed"
            try:
                userGoal = UserGoalLog.objects.get(user=user, goal=goal)
                print("usergoal1", userGoal)
                userGoal.status = goal_status
                userGoal.progress_percentage = data
                userGoal.updated_by = user
                userGoal.save()
            except:
                UserGoalLog.objects.create(user=user, goal=goal, status=goal_status,
                                           created_by=user, progress_percentage=data)

        elif goal.goal_type == 'Mentorship':
            try:
                userGoal = UserGoalLog.objects.get(user=user, goal=goal)
                print("usergoal2", userGoal)
                userGoal.status = "Started"
                userGoal.updated_by = user
                userGoal.progress_percentage = data
                userGoal.save()
            except:
                UserGoalLog.objects.create(user=user, goal=goal, status='Started',
                                           created_by=user, progress_percentage=data)

            return Response({"message": "Status logged successfully", "success": True}, status=status.HTTP_200_OK)

        else:
            try:
                userGoal = UserGoalLog.objects.get(user=user, goal=goal, created_at__date=date.today())
                print("usergoal3", userGoal)
                if isinstance(data, int):
                    userGoal.progress_percentage = data
                else:
                    userGoal.status = data
                userGoal.updated_by = user
                userGoal.save()
            except:
                if isinstance(data, int):
                    UserGoalLog.objects.create(user=user, goal=goal, progress_percentage=data, created_by=user)
                else:
                    UserGoalLog.objects.create(user=user, goal=goal, status=data, created_by=user)

        return Response({"message": "Status logged successfully", "success": True}, status=status.HTTP_200_OK)


class GoalCategoryList(APIView):
    def get(self, request):
        category = UserDrivenGoal.category.field.choices
        category_list = [cat[0] for cat in category]
        status_list = ["Completed", "Failed", "Skipped"]
        data = {
            "category_list": category_list,
            "status_list": status_list,
            "Success": True
        }
        return Response(data, status=status.HTTP_200_OK)


class UserGoalDetail(APIView):
    def get(self, request, **kwargs):
        goal_id = self.kwargs['goal_id']
        try:
            user_goal = UserDrivenGoal.objects.get(pk=goal_id)
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "Goal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        user_id = self.request.query_params.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        goalLog = UserGoalLog.objects.filter(user=user, goal=user_goal).order_by('created_at')
        complete = 0
        failed = 0
        skipped = 0
        for goal in goalLog:
            if(goal.status == 'Completed'):
                complete = complete + 1

            elif(goal.status == 'Failed'):
                failed = failed + 1

            elif(goal.status == 'Skipped'):
                skipped = skipped + 1

        data = individual_goal_progress_chart(goalLog)
        try:
            goal_log = UserGoalLog.objects.filter(user=request.user, goal=user_goal,
                                                  created_at__date=date.today()).first()

            goal_status = goal_log.status if goal_log else ""
            progress_percentage = goal_log.progress_percentage if goal_log else 0

        except UserGoalLog.DoesNotExist:
            goal_status = ''
            progress_percentage = 0
        # print("data", data)
        context = {
            "id": user_goal.id,
            "heading": user_goal.heading,
            "description": user_goal.description,
            "goal_type": "User Driven",
            "duration_number": user_goal.duration_number,
            "duration_time": user_goal.duration_time,
            "category": user_goal.category,
            "priority": user_goal.priority_level,
            "frequency": user_goal.frequency,
            "created_by": f"{user.first_name} {user.last_name}",
            "created_by_id": user.id,
            "today_progress_percentage": progress_percentage,
            "today_status": goal_status,
            "total_completed": complete,
            "total_skipped": skipped,
            "total_failed": failed,
            "goal_progress_chart": data,
        }
        # print("context", context)
        return Response(context, status=status.HTTP_200_OK)

class IndividualGoalProgressChart(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user_goal = UserDrivenGoal.objects.get(pk=self.kwargs['goal_id'])
        except UserDrivenGoal.DoesNotExist:
            return Response({"message": "Goal does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        goalLog = UserGoalLog.objects.filter(user=user, goal=user_goal).order_by('created_at')
        data = individual_goal_progress_chart(goalLog)
        response = {
            "message": "User individual goal progress chart",
            "success": True,
            "Individual_goal_progress": data
        }
        return Response(response, status=status.HTTP_200_OK)

class UserGoalsChart(APIView):
    def get(self, request, **kwargs):
        user_id = self.kwargs['user_id']
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        goals = UserDrivenGoal.objects.filter(created_by=user, is_deleted=False, goal_type="User Driven")
        goal_log_list = user_goal_bar_chart(user, goals)
        category_list = user_goal_donut_chart(goals)

        response = {
            "message": "User goal chart data",
            "success": True,
            "user_goal_bar_chart": goal_log_list,
            "user_goal_donut_chart": category_list,
        }
        # print("context", context)
        return Response(response, status=status.HTTP_200_OK)


class GetMentorMentees(APIView):
    def get(self, request, **kwargs):
        mentor_id = self.kwargs['mentor_id']
        try:
            mentor = User.objects.get(id=mentor_id)
        except User.DoesNotExist:
            return Response({"message": "Mentor does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        mentees = get_mentor_mentees(mentor)
        data = {
            "message": "Mentor mentees",
            "success": True,
            "mentees": mentees
        }
        return Response(data, status=status.HTTP_200_OK)


class MentorshipGoalsChart(APIView):
    def get(self, request, **kwargs):
        user_id = self.kwargs['user_id']
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        assign_users = AssignMentorToUser.objects.filter(user=user, mentor__company__in=[company])
        mentor_list = [assign_user.mentor for assign_user in assign_users]
        mentorship_goals = UserDrivenGoal.objects.filter(learners__in=[user], is_deleted=False, goal_type="Mentorship", created_by__in=mentor_list)

        response = {
            "message": "Mentorship goal chart data",
            "success": True,
            "mentorship_goal_category_chart": user_goal_donut_chart(mentorship_goals),
            "mentorship_goal_status_chart": mentorship_goal_status_chart(user, mentorship_goals),
            "mentorship_goal_progress_chart": mentorship_goal_progress_chart(user, mentorship_goals)
        }
        # print("context", context)
        return Response(response, status=status.HTTP_200_OK)

class UserActivityChart(APIView):
    def get(self, request, **kwargs):
        user_id = self.kwargs['user_id']
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        streakActivity = lineChartData(user)
        response = {
            "message": "User activity chart data",
            "success": True,
            "user_activity_chart": streakActivity
        }
        # print("context", context)
        return Response(response, status=status.HTTP_200_OK)

class UserLeaderBoard(APIView):
    def get(self, request, *args, **kwargs):
        user_type = self.request.query_params.get('user_type') or "Learner"
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        position = 1
        user_points=0
        if userpoints := UserEarnedPoints.objects.filter(user=user, user__userType__type="Learner").first():
            user_points = userpoints.total_points
        user_earned_points = UserEarnedPoints.objects.filter(total_points__gt=user_points).count()

        points = UserEarnedPoints.objects.filter().order_by('-total_points')[:10]
        table_list = []
        for point in points:
            table_list.append({
                "profile_image": avatar(point.user),
                "fullname": f"{point.user.first_name} {point.user.last_name}",
                "total_points": point.total_points
            })
        user_data = {
            "profile_image": avatar(user),
            "user_name": f"{user.first_name} {user.last_name}",
            "total_points": user_points,
            "position": position+user_earned_points
        }
        response = {
            "message": "leaderboard data",
            "success": True,
            "user_data": user_data,
            "data": table_list
        }
        return Response(response, status=status.HTTP_200_OK)


class UserAllCertificates(APIView):
    def get(self, request, user_id):
        data = {"user_id": str(user_id)}
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            if not self.request.query_params.get('user_type'):
                return Response({"message": "user_type is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user_type = UserTypes.objects.get(type=self.request.query_params.get('user_type'))
                user = User.objects.get(pk=user_id, userType=user_type)
            except User.DoesNotExist:
                return Response({"message": "User with this user_type does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

            company_id = ""
            if user_type.type != 'Admin':
                if not self.request.query_params.get('company_id'):
                    return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    company = Company.objects.get(id=self.request.query_params.get('company_id'))
                    company_id = company.id
                except Company.DoesNotExist:
                    return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

            user_certificates = UserCertificate.objects.filter(user=user, company=company, is_active=True, is_delete=False)
            certificate_list = []
            for certificate in user_certificates:
                certificate_list.append({
                    "id": certificate.id,
                    "title": certificate.certificate_template.title,
                    "certificate_for": certificate.certificate_template.Certificate_for,
                    "journey_id": certificate.journey.id,
                    "journey_title": certificate.journey.title,
                    "company_id": certificate.company.id,
                    "company_title": certificate.company.name,
                    "certificate_file": certificate_file(certificate),
                    "created_at": certificate.created_at,
                    "updated_at": certificate.updated_at
                })

            response = {
                "message": "User Certificates List",
                "success": True,
                "data": certificate_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class MailCertificate(APIView):
    def get(self, request, user_id, certificate_id):
        data = {"user_id": str(user_id)}
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            try:
                user_certificate = UserCertificate.objects.get(pk=certificate_id)
            except UserCertificate.DoesNotExist:
                return Response({"message": "User certificate does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

            program_team = CertificateSignature.objects.filter(certificate_template=user_certificate.certificate_template).first()
            result = send_user_certificate_mail(user_certificate.user, user_certificate.file, user_certificate.journey.title, user_certificate.company.name, program_team.name, program_team.headline)
            if result:
                message = "Mail Sent Successfully!"
            else:
                message = "Something Went Wrong!"
            response = {
                "message": message,
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)