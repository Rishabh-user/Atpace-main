from apps.mentor.models import mentorCalendar
from apps.users.utils import meeting
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.users.models import Company, UserTypes, User
from apps.feedback.models import UserFeedback


class FeedbackList(APIView):
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('company_id'):
            return Response({"message": "Company Id is Required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "Company Id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        type = UserTypes.objects.get(type=self.kwargs['type'])
        try:
            user = User.objects.get(id=self.kwargs['user_id'], userType=type)
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = []
        user_feedback = UserFeedback.objects.filter(feedback_for_user=user, is_private=False, journey_feedback__company=company)
        for feedback in user_feedback:
            feedback_for_obj = mentorCalendar.objects.filter(id=feedback.template_for_id).first()
            data.append({
                "id": feedback.id,
                "template_id": feedback.feedback_template.id,
                "template_name": feedback.feedback_template.name,
                "feedback_from_id": feedback.user.id,
                "feedback_for_type": feedback.feedback_template.template_for,
                "feedback_from_name": feedback.user.first_name + " " + feedback.user.last_name,
                "is_private": feedback.is_private,
                "is_name_private": feedback.is_name_private,
                "journey": feedback.journey_feedback.journey.title,
                "feedback_for": feedback_for_obj.title if feedback_for_obj else None,
                "feedback_for_id": feedback_for_obj.id if feedback_for_obj else None,
            })
        # # # print("data",data)
        response = {
            "success": True,
            "data": "Feedback data",
            "feedback_list": data
        }
        # # # print("response",response)
        return Response(response, status=status.HTTP_200_OK)
