from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .Models.Learner import NoActivityMenteeData, NoActivityMentorData, NoActivityPairData


class RiskPairs(APIView):

    def get(self, request, *args, **kwargs):
        company_id = self.request.query_params.get("company_id")
        if not company_id:
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        pair_data = NoActivityPairData.objects.filter(company__id=company_id)
        pair_data_list = [{
            "company_id": pair.company.pk,
            "company_name": pair.company.name,
            "journey_id": pair.pair.journey.pk,
            "journey_name": pair.pair.journey.title,
            "mentor_id": pair.mentor.id if pair.mentor else "",
            "mentor_name": pair.pair.mentor.get_full_name(),
            "mentee_id": pair.pair.user.id if pair.pair.user else "",
            "mentee_name": pair.pair.user.get_full_name(),
        }
            for pair in pair_data]
        
        response = {
            "message": "Get Risk Pairs",
            "data": pair_data_list,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class RiskMentors(APIView):

    def get(self, request, *args, **kwargs):
        company_id = self.request.query_params.get("company_id")
        if not company_id:
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        mentor_data = NoActivityMentorData.objects.filter(company__id=company_id)
        mentor_data_list = [{
            "company_id": mentor.company.pk,
            "company_name": mentor.company.name,
            "user_name": mentor.user_name,
            "mentor_id": mentor.user.id,
            "mentor_name": mentor.user.get_full_name(),
            "no_calls": mentor.no_calls,
            "no_quest": mentor.no_quest,
            "no_journals": mentor.no_journals,
            "all_post": mentor.all_post
        }
            for mentor in mentor_data]
        
        response = {
            "message": "Get Risk Mentor",
            "data": mentor_data_list,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class RiskMentees(APIView):

    def get(self, request, *args, **kwargs):
        company_id = self.request.query_params.get("company_id")
        if not company_id:
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        mentee_data = NoActivityMenteeData.objects.filter(company__id=company_id)
        mentee_data_list = [{
            "company_id": mentee.company.pk,
            "company_name": mentee.company.name,
            "user_name": mentee.user_name,
            "mentee_id": mentee.user.id,
            "mentee_name": mentee.user.get_full_name(),
            "no_calls": mentee.no_calls,
            "no_quest": mentee.no_quest,
            "no_journals": mentee.no_journals,
            "all_post": mentee.all_post
        }
            for mentee in mentee_data]
        
        response = {
            "message": "Get Risk Mentees",
            "data": mentee_data_list,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)