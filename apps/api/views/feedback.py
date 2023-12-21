from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from rest_framework.authentication import TokenAuthentication
from apps.content.utils import company_journeys
from apps.feedback.models import FeedbackTemplate, JourneyFeedback, UserFeedback, FeedbackTemplateQuerstion, feedbackAnswer
from ..serializers import FeedbackResponseSerializer, FeedbackTemplateSerializer
from apps.api.utils import check_valid_user, update_boolean
from apps.content.models import Channel, UserChannel
from apps.users.models import Company, User
from apps.mentor.models import PoolMentor
from apps.atpace_community.utils import cover_images
from apps.users.utils import local_time
from apps.feedback.utils import feedbackTemplateData


class CreateFeedbackTemplate(APIView):
    model = FeedbackTemplate
    serializer_class = FeedbackTemplateSerializer
    
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_type = self.request.query_params.get('user_type') or None
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if user.userType.filter(type=user_type).exists():
            return Response({"message": "Invalid User Type", "success": False}, status=status.HTTP_404_NOT_FOUND)

        journey_list = company_journeys(user_type, user, company_id=company.id)
        journey_feedback_list = JourneyFeedback.objects.filter(journey__in=journey_list)
        feedback_template_list = [feedback_template.feedback_template for feedback_template in journey_feedback_list]
        template_data = []
        for template in feedback_template_list:
            journey_feedback = template.journey_feedback_template.first()
            template_data.append({
                "id": template.id,
                "name": template.name,
                "template_for": template.template_for,
                "cover_image": cover_images(template),
                "short_description": template.short_description,
                "is_active": template.is_active,
                "created_by": f"{template.created_by.first_name} {template.created_by.last_name}",
                "created_at": local_time(template.created_at),
                "company": journey_feedback.company.name,
                "journey": journey_feedback.journey.title,
            })
        
        response = {
            "message": "All template list",
            "success": True,
            "data": template_data
        }
        return Response(response, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_type = self.request.query_params.get('user_type') or None
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            if user.userType.filter(type=user_type).exists():
                return Response({"message": "Invalid User Type", "success": False}, status=status.HTTP_404_NOT_FOUND)
            name = request.data['name']
            short_description = request.data['short_description']
            template_for = request.data['template_for']
            cover_image = request.data['cover_image']
            is_draft = update_boolean(request.data['is_draft'])
            is_active = update_boolean(request.data['is_active'])
            template = self.model.objects.create(name=name, short_description=short_description, cover_image=cover_image,
                                      template_for=template_for, is_active=is_active, is_draft=is_draft, created_by=user)
            if data.get('journey') and data.get('journey') != "":
                journey_id = request.data['journey']
                try:
                    journey = Channel.objects.get(id=journey_id)
                except Channel.DoesNotExist:
                    return Response({"message": "Invalid journey", "success": False}, status=status.HTTP_404_NOT_FOUND)
                JourneyFeedback.objects.create(feedback_template=template, journey=journey, created_by=user)
            response = {
                "message": "Feedback template created",
                "success": True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class FeedbackResponseList(APIView):
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_type = self.request.query_params.get('user_type') or None
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if not user.userType.filter(type=user_type).exists():
            return Response({"message": "Invalid User Type", "success": False}, status=status.HTTP_404_NOT_FOUND)
        journey_list = company_journeys(user_type, user, company_id=company.id)
        user_channels = UserChannel.objects.filter(Channel__in=journey_list, user__userType__type__in=["Learner", "Mentor"], status="Joined", is_removed=False)
        mentor_pools = PoolMentor.objects.filter(pool__journey__in=journey_list, pool__is_active=True)
        user_list = [user_channel.user for user_channel in user_channels]
        mentor_list = [mentor_pool.mentor for mentor_pool in mentor_pools]
        user_list.extend(mentor_list)
        user_feedback = UserFeedback.objects.filter(user__in=user_list, is_private=False, is_active=True, is_delete=False, feedback_template__is_active=True, feedback_template__is_delete=False)
        user_feedback_data = [{
            "id": feedback.id,
            "template_id": feedback.feedback_template.id,
            "template_name": feedback.feedback_template.name,
            "template_for": feedback.feedback_template.template_for,
            "user_name": f"{feedback.user.first_name} {feedback.user.last_name}",
            "is_private": feedback.is_private,
            "created_at": local_time(feedback.created_at),
            # "feedback_for_user": f"{feedback.feedback_for_user.first_name} {feedback.feedback_for_user.last_name}" if feedback.feedback_for_user else "",
            "template_for_id": feedback.template_for_id,
            "is_name_private": feedback.is_name_private,
            "user_id": feedback.user.id,
            "company": feedback.journey_feedback.company.name if feedback.journey_feedback else "",
            "journey": feedback.journey_feedback.journey.title if feedback.journey_feedback else ""
        } for feedback in user_feedback]
        response = {
            "message": "All User Feedback Data list",
            "success": True,
            "data": user_feedback_data
        }
        return Response(response, status=status.HTTP_200_OK)


class FeedbackFormAPI(APIView):
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('feedback_for'):
            return Response({"message": "feedback_for is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)

        if not self.request.query_params.get('feedback_for_id'):
            return Response({"message": "feedback_for_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        print("feedback data 146",self.request.query_params.get('feedback_for'), self.request.query_params.get('feedback_for_id') )
        # try:
        template_data = feedbackTemplateData(self.request.query_params.get('feedback_for_id'), self.request.query_params.get('feedback_for'))
        # except:
            # return Response({"message": "Invalid feedback_for or feedback_for_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
        template_for = template_data['template_for']
        template_for_id = template_data['template_for_id']
        call_company = template_data['company']
        call_journey = template_data['journey']
        print("template data", template_data)
        journey_feedback = JourneyFeedback.objects.filter(type=template_for, company=call_company, is_active=True, is_delete=False)
        print("journey template1", journey_feedback)
        
        if template_for != 'GroupCall' and template_for != 'OneToOne':
            journey_feedback = journey_feedback.filter(journey=call_journey).first()
        else:
            journey_feedback = journey_feedback.first()

        print("journey template2", journey_feedback)
        
        if not journey_feedback:
            return Response({"message": "No feedback for this "+template_for, "success": True}, status=status.HTTP_200_OK)

        template = journey_feedback.feedback_template
        
        questions = FeedbackTemplateQuerstion.objects.filter(
            feedback_template=template, is_active=True, is_delete=False).order_by("display_order")

        print("journey template question", questions)

        if not questions.count() > 0:
            return Response({"message": "No feedback for this "+template_for, "success": True}, status=status.HTTP_200_OK)
        question_list = []
        for question in questions:
            question_list.append({
                "id":str(question.id),
                "title": question.title,
                "type": question.type,
                "is_required": question.is_required,
                "option_list": question.option_list,
                "start_rating_scale": question.start_rating_scale,
                "end_rating_scale": question.end_rating_scale,
                "is_multichoice": question.is_multichoice,
                "is_active": question.is_active,
                "created_at":question.created_at,
                "is_draft": question.is_draft,
                "display_order": question.display_order
            })

        response = {
            "message": "Feedback Form Questions",
            "success": True,
            "question_list": question_list,
            "template_for":template_for,
            "template_for_id":str(template_for_id),
            "company":call_journey,
            "template_id":str(template.id)
        }
        return Response(response, status=status.HTTP_200_OK)
    
class SubmitFeedbackForm(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = FeedbackResponseSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            feedback_id = request.data['feedback_id']
            feedback_for_id = request.data['feedback_for_id']
            feedback_for = request.data['feedback_for']
            is_private = update_boolean(request.data['is_private'])
            is_name_private = update_boolean(request.data['is_name_private'])
            questions = request.data['questions']
            print(questions)
            template_data = feedbackTemplateData(feedback_for_id, feedback_for)
            try:
                user = User.objects.get(pk=request.data["user_id"])
                print(user)
            except User.DoesNotExist:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            try:
                feedback = FeedbackTemplate.objects.get(pk=feedback_id)
            except FeedbackTemplate.DoesNotExist:
                return Response({"message": "Enter Valid Feedback Id", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            feedback_attempt = UserFeedback.objects.create(user=user, feedback_template=feedback, is_private=is_private, is_name_private=is_name_private, template_for=template_data['template_for'], template_for_id=template_data['template_for_id'])

            for i in questions:

                question_instance = FeedbackTemplateQuerstion.objects.get(pk=i['q_id'])
                if question_instance.type == 'Checkbox':
                    res = i["response"].split(",")
                    for j in res:
                        feedbackAnswer.objects.create(user=user, question=question_instance, journey_template=feedback,
                                                  user_feedback=feedback_attempt, answer=res)
                else:
                    feedbackAnswer.objects.create(user=user, question=question_instance, journey_template=feedback,
                                              user_feedback=feedback_attempt, answer=i['response'])

            response = {
                "success": True,
                "message": "Submit Successfully",
                "data": {
                    "feedback_attempt_id": feedback_attempt.pk
                }
            }
            return Response({"message": "Submit", "data": response, "success": True}, status=200)

        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)