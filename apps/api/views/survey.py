# from werkzeug.utils import secure_filename
import os
from apps.api.serializers import JourneySurveuResponseSerializer, SurveySerializer, UploadFileSerializer
from apps.api.utils import survey_file, survey_upload, survey_upload_file
from apps.atpace_community.utils import cover_images, ques_image
from apps.users.models import User
from apps.survey_questions.models import Survey, Question, Options, SurveyAttempt, UserAnswer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from apps.content.models import Channel, SurveyAttemptChannel
from rest_framework.decorators import api_view
import ast

from ravinsight.settings import AWS_STORAGE_BUCKET_NAME, BASE_DIR, DEFAULT_FILE_STORAGE, MEDIA_URL


class JourneySurvey(APIView):
    def post(self, request):
        data = request.data
        serializer = SurveySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            assessment_id = data['survey_id']
            journey_type = data["journey_type"]
            if journey_type == "MentoringJourney":
                try:
                    test_series = Survey.objects.get(pk=assessment_id)
                except Survey.DoesNotExist:
                    return Response({"message": "Survey does not exist"}, status=status.HTTP_400_BAD_REQUEST)
                print("test_series", test_series)
                test_question = Question.objects.filter(survey=test_series)
                data = []
                for test_question in test_question:
                    rating_scale = ""
                    print("test_question", test_question)
                    test_options = Options.objects.filter(question=test_question)
                    print("test_options", test_options)
                    options_list = []
                    if test_question.type == "MultiChoiceGrid":
                        options_list.append({"grid_row": test_question.grid_row})
                        options_list.append({"grid_coloum": test_question.grid_coloum})
                    elif test_question.type == "CheckboxGrid":
                        options_list.append({"grid_row": test_question.grid_row})
                        options_list.append({"grid_coloum": test_question.grid_coloum})
                    elif test_question.type == "LinearScale":
                        rating_scale = {
                            "end_rating_scale": test_question.end_rating_scale,
                            "start_rating_scale": test_question.start_rating_scale,
                            "end_rating_name": test_question.end_rating_name,
                            "start_rating_name": test_question.start_rating_name
                        }
                        options_list.append(f"{test_question.start_rating_scale}- {test_question.end_rating_scale}")
                    else:
                        options_list = None
                    data.append({
                        "id": test_question.id,
                        "title": test_question.title,
                        "type": test_question.type,
                        "options":  test_question.option_list if test_question.option_list else options_list,
                        "is_required": test_question.is_required,
                        "display_order": test_question.display_order,
                        "image": ques_image(test_question),
                        "rating_scale": rating_scale
                    })
                response = {
                    "message": "Get data",
                    "success": True,
                    "data": {
                        "id": test_series.id,
                        "survey": test_series.name,
                        "image": cover_images(test_series),
                        "description": test_series.short_description,
                        "question": data
                    }
                }
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid Journey type", "success": False}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class SubmitSurvey(APIView):
    def post(self, request):
        data = request.data
        print(data)
        serializer = JourneySurveuResponseSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # try:
            survey_id = request.data['survey_id']
            journey = request.data["journey_id"]
            questions = request.data['questions']
            print(questions)
            try:
                user = User.objects.get(pk=request.data["user_id"])
                print(user)
            except User.DoesNotExist:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            try:
                survey = Survey.objects.get(pk=survey_id)
            except Survey.DoesNotExist:
                return Response({"message": "Enter Valid Assessment Id", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            try:
                channel = Channel.objects.get(pk=journey)
            except Channel.DoesNotExist:
                return Response({"message": "Enter Valid Journey Id", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            survey_attempt = SurveyAttempt.objects.create(user=user, survey=survey)
            SurveyAttemptChannel.objects.create(survey_attempt=survey_attempt, channel=channel, user=user)
            if not isinstance(questions, list):
                questions = ast.literal_eval(questions)
            print("question", questions)
            for i in questions:
                print("resonse", i)
                question_instance = Question.objects.get(pk=i['q_id'])
                if question_instance.type == "FileUpload":
                    print("ip ", i['response'])
                    name, file_upload = survey_upload_file(i['response'])
                    print(f"name {name} upload {file_upload}")
                    user_answer = UserAnswer.objects.create(user=user, question=question_instance,
                                                            survey_attempt=survey_attempt)
                    user_answer.upload_file.save(name, file_upload)
                elif question_instance.type == 'Checkbox':
                    res = i["response"].split(",")
                    for j in res:
                        UserAnswer.objects.create(user=user, question=question_instance,
                                                  survey_attempt=survey_attempt, response=res)
                elif question_instance.type == "MultiChoiceGrid":
                    res = i['response']
                    resp = list(res.values())
                    question_answer_radio = [[f"{resp[x]}/{question_instance.grid_row[x]}"]
                                             for x in range(len(question_instance.grid_row))]
                    print(question_answer_radio)
                    UserAnswer.objects.create(user=user, question=question_instance,
                                              survey_attempt=survey_attempt, response=question_answer_radio)
                elif question_instance.type == "CheckboxGrid":
                    res = i['response']
                    resp = list(res.values())
                    question_answer = []
                    for x in range(len(question_instance.grid_row)):
                        question_answer.append([f"{y}/{question_instance.grid_row[x]}" for y in resp[x]])
                    print("checkbox ", question_answer)
                    UserAnswer.objects.create(user=user, question=question_instance,
                                              survey_attempt=survey_attempt, response=question_answer)
                else:
                    UserAnswer.objects.create(user=user, question=question_instance,
                                              survey_attempt=survey_attempt, response=i['response'])

            response = {
                "success": True,
                "message": "Submit Successfully",
                "data": {
                    "survey_attempt_id": survey_attempt.pk
                }
            }
            return Response({"message": "Submit", "data": response, "success": True}, status=200)

        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class SurveyAnswer(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"Message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        survey_attempt = SurveyAttempt.objects.filter(pk=self.kwargs['attempt_id'], user=user).first()
        user_answer = UserAnswer.objects.filter(survey_attempt=survey_attempt)
        print(survey_attempt)
        if survey_attempt is None:
            return Response({"Message": "User attempt not found"}, status=status.HTTP_400_BAD_REQUEST)
        details_list = []
        for attempt in user_answer:
            print("1", attempt)
            details_list.append({
                "attemp_id": attempt.survey_attempt.pk,
                "question": attempt.question.title,
                "answer": attempt.response if attempt.response else survey_file(attempt),
            })
        return Response({"message": "get answers", "response": details_list, "Success": True}, status=status.HTTP_200_OK)
