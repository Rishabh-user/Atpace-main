from datetime import datetime
from apps.content.models import Channel, Content, ContentChannels, ContentData, UserActivityData, UserChannel
from apps.mentor.models import AssignMentorToUser
from rest_framework.views import APIView
from apps.api.serializers import UserIdSerializer
from rest_framework.response import Response
from rest_framework import status
from apps.users.models import User, Company, UserTypes
from apps.content.utils import company_journeys
from apps.atpace_community.utils import activityFile
from apps.users.templatetags.tags import get_mentor_mentees
from apps.api.utils import get_journey_content


class AllActivity(APIView):
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

            if not self.request.query_params.get('content_type'):
                return Response({"message": "content_type is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            company_id = ""
            if user_type.type != 'Admin':
                if not self.request.query_params.get('company_id'):
                    return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    company = Company.objects.get(id=self.request.query_params.get('company_id'))
                    company_id = company.id
                except Company.DoesNotExist:
                    return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

            companyJourneys = company_journeys(user_type.type, user, company_id)
            #print("companyJourneys", companyJourneys)
            if user_type.type == 'Learner':
                user_channel = UserChannel.objects.filter(user=user, is_removed=False, Channel__in=companyJourneys)
                #print("line 32", user_channel)
                journeys = [channel.Channel for channel in user_channel]

            elif user_type.type == 'Mentor':
                assign_mentor_to_user = AssignMentorToUser.objects.filter(mentor=user, journey__in=companyJourneys)
                #print("assign_mentor_to_user", assign_mentor_to_user)
                journeys = [channel.journey for channel in assign_mentor_to_user]
                #print("journey", journeys)

            else:
                journeys = companyJourneys

            channel_content = ContentChannels.objects.filter(Channel__in=journeys)
            #print("channel_content", channel_content)
            content = [content.content for content in channel_content]
            # content = Content.objects.filter(Channel__in=journeys, is_delete=False)
            #print("content", content)
            content_data = ContentData.objects.filter(
                content__in=content, type=self.request.query_params.get('content_type'))
            #print("contrntdata", content_data)
            activity_list = []
            for data in content_data:
                is_completed = ""
                activity_file = ""
                learners_completed = ""
                if user_type.type == 'Learner':
                    is_completed = UserActivityData.objects.filter(
                        content_data=data, submitted_by=user, is_active=True, is_delete=False, is_draft=False).exists()
                    if is_completed:
                        user_activity_data = UserActivityData.objects.filter(
                            content_data=data, submitted_by=user, is_active=True, is_delete=False, is_draft=False).first()
                        activity_file = activityFile(user_activity_data)

                elif user_type.type == 'Mentor':
                    #print("line 55")
                    mentees = get_mentor_mentees(user, company.id)
                    mentees_list = [mentee.user for mentee in mentees]
                    #print("mentees", mentees)
                    learners_completed = UserActivityData.objects.filter(
                        content_data=data, submitted_by__in=mentees_list, is_active=True, is_delete=False, is_draft=False).count()

                elif user_type.type == "ProgramManager":
                    learners_completed = UserActivityData.objects.filter(
                        content_data=data, journey__in=journeys, is_active=True, is_delete=False, is_draft=False).count()

                else:
                    learners_completed = UserActivityData.objects.filter(
                        content_data=data, is_active=True, is_delete=False, is_draft=False).count()
                try:
                    journey_id = data.content__Channel.id
                    journey_title = data.content__Channel.title
                except:
                    journey_id = ""
                    journey_title = ""
                activity_list.append({
                    "id": data.id,
                    "title": data.title,
                    "content_id": data.content.id if data.content else "",
                    "content_title": data.content.title if data.content else "",
                    "type": data.type,
                    "activity_type": data.activity_type,
                    "description": data.data,
                    "display_order": data.display_order,
                    "time": data.time,
                    "submit_duration": data.submit_duration,
                    "journey_id": journey_id,
                    "journey_title": journey_title,
                    "is_completed": is_completed,
                    "activity_file": activity_file,
                    "learners_completed": learners_completed
                })

            response = {
                "message": "All Activity List",
                "success": True,
                "data": activity_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class ActivityUser(APIView):
    def get(self, request, user_id, activity_id):
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

            if user_type.type != 'Admin':
                if not self.request.query_params.get('company_id'):
                    return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    company = Company.objects.get(id=self.request.query_params.get('company_id'))
                except Company.DoesNotExist:
                    return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

            try:
                content_data = ContentData.objects.get(id=activity_id)
            except ContentData.DoesNotExist:
                return Response({"message": "Activity does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

            if user_type.type == 'Mentor':
                mentees = get_mentor_mentees(user, company.id)
                mentees_list = [mentee.user for mentee in mentees]
                #print("mentees", mentees)
                user_activity = UserActivityData.objects.filter(
                    content_data=content_data, submitted_by__in=mentees_list, is_active=True, is_delete=False, is_draft=False)

            elif user_type.type == 'ProgramManager':
                journeys = company_journeys(user_type.type, user, company.id)
                user_activity = UserActivityData.objects.filter(
                    content_data=content_data, journey__in=journeys, is_active=True, is_delete=False, is_draft=False)

            elif user_type.type == 'Admin':
                user_activity = UserActivityData.objects.filter(
                    content_data=content_data, is_active=True, is_delete=False, is_draft=False)

            #print("contrntdata 125", content_data, user_activity)
            activity_list = []
            for data in user_activity:
                activity_list.append({
                    "id": data.id,
                    "title": data.content_data.title,
                    "journey_id": data.journey.id,
                    "journey_title": data.journey.title,
                    "is_review": data.is_review,
                    "upload_file": activityFile(data),
                    "submitted_by": data.submitted_by.first_name + " " + data.submitted_by.last_name,
                    "reviewed_by": data.reviewed_by.first_name + " " + data.reviewed_by.last_name,
                })

            response = {
                "message": "Activity User List",
                "success": True,
                "data": activity_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)
