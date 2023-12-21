import ast
import csv
import  pandas as pd
import json
from ntpath import join
from django.contrib.auth.decorators import login_required
# from oauth2_provider.models import AccessToken, Application, RefreshToken
from django.http import HttpResponse
from apps.content.serializers import JourneySerializer
from apps.survey_questions.models import Question, Survey, SurveyAttempt, UserAnswer
from apps.content.models import Channel, ChannelGroup, ChannelGroupContent, Content, ContentData, TestAttempt, \
    UserChannel, UserCourseStart, MatchQuesConfig, MatchQuestion, \
    UserTestAnswer, MentoringJourney
from rest_framework import viewsets
from rest_framework.response import Response
from apps.survey_questions.serializer import SurveySerializer
from apps.test_series.models import TestOptions, TestQuestion, TestSeries
from apps.test_series.serializers import AssessmentSerializer
from apps.webapi.utils import Assessment_attempt_list, survey_attempt_list
from .serializers import UserSerializer
from apps.users.models import Learner, User, UserCompany, UserTypes, Coupon, Company, UserProfileAssest, ProfileAssestQuestion
from apps.users.utils import AlloteChannel
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from django.views.generic.base import View

# Create your views here.
from ..mentor.models import AssignMentorToUser, PoolMentor


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class AssessmentAttemptViewSet(APIView):
    def get(self, request, **kwargs):
        queryset = TestAttempt.objects.all()
        res = []
        if request.GET.get('id'):
            queryset = queryset.filter(pk=request.GET['id'])
        for queryset in queryset:
            res.append({
                'user_skill': queryset.user_skill.label if queryset.user_skill else None,
                'assessment_marks': queryset.test_marks,
                'user_marks': queryset.total_marks,
                'journey': queryset.channel.title,
                'journey_id': queryset.channel.pk,
                'is_check': queryset.is_check,
                'assessment': queryset.test.name,
                'assessment_id': queryset.test.pk,
                'username': queryset.user.username,
                'user_id': queryset.user.pk
            })

        return Response(res)


class AllAssessment(APIView):
    def get(self, request, **kwargs):
        queryset = TestSeries.objects.all()
        res = []
        for queryset in queryset:
            test_questions = TestQuestion.objects.filter(survey=queryset.pk)
            res.append({
                "id": queryset.pk,
                "name": queryset.name,
                "created_at": queryset.created_at,
                "auto_check": queryset.auto_check,
                "question": AssessmentSerializer(test_questions, many=True).data,
            })
        return Response(res)


class AllSurvey(APIView):
    def get(self, request, **kwargs):
        queryset = Survey.objects.all()
        res = []
        for queryset in queryset:
            test_questions = Question.objects.filter(survey=queryset.pk)
            res.append({
                "id": queryset.pk,
                "name": queryset.name,
                "created_at": queryset.created_at,
                "auto_check": queryset.auto_check,
                "question": SurveySerializer(test_questions, many=True).data,
            })
        return Response(res)


class SurveyAttemptViewSet(APIView):
    def get(self, request, **kwargs):

        queryset = SurveyAttempt.objects.all()
        if request.GET.get('id'):
            queryset = queryset.filter(pk=request.GET['id'])
        res = []
        for queryset in queryset:
            res.append({
                'user_skill': queryset.user_skill.label if queryset.user_skill else None,
                'journey': queryset.channel.title,
                'journey_id': queryset.channel.pk,
                'is_check': queryset.is_check,
                'survey': queryset.survey.name,
                'survey_id': queryset.survey.pk,
                'username': queryset.user.username,
                'user_id': queryset.user.pk
            })

        return Response(res)


class UserJourneyViewSet(APIView):
    def get(self, request, *args, **kwargs):
        queryset = UserChannel.objects.all()
        if request.GET.get('status'):
            queryset = queryset.filter(status=request.GET['status'])

        res = []

        for queryset in queryset:
            data = JourneySerializer(Channel.objects.get(pk=queryset.Channel.pk))

            res.append({
                'username': queryset.user.username,
                'user_id': queryset.user.pk,
                'journey': data.data,
                'status': queryset.status
            })
        return Response(res)


class AllJourney(APIView):
    def get(self, request, *args, **kwargs):
        queryset = Channel.objects.filter(parent_id=None)
        if request.GET.get('status'):
            queryset = queryset.filter(pk=request.GET['id'])
        res = []
        # data = JourneySerializer(queryset, many=True)
        for queryset in queryset:
            journey = JourneySerializer(queryset, many=False).data

            skill = JourneySerializer(Channel.objects.filter(parent_id=queryset.pk), many=True).data

            res.append({
                'details': journey,
                'skill': skill

            })

        return Response({'journey': res})


class OrderContent(APIView):
    def get(self, request):
        all_content = Content.objects.all()

        for content in all_content:
            i = 1
            content_data = ContentData.objects.filter(content=content).order_by("display_order")
            for content_data in content_data:
                content_data.display_order = i
                content_data.save()
                i += 1
            print("#########")
        res = {
            "message": "success"
        }
        return Response(res)


# class OrderGroupContent(APIView):
#     def get(self, request):
#         all_group = ChannelGroup.objects.all()
#         for group in all_group:
#             i = 1
#             group_content = ChannelGroupContent.objects.filter(channel_group=group).order_by('display_order')
#             for group_content in group_content:
#                 print(group_content)
#                 group_content.display_order = i
#                 group_content.save()
#                 i += 1
#             print("####")
#         res = {
#             "message": "Success"
#         }
#         return Response(res)


# class Checkgroup(APIView):
#     def get(self, request):
#         all_group = ChannelGroup.objects.all().order_by('-created_at')
#         for group in all_group:
#             print(group.title)
#             try:
#                 print(group.title)
#                 level = SurveyLabel.objects.get(label=group.title)
#                 group.channel_for = level
#                 group.save()
#             except:
#                 pass

#         res = {
#             "message": "Success"
#         }
#         return Response(res)

@permission_classes((AllowAny,))
class JourneyPathway(APIView):
    def get(self, request, *args, **kwargs):
        user = Learner.objects.all()

        if self.kwargs.get('username'):
            user = user.filter(username=self.kwargs['username'])
        context = []
        for user in user:
            userchannels = UserChannel.objects.filter(user=user)
            user_channel_list = [userchannels.Channel.pk for userchannels in userchannels]
            get_channel = Channel.objects.filter(pk__in=user_channel_list)
            Channel_list = []
            for get_channel in get_channel:

                course_start = []

                # channel_group = ChannelGroup.objects.filter(channel=get_channel)

                get_skill_channel = Channel.objects.filter(parent_id=get_channel)
                if get_channel.channel_type == "SkillDevelopment":

                    skill_list = []
                    for get_skill_channel in get_skill_channel:

                        skill_channel_group = ChannelGroup.objects.filter(channel=get_skill_channel, is_delete=False)
                        skill_channel_group_list = []
                        for skill_channel_group in skill_channel_group:

                            course_content = ChannelGroupContent.objects.filter(channel_group=skill_channel_group, is_delete=False)
                            course_content_list = []
                            for course_content in course_content:

                                try:
                                    read_status = UserCourseStart.objects.filter(
                                        content=course_content.content, channel_group=skill_channel_group,
                                        channel=get_skill_channel).first()

                                    read_status = read_status.status
                                except Exception as e:

                                    read_status = "Not Start"
                                course_content_list.append({
                                    "content": course_content.content.title,
                                    "status": course_content.status,
                                    "read_status": read_status
                                })
                            skill_channel_group_list.append({
                                "proficiency_level": skill_channel_group.title,
                                "post_assessment": skill_channel_group.post_assessment.name if skill_channel_group.post_assessment else None,
                                "microskill": course_content_list
                            })
                        skill_list.append({
                            "name": get_skill_channel.title,
                            "pre_assessment": get_channel.test_series.name if get_channel.test_series else None,
                            "proficiency": skill_channel_group_list
                        })
                else:
                    skill_list = []
                    skill_channel_group = ChannelGroup.objects.filter(channel=get_channel, is_delete=False)
                    skill_channel_group_list = []
                    for skill_channel_group in skill_channel_group:

                        course_content = ChannelGroupContent.objects.filter(channel_group=skill_channel_group, is_delete=False)
                        course_content_list = []
                        for course_content in course_content:

                            try:
                                read_status = UserCourseStart.objects.filter(
                                    content=course_content.content, channel_group=skill_channel_group,
                                    channel=get_channel).first()

                                read_status = read_status.status
                            except Exception as e:
                                print(e)
                                read_status = "Not Start"
                            course_content_list.append({
                                "content": course_content.content.title,
                                "status": course_content.status,
                                "read_status": read_status
                            })
                        skill_channel_group_list.append({
                            "proficiency_level": skill_channel_group.title,
                            "post_assessment": skill_channel_group.post_assessment.name if skill_channel_group.post_assessment else None,
                            "microskill": course_content_list
                        })

                    skill_list.append({
                        "id": None,
                        "name": None,
                        "pre_assessment": None,
                        "proficiency": skill_channel_group_list
                    })

                Channel_list.append({
                    "id": get_channel.pk,
                    "name": get_channel.title,
                    "pre_assessment": get_channel.test_series.name if get_channel.test_series else None,
                    "channel_type": get_channel.channel_type,
                    "skill": skill_list
                })

            context.append({
                "user": user.pk,
                "username": user.username,
                "journeys": Channel_list
            })
        return Response(context)


# "course_start": course_start,
#             "test_attempt": test_attempt,
#             "survey_attempt": survey_attempt,
#             "group_content": group_content


class APITest(APIView):
    def get(self, request):
        user_course_start = UserCourseStart.objects.all()
        for user_course_start in user_course_start:
            if user_course_start.channel.channel_type == "SkillDevelopment":
                channel_group = ChannelGroup.objects.filter(channel=user_course_start.channel, is_delete=False)
                for channel_group in channel_group:
                    print(user_course_start.channel, channel_group, user_course_start.content)
                    data = ChannelGroupContent.objects.filter(
                        content=user_course_start.content, channel_group=channel_group, is_delete=False)
                    user_course_start.channel_group = channel_group
                    user_course_start.save()
            else:
                channel_group = ChannelGroup.objects.get(channel=user_course_start.channel)
                data = ChannelGroupContent.objects.filter(
                    content=user_course_start.content, channel_group=channel_group, is_delete=False)
                user_course_start.channel_group = channel_group
                user_course_start.save()
                print(data)
        return Response("success")


class TestAssessmentMarks(APIView):
    def get(self, request):
        user_tests = UserTestAnswer.objects.all()
        for user_test in user_tests:
            user_test.question_marks = user_test.question.marks
            user_test.save()
        return Response("success")


# @permission_classes((AllowAny,))
# class TokenRefresh(APIView):
#     def post(self, request, format=None):
#         data = request.data
#         user_id = data['user_id']
#         client_id = data['client_id']
#         client_secret = data['client_secret']
#         token_obj = RefreshToken.objects.filter(user_id=user_id).order_by('-id')
#         refersh_token = ''
#         if token_obj:
#             token_obj = token_obj[0]
#             refersh_token = token_obj.token
#         url = 'http://'+request.get_host()+'/o/token/'
#         data_dict = {
#             'grant_type': 'refresh_token',
#             'client_id': client_id,
#             "client_secret": client_secret,
#             "refresh_token": refersh_token
#         }
#         aa = requests.post(url, data=data_dict)
#         print(aa)
#         data = json.loads(aa.text)
#         return Response(data, status=201)


@permission_classes((AllowAny,))
class userinfo(APIView):
    def get(self, request):
        data = {
            "user": {
                "email": "prashantk794@gmail.com",
                "name": "prashant",
                "avatar": "http://127.0.0.1:8000/static/dist/img/avatar.png",
                "id": "015c5dd1-5c1b-4e29-8554-534ad60996fc"
            }
        }
        return Response(data, status=200)


@permission_classes((AllowAny,))
class UserToLearner(APIView):
    def get(self, request):
        user_type = UserTypes.objects.get(type="ContentCreator")
        user_type_learner = UserTypes.objects.get(type="ProgramManager")
        all_users = User.objects.filter(userType=user_type)
        for user in all_users:
            user.userType.add(user_type_learner.id)
        # ContentData.objects.filter(type ="Link").update(type="YtVideo")
        return Response({"message": True})


# export journeys to csv file(download journey data)
@login_required
def ExportJourney(request, journey_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="JourneyData.csv"'

    Fields = (
        ['Title', 'Short Description', 'Category', 'Description', 'Type', 'Is Active', 'Company', 'Survey',
         'Test Series',
         'Content Title',
         'Content Description', 'Content Status', 'Created By', 'Time'])
    file = csv.DictWriter(response, fieldnames=Fields)
    channel = Channel.objects.all()
    if journey_type == 'MentoringJourney':
        channel = channel.filter(channel_type='MentoringJourney')
    datadict = []
    for channel in channel:
        content = Content.objects.filter(Channel=channel)
        datadict.extend(
            {'Title': channel.title, 'Short Description': channel.short_description, 'Category': channel.category,
             'Description': channel.description, 'Type': channel.channel_type, 'Is Active': channel.is_active,
             'Company': channel.company, 'Survey': channel.survey, 'Test Series': channel.test_series,
             'Content Title': content.title, 'Content Description': content.description,
             'Content Status': content.status, 'Created By': channel.created_by, 'Time': channel.created_at } for content in content)

        datadict.append({
            'Title': channel.title,
            'Short Description': channel.short_description,
            'Category': channel.category,
            'Description': channel.description,
            'Type': channel.channel_type,
            'Is Active': channel.is_active,
            'Company': channel.company,
            'Survey': channel.survey,
            'Test Series': channel.test_series,
            'Created By': channel.created_by,
            'Time': channel.created_at
        })
    file.writeheader()
    file.writerows(datadict)
    return response


@login_required
def AssessmentCSV(request, attempt_id):
    test_attempt = TestAttempt.objects.get(pk=attempt_id)
    response = HttpResponse(content_type='text/csv', headers={
        'Content-Disposition': f'attachment; filename="{test_attempt.test.name}-{test_attempt.user.username}.csv"'})

    Fields = (
        ['Attemp_ID', 'Test_Name', 'Question', 'Answer', 'Question_Marks', 'Given_Marks', 'Journey_Name',
         'Assessment_type', 'Time', 'User'])

    file = csv.DictWriter(response, fieldnames=Fields)
    details_list = []
    attempt = test_attempt.test_attempet_answer.all()
    for attempt in attempt:
        attempt_response = attempt.response
        if attempt.question.type == "Checkbox":
            ids = ast.literal_eval(attempt.response)
            print(ids)
            temp = TestOptions.objects.filter(pk__in=ids)
            responses = [temp.option for temp in temp]
            res1 = ''
            for res in responses:
                res1 = f"{res1}, {res}" if res1 != "" else f"{res1}{res}"
            attempt_response = res1
        details_list.append({"Attemp_ID": test_attempt.pk, "Test_Name": test_attempt.test.name, "Journey_Name": test_attempt.channel.title,
            "Question": attempt.question.title, "Answer": attempt_response, "Question_Marks": attempt.question_marks,
            "Given_Marks": attempt.total_marks, "Assessment_type": test_attempt.type, "User": test_attempt.user.username,
            "Time": test_attempt.created_at})

    file.writeheader()
    file.writerows(details_list)
    return response


@login_required
def matchAllAssessment(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="AllAssessmentData.csv"'},
    )
    Fields = (
        ['Attemp_ID', 'Test_Name', 'Question', 'Answer', 'Question_Marks', 'Given_Marks', 'Journey_Name',
         'Assessment_type',
         'User'])

    file = csv.DictWriter(response, fieldnames=Fields)

    assessment_id = request.POST['assessment_id']
    channel_id = request.POST['channel_id']
    user_id = request.POST['user_id']

    if assessment_id and channel_id and user_id:
        assessment = TestSeries.objects.get(id=assessment_id)
        channel = Channel.objects.get(id=channel_id)
        user = User.objects.get(pk=user_id)
        attempt_list = TestAttempt.objects.filter(channel=channel, user=user, test=assessment)
    elif assessment_id and channel_id == "" and user_id:
        assessment = TestSeries.objects.get(id=assessment_id)
        user = User.objects.get(pk=user_id)
        attempt_list = TestAttempt.objects.filter(user=user, test=assessment)
    elif assessment_id == "" and channel_id and user_id:
        channel = Channel.objects.get(id=channel_id)
        user = User.objects.get(pk=user_id)
        attempt_list = TestAttempt.objects.filter(user=user, channel=channel)
    elif assessment_id and channel_id and user_id == "":
        channel = Channel.objects.get(id=channel_id)
        assessment = TestSeries.objects.get(id=assessment_id)
        attempt_list = TestAttempt.objects.filter(channel=channel, test=assessment)
    elif assessment_id == "" and channel_id == "" and user_id:
        user = User.objects.get(pk=user_id)
        attempt_list = TestAttempt.objects.filter(user=user)
    elif assessment_id and channel_id == "" and user_id == "":
        assessment = TestSeries.objects.get(id=assessment_id)
        attempt_list = TestAttempt.objects.filter(test=assessment)
    elif assessment_id == "" and channel_id and user_id == "":
        channel = Channel.objects.get(id=channel_id)
        attempt_list = TestAttempt.objects.filter(channel=channel)
    else:
        attempt_list = TestAttempt.objects.all()
    data = Assessment_attempt_list(attempt_list)

    file.writeheader()
    file.writerows(data)
    return response


@login_required
def matchAllSurveys(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="AllSurveysData.csv"'},
    )
    Fields = (['Attemp_ID', 'Test_Name', 'Question', 'Answer', 'Upload_File', 'Journey_Name', 'User', "Time"])

    file = csv.DictWriter(response, fieldnames=Fields)

    survey_id = request.POST['survey_id']
    channel_id = request.POST['channel_id']
    user_id = request.POST['user_id']
    attempt_list = SurveyAttempt.objects.all()
    if survey_id and channel_id and user_id:
        print(1)
        survey = Survey.objects.get(id=survey_id)
        channel = Channel.objects.get(id=channel_id)

        if channel.channel_type == "MentoringJourney":
            surveys = surveys_list_by_journey(channel)
        else:
            surveys = [channel.survey] if channel.survey else []

            print(surveys)
        user = User.objects.get(pk=user_id)

        attempt_list = SurveyAttempt.objects.filter(user=user, survey__in=surveys)
        data = survey_attempt_list(attempt_list)

    elif survey_id == "" and channel_id and user_id:
        print(2)
        channel = Channel.objects.get(id=channel_id)

        if channel.channel_type == "MentoringJourney":
            surveys = surveys_list_by_journey(channel)
        else:
            surveys = [channel.survey] if channel.survey else []

        user = User.objects.get(pk=user_id)
        attempt_list = SurveyAttempt.objects.filter(user=user, survey__in=surveys)
        data = survey_attempt_list(attempt_list)

    elif survey_id and channel_id == "" and user_id:

        survey = TestSeries.objects.get(id=survey_id)
        user = User.objects.get(pk=user_id)
        attempt_list = SurveyAttempt.objects.filter(user=user, survey=survey)
        data = survey_attempt_list(attempt_list)
    elif survey_id and channel_id and user_id == "":
        print(3)
        survey = Survey.objects.get(id=survey_id)
        channel = Channel.objects.get(id=channel_id)

        if channel.channel_type == "MentoringJourney":
            surveys = surveys_list_by_journey(channel)
        else:
            surveys = [channel.survey] if channel.survey else []

        attempt_list = SurveyAttempt.objects.filter(survey__in=surveys)
        data = survey_attempt_list(attempt_list)
    elif survey_id == "" and channel_id == "" and user_id:
        print(5)
        user = User.objects.get(pk=user_id)
        attempt_list = SurveyAttempt.objects.filter(user=user)
        data = survey_attempt_list(attempt_list)
    elif survey_id and channel_id == "" and user_id == "":
        print(6)
        survey = Survey.objects.get(id=survey_id)
        attempt_list = SurveyAttempt.objects.filter(survey=survey)
        data = survey_attempt_list(attempt_list)
    elif survey_id == "" and channel_id and user_id == "":
        print(7)
        channel = Channel.objects.get(id=channel_id)

        if channel.channel_type == "MentoringJourney":
            surveys = surveys_list_by_journey(channel)
        else:
            surveys = [channel.survey] if channel.survey else []

        attempt_list = SurveyAttempt.objects.filter(survey__in=surveys)
        data = survey_attempt_list(attempt_list)

    if request.session['user_type'] == "ProgramManager":
        all_users = User.objects.filter(company__in=request.user.company.all())
        attempt_list = attempt_list.filter(user__in=all_users)
        data = survey_attempt_list(attempt_list)
    print(len(attempt_list), "Print")
    print(data)
    file.writeheader()
    file.writerows(data)
    return response


def surveys_list_by_journey(channel):
    surveys_ids = MentoringJourney.objects.filter(journey=channel, meta_key="survey", is_delete=False).values("value")
    survey_id_list = [ids['value'] for ids in surveys_ids]
    print(survey_id_list)
    return Survey.objects.filter(pk__in=survey_id_list)


@login_required
def SurveyCSV(request, attempt_id):
    survey_attempt = SurveyAttempt.objects.get(pk=attempt_id)
    survey_attempt_count = SurveyAttempt.objects.filter(survey=survey_attempt.survey, user=survey_attempt.user).count()
    response = HttpResponse(content_type='text/csv', headers={
        'Content-Disposition': f'attachment; filename="{survey_attempt.survey.name}-{survey_attempt.user.username}.csv"'})

    Fields = (['ID', 'No of attempts', 'Unique key', 'Attemp_ID', 'Date of attempt submission', 'User Name', 'Type of User - Mentor/Mentee', 
                    'Paired Partner - Mentor/Mentee', 'User Industry', 'User Location', 'User Country', 'User Organisation', 'Matched partner industry', 'Test_Name', 
                    'Question', 'Answer', 'Upload_File', 'Journey_Name', 'AnnounceVery', 'AnnounceJust', 'Announce Not', 'Pre Very', 'Pre Just', 'Pre Not'])

    file = csv.DictWriter(response, fieldnames=Fields)
    user_answers = UserAnswer.objects.filter(survey_attempt=survey_attempt)
    details_list = []
    for attempt in user_answers:
        res1 = ''
        attempt_response = attempt.response

        if attempt.question.type == "MultiChoiceGrid":
            attempt_response = ast.literal_eval(attempt.response)
            for res in attempt_response:
                res = res[0].replace("/",":")
                res1 = f"{res1}, {res}" if res1 != "" else f"{res1}{res}"
            attempt_response = res1

        elif attempt.question.type == "CheckboxGrid":
            attempt_response = ast.literal_eval(attempt.response)
            for rest in attempt_response:
                for res in rest:
                    res = res.replace("/",":")
                    res1 = f"{res1}, {res}" if res1 != "" else f"{res1}{res}"
            attempt_response = res1

        elif attempt.question.type == "Checkbox":
            attempt_response = ast.literal_eval(attempt.response)
            for res in attempt_response:
                res1 = f"{res1}, {res}" if res1 != "" else f"{res1}{res}"
            attempt_response = res1

        details_list.append({
            "ID":1,
            "No of attempts": survey_attempt_count,
            "Unique key": survey_attempt.user.email,
            "Attemp_ID": survey_attempt.id,
            "Date of attempt submission": survey_attempt.created_at,
            "User Name": survey_attempt.user.username,
            "Type of User - Mentor/Mentee": ",".join(str(type.type) for type in survey_attempt.user.userType.all()),
            "Paired Partner - Mentor/Mentee": "",
            "User Industry": ",".join(str(industry.name) for industry in survey_attempt.user.industry.all()),
            "User Location": "",
            "User Country": "",
            "User Organisation": survey_attempt.user.organization,
            "Matched partner industry": ",".join(str(industry.name) for industry in survey_attempt.user.industry.all()),
            "Test_Name": survey_attempt.survey.name,
            "Question": attempt.question.title,
            "Answer": attempt_response,
            "Upload_File": "" if attempt.upload_file == "" else attempt.upload_file,
            "Journey_Name": survey_attempt.survey_attempt_channel.first().channel,
            "AnnounceVery": "",
            "AnnounceJust": "",
            "Announce Not": "",
            "Pre Very": "",
            "Pre Just": "",
            "Pre Not": "",
        })

    file.writeheader()
    file.writerows(details_list)
    return response


@login_required
def activeUserCSV(request, active_status):
    print(active_status)
    user_type = UserTypes.objects.get(type="Learner")
    users = User.objects.filter(is_active=active_status, is_delete=False, userType=user_type)
    if active_status == "True":
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="ActiveLearnerData.csv"'},
        )
    else:
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="InActiveLearnerData.csv"'},
        )

    Fields = (['User_ID', 'Username', 'Full_Name', 'Email', 'Phone', 'Company', 'Last_Login', 'Date_Joined', ])

    file = csv.DictWriter(response, fieldnames=Fields)
    details_list = []
    for user in users:
        comapny_list = [compny.name for compny in user.company.all()]
        company = ', '.join(comapny_list)
        print(company)
        details_list.append({
            "User_ID": user.id,
            "Username": user.username,
            "Full_Name": f"{user.first_name} {user.last_name}",
            "Email": user.email,
            "Phone": user.phone,
            "Company": company,
            "Date_Joined": user.date_joined,
            "Last_Login": user.last_login,
        })
    file.writeheader()
    file.writerows(details_list)
    return response


def Channel_Company(journey, user):
    usercompany = UserCompany.objects.create(user=user, company=journey.company)


@login_required
def update_journey(request):
    coupon_code = "AMP22"
    all_user = User.objects.filter(coupon_code=coupon_code)
    coupon = Coupon.objects.get(code=coupon_code)

    journey = Channel.objects.get(pk=coupon.journey)
    for user in all_user:
        if not user.company.all():
            print("Company Is None")
            UserCompany.objects.create(user=user, company=journey.company)
            user.company.add(journey.company)
            user.save()

            response = AlloteChannel(coupon.journey, user.pk)
            print(response)
    print(journey.company)

    return HttpResponse("s")

# def download_data(request):

#     user_email = ["adrian.tan@sgassist.com",
#     "aw.wibisana@gmail.com",
#     "briankhasegawa@gmail.com",
#     "carolhoon08@gmail.com",
#     "ccsaw@mewahgroup.com",
#     "cyenseah@gmail.com",
#     "daniel.tando@gmail.com",
#     "dawong1991@gmail.com",
#     "dyahambarwati@yahoo.com",
#     "eddielwp@gmail.com",
#     "francesburnhardt@gmail.com",
#     "generasicakap@gmail.com",
#     "greg.tan@sgassist.com",
#     "guankiat.lau@payboy.biz",
#     "haidanghere@gmail.com",
#     "hangconstant@gmail.com",
#     "hazrilharith@gmail.com",
#     "hello@windyagni.com",
#     "hongyen.pham71@gmail.com",
#     "hsgemilang@gmail.com",
#     "jamesneowh@gmail.com",
#     "jnvnamuco@gmail.com",
#     "Juliachin.li2021@gmail.com",
#     "lanh22003@yahoo.com",
#     "lawrence.p.young@hrfc.asia",
#     "lutbatb@gmail.com",
#     "mariejanise_06@yahoo.com",
#     "meganleetong@gmail.com",
#     "mendynasan16@gmail.com",
#     "mingyonglee90@gmail.com",
#     "n.shakinahrosman@gmail.com",
#     "narantsatsral.hr@gmail.com",
#     "patrick_hkw@yahoo.com.sg",
#     "ravi@growatpace.com",
#     "roma.tampubolon@bankraya.co.id",
#     "sauyong@peaks.sg",
#     "saywan.ong@payboy.biz",
#     "syahrida.syahrul@gmail.com",
#     "tuanpang@gmail.com",
#     "lavanyakarthikeyan1@gmail.com",
#     "battsetseg.7151@gmail.com",
#     "gunawanw@pure-tco.com",
#     "laneywijaya10@gmail.com",
#     "amarjargal301@gmail.com"]
#     # user_email = ["ravi@growatpace.com"]
#     user_list = User.objects.filter(email__in = user_email)
#     output_data = []
#     mentee = UserTypes.objects.get(type= "Learner")
#     mentor = UserTypes.objects.get(type="Mentor")

#     print(mentee, mentor)
#     for user_list in user_list:
#         alloted_mentor = ""
#         alloted_learner = ""
#         if mentee in user_list.userType.all():
#             print("1")
#             all_users  = AssignMentorToUser.objects.filter(user=user_list)
#             alloted_mentor = ",".join(str(user.user.email) for user in all_users)
#         if mentor in user_list.userType.all():
#             print(2)
#             all_users = AssignMentorToUser.objects.filter(mentor=user_list)
#             alloted_learner = ",".join(str(user.user.email) for user in all_users)
#         output_data.append({
#             "name": user_list.first_name + user_list.last_name,
#             "email" : user_list.email,
#             "locations": "",
#             "user_type":",".join(str(type.type) for type in user_list.userType.all()),
#             "alloted_learner": alloted_learner,
#             "alloted_mentor":alloted_mentor,
#             "organization": user_list.company.name,
#             "Industry": ",".join(str(industry.name) for industry in user_list.industry.all())
#         })
#     info = json.loads(json.dumps(output_data))

#     df = pd.json_normalize(info)

#     df.to_csv("samplecsv.csv")
#     print(output_data)
#     return  HttpResponse(output_data)


# def deactivate_user(request):
#     get_company = Company.objects.filter(id = "958ee7e42db347039a08a8064cbde053")
#     print(get_company)
#     all_users = User.objects.filter(company__in = get_company)
#     print(all_users)
#     return HttpResponse("Success")

import datetime

@login_required
def update_last_modified(request):
    code_coupan = Coupon.objects.get(code="DEFAULT")
    journey = code_coupan.journey
    channel = Channel.objects.get(pk = journey)
    d = datetime.date(2022, 8, 10)
    print(d)
    user_channel = UserChannel.objects.filter(Channel = channel)
    for user in User.objects.all():
        user.date_modified = user.date_joined
        user.save()
    for user in user_channel:
        print(user.user)
        # user.user.date_modified = d
        # user.user.save()
        user_list = User.objects.get(pk=user.user.pk)
        user_list.date_modified = d
        user_list.save()
        print(user_list.date_modified)
    print(user_channel)
    return HttpResponse("Success")


@permission_classes((AllowAny,))
class all_user_download_data(View):
    def get(self, request, **kwargs):

        user = User.objects.get(pk=self.kwargs['user_id'])
        journey = Channel.objects.get(pk=self.kwargs['journey_id'])
        company = Company.objects.get(pk=self.kwargs['company_id'])
        user_type = UserTypes.objects.get(type=self.kwargs['user_type'])

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="MatchingReport.csv"'

        Fields = ([ 'Id', 'Username', 'Email', 'First_Name', 'Last_Name', 'Phone', 'Gender', 'Age', 'User_Type', 'Status', 'Profile_Assessment', 'Join_Date', 'Modified_Date', 'Linked_in', 'Designation', 'Department', 'Organization', 'City & Country', 'Which INDUSTRY are you currently in?', '3 goals', 'Self Match', 'Company'  ])

        file = csv.DictWriter(response, fieldnames=Fields)

        match_ques_config = MatchQuesConfig.objects.filter(company=company, journey=journey).first()
        match_questions = MatchQuestion.objects.filter(ques_config=match_ques_config)
        if user_type.type == 'Mentor':
            profile_ques = [ques.mentor_ques for ques in match_questions]
            
            pool_mentor = PoolMentor.objects.filter(pool__company=company, pool__journey=journey, is_active=True)
            all_user = [user.mentor for user in pool_mentor]

        elif user_type.type == 'Learner':
            profile_ques = [ques.learner_ques for ques in match_questions]

            user_channel = UserChannel.objects.filter(status='Joined', is_removed=False, Channel=journey)
            all_user_list = [user_obj.user.pk for user_obj in user_channel]

            all_user = User.objects.filter(pk__in=all_user_list, userType__type='Learner')

        question_4 = ProfileAssestQuestion.objects.filter(question="Job Title/Designation", question_for=user_type.type).first()
        question_5 = ProfileAssestQuestion.objects.filter(question="Organization", question_for=user_type.type).first()
        question_6 = ProfileAssestQuestion.objects.filter(question="Department/Function", question_for=user_type.type).first()
        question_7 = ProfileAssestQuestion.objects.filter(question="LinkedIn Profile", question_for=user_type.type).first()
        question_8 = ProfileAssestQuestion.objects.filter(question="City & Country", question_for=user_type.type).first()
        user_list = []
        for user in all_user:
            try:
                company =  ",".join(str(type.company.name) for type in user.user_company.all())
            except:
                company = ""

            ans_1 = ans_2 = ans_3 = ans_4 = ans_5 = ans_6 = ans_7 = ans_8 = []
            if UserProfileAssest.objects.filter(user=user).count() == 0:
                profile_assessment = "Pending"

            else:
                if len(profile_ques) > 0:
                    ans_1 = UserProfileAssest.objects.filter(assest_question=profile_ques[0], user=user)
                if len(profile_ques) > 1:
                    ans_2 = UserProfileAssest.objects.filter(assest_question=profile_ques[1], user=user)
                if len(profile_ques) > 2:
                    ans_3 = UserProfileAssest.objects.filter(assest_question=profile_ques[2], user=user)
                if question_4:
                    ans_4 = UserProfileAssest.objects.filter(assest_question=question_4, user=user)
                if question_5:
                    ans_5 = UserProfileAssest.objects.filter(assest_question=question_5, user=user)
                if question_6:
                    ans_6 = UserProfileAssest.objects.filter(assest_question=question_6, user=user)
                if question_7:
                    ans_7 = UserProfileAssest.objects.filter(assest_question=question_7, user=user)
                if question_8:
                    ans_8 = UserProfileAssest.objects.filter(assest_question=question_8, user=user)
                profile_assessment = "Complete"
            user_list.append({
                'Id': str(user.id),
                'Username': user.username,
                'Email': user.email,
                'First_Name': user.first_name,
                'Last_Name': user.last_name,
                'Phone': str(user.phone),
                'Gender': user.gender,
                'Age': user.age,
                'User_Type': ",".join(str(type.type) for type in user.userType.all()),
                "Status": user.is_active,
                "Profile_Assessment": profile_assessment,
                "Join_Date": user.date_joined,
                "Modified_Date": user.date_modified,
                "Linked_in": ans_7[0].response if len(ans_7) > 0 else "",
                "Designation": ans_4[0].response if len(ans_4) > 0 else "",
                "Department": ans_6[0].response if len(ans_6) > 0 else "",
                "Organization": ans_5[0].response if len(ans_5) > 0 else "",
                "City & Country": ans_8[0].response if len(ans_8) > 0 else "",
                "Which INDUSTRY are you currently in?": ans_1[0].response if len(ans_1) > 0 else "",
                "3 goals": ans_2[0].response if len(ans_2) > 0 else "",
                "Self Match": ans_3[0].response if len(ans_3) > 0 else "",
                "Company": company
            })

        file.writeheader()
        file.writerows(user_list)

        return response


@login_required
def update_question_type(request):
    use_profile_assest = UserProfileAssest.objects.all()
    for use_profile_assest in use_profile_assest:
        use_profile_assest.question_for = use_profile_assest.assest_question.question_for
        use_profile_assest.save()
    return HttpResponse("Success")


@login_required
def change_course_type(request):
    journey_type = ["onlyCommunity", "Course", "SurveyCourse"]
    get_channel = Channel.objects.filter(channel_type__in=journey_type).update(channel_type="MentoringJourney")
    print(get_channel)
    return HttpResponse("Success")

