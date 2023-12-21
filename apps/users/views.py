import re
import pandas as pd
import uuid
import ast
from apps.program_manager_panel.models import ProgramManagerTask
from apps.users.helper import add_user_to_company, user_company
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import json, jwt
from django.views.decorators.csrf import csrf_exempt
from requests import request
from apps.atpace_community.utils import add_member_to_space, avatar, create_journey_space, default_space_join_user, \
    add_to_community_event, strf_format
from apps.leaderboard.utils import user_dashboard, mentor_dashboard
from apps.vonage_api.utils import journey_enrolment, live_stream_event, program_team_broadcast, user_credentail_info, \
    enroll_lite
from django_user_agents.utils import get_user_agent
from django.core.validators import validate_email
import csv
from http.client import HTTPResponse
from django.utils.http import urlsafe_base64_decode
import logging
import random
import string
from datetime import datetime
from apps.api.utils import available_slots, book_appointment, cancel_appointment, get_or_create_user, meeting_notification, social_type, update_boolean
from apps.chat_app.models import Chat, Room
from apps.leaderboard.userStreaks import userStreakActivity, userStreakCount, lineChartData
from user_visit.models import UserVisit
import requests
from apps.users.models import UserPhoneChangeRecord
from ravinsight import settings
from apps.content.models import Channel, JourneyContentSetupOrdering, ProgramTeamAnnouncement, UserChannel, MatchQuesConfig, MatchQuestion, \
    journeyContentSetup, UserActivityData
from apps.users.utils import convert_to_local_time, convert_to_utc, marketplace_user_email, getJourneyUsers, removeUserSlotFun, send_missing_existing_users, strf_format
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import response
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView
)
from ravinsight.web_constant import BASE_URL, SITE_NAME, DOMAIN, PROTOCOL
from datetime import date, datetime, timedelta
from django.views.generic import RedirectView
from django.views.generic.base import View
from rest_framework.views import APIView
# from api.views.views import GenerateOtp
from apps.leaderboard.views import NotificationAndPoints, UserBestStreak, UserSiteVisit, dashboardMentorshipGoal, \
    UpdateUserStreakCount, AddUserStreak, CheckEndOfJourney, UserNextGoal, EndOfJourney, send_push_notification
from apps.community.models import LearningJournals, LearningJournalsAttachment, LearningJournalsComments, \
    WeeklyLearningJournals
from apps.mentor.models import AllMeetingDetails, AssignMentorToUser, MeetingParticipants, Pool, PoolMentor
from apps.mentor.models import mentorCalendar
from apps.content.models import MentoringJourney, Content, UserCourseStart, TestAttempt, \
    ProgramAnnouncementWhatsappReport
from apps.survey_questions.models import Survey, SurveyAttempt
from apps.test_series.models import TestSeries
from apps.leaderboard.models import UserPoints, UserBadgeDetails, BadgeDetails, StreakPoints, UserStreakHistory, \
    UserEngagement
from ravinsight.decorators import admin_only
from ravinsight.web_constant import INFO_CONTACT_EMAIL
from apps.users.templatetags.tags import cookie, user_profile_assessment, get_chat_room
from apps.users.utils import *
from rest_framework.authtoken.models import Token

from apps.utils.utils import send_otp, generate_attendence, url_shortner, vonage_sms_otp, vonage_sms_otp_sender
import math
from .forms import (
    CollabarateForm,
    EditCollabarateForm,
    CollabarateGroupForm,
    EditCollabarateGroupForm,
    CompanyCreationFrom,
    CouponCodeForm,
    CreateRoleForm,
    CustomAdminCreationForm,
    CustomAuthenticationForm,
    CustomUserCreationForm,
    CustomUserUpdateForm,
    ProfileAssestQuestionFrom,
    SetPasswordForm,
    UploadCSVForm,
    UserProfileUpdateForm,
    ContactProgramTeamForm,
)
from .models import (
    AdminUser,
    Collabarate,
    Coupon,
    Learner,
    Company,
    Profile,
    ProfileAssestQuestion,
    User,
    UserCompany,
    UserProfileAssest,
    UserRoles,
    UserTypes,
    Mentor,
    ProgramManager,
    ContactProgramTeam,
    ContactProgramTeamImages,
    UserEarnedPoints,
    UserEmailChangeRecord,
    UserPhoneChangeRecord
)
from apps.webapp.utils import user_device
from apps.chat_app.models import Chat, Room as AllRooms
import time
from apps.atpace_community.models import Event, Post
from apps.utils.models import UrlShortner
from apps.content.utils import company_journeys
from .serializers import CheckLiteSignupUserSerializer, UserEnrollCheckSerializer, AssesmentQuestionSerializer
from rest_framework.permissions import AllowAny
from django.http import HttpResponseRedirect

# from oauth2_provider.models import AccessToken, Application, RefreshToken
# Create your views here.
logger = logging.getLogger('django')


# def send_otp(mobile, otp):
#     print("FUNCTION CALLED")

#     data = "Send OTP"
#     print(data)
#     return None


def check_check_box(value):
    if value == "on":
        return True
    elif value == True:
        return True
    else:
        return False


def login_attempt(request):
    user_type_list = UserTypes.objects.filter(~Q(type="Creator"))

    if request.method == 'POST':
        mobile = request.POST.get('mobile')
        type = request.POST.get('type')
        user = User.objects.filter(phone=mobile).first()

        if user is None:
            messages.error(
                request, f'User with phone number {mobile} not found.')
            context = {"user_type": user_type_list}
            return render(request, 'auth/login_with_otp.html', context)

        user_type = UserTypes.objects.get(id=type)

        try:
            check_user = User.objects.get(phone=mobile, userType=user_type)
        except User.DoesNotExist:
            messages.error(
                request, 'Please enter a correct phone number with country code and user type.')
            return redirect(reverse('user:login_otp'))
        request.session['user_type'] = user_type.type

        if user_type.type != 'Admin' and request.POST.get('company'):
            company_id = request.POST['company']
            request.session['company_id'] = company_id
            company = Company.objects.get(pk=company_id)
            request.session['company_name'] = company.name
        otp = str(random.randint(100000, 999999))

        user_profile = Profile.objects.filter(user=user)
        if user_profile.count() > 0:
            user_profile = Profile.objects.filter(user=user).first()
            user_profile.otp = otp
            user_profile.save()
        else:
            user_profile = Profile.objects.create(user=user, otp=otp)
        vonage_sms_otp_sender(user, otp)
        # send_otp_mail(user, otp)

        request.session['mobile'] = mobile
        # UserDeviceDetails()
        return redirect('user:otp_login')
    user_type_list = UserTypes.objects.filter(~Q(type="Creator"))

    return render(request, 'auth/login_with_otp.html', {"user_type": user_type_list})


def ResendOtp(request, *args, **kwargs):
    if request.method == 'GET':
        mobile = request.session['mobile']
        if not User.objects.filter(phone__iexact=mobile).exists():
            return redirect(reverse('user:login_otp'))
        user = User.objects.get(phone__iexact=mobile)
        otp = str(random.randint(100000, 999999))

        user_profile = Profile.objects.filter(user=user)

        if user_profile.count() > 0:
            user_profile = Profile.objects.filter(user=user).first()
            user_profile.otp = otp
            user_profile.save()
            vonage_sms_otp_sender(user, otp)
        return redirect('user:otp_login')
    return redirect(reverse('user:login_otp'))


def login_otp(request):
    try:
        mobile = request.session['mobile']
    except KeyError:
        if request.user.is_authenticated:
            return redirect('user:user-dashboard')
        return redirect('user:otp_login')
    is_lite_signup = False
    context = {'mobile': mobile}
    if request.method == 'POST':
        otp = request.POST.get('otp')

        if 'is_lite_signup' in request.session:
            is_lite_signup = request.session['is_lite_signup']

        user = User.objects.filter(phone=mobile).first()
        profile = Profile.objects.filter(user=user).first()

        if otp == profile.otp:
            user = User.objects.get(id=profile.user.id)
            user.is_phone_verified = True
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            token, created = Token.objects.get_or_create(user=user)
            request.session['token'] = token.key
            # UserDeviceDetails()
            UserSiteVisit(user)

            if user.is_email_verified:

                if request.COOKIES.get('course_detail_url'):
                    url = request.COOKIES.get('course_detail_url')
                    return redirect(url)
                if is_lite_signup:
                    return redirect('user:signup-thankyou')
                return redirect('user:user-dashboard')
            else:
                return render(request, 'auth/resend_mail_verification.html')

        else:
            context = {'message': 'Wrong OTP', 'class': 'danger', 'mobile': mobile}
            return render(request, 'auth/otp-verify.html', context)

    return render(request, 'auth/otp-verify.html', context)


@login_required
def signup_thankyou(request):
    journey = Channel.objects.filter(pk=request.session['list_signup_journey']).first()
    try:
        user_type = request.session['session_type']
    except:
        user_type = None
    if journey.whatsapp_notification_required and (request.user.phone and request.user.is_whatsapp_enable):
        enroll_lite(request.user, journey, user_type)
    else:
        print("no phone number exist")
    del request.session['list_signup_journey']
    return render(request, 'website/signup-thankyou.html', {"journey": journey})


def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        coupon_code = request.POST.get('coupon_code')
        print("coupon", coupon_code)
        user_type = request.POST.get('type')
        term_and_conditions = check_check_box(request.POST.get('term_and_conditions'))
        is_whatsapp_enable = check_check_box(request.POST.get('is_whatsapp_enable'))
        if User.objects.filter(username=username).exists():
            context = {'message': 'Username is already exists', 'class': 'danger'}
            return render(request, 'website/register.html', context)
        print(username)
        try:
            validate_email(email)
        except:
            context = {'message': 'you have entered incorrect email address', 'class': 'danger'}
            return render(request, 'website/register.html', context)

        if not '+' in mobile:
            context = {'message': 'you have entered incorrect country code or phone number', 'class': 'danger'}
            return render(request, 'website/register.html', context)
        if User.objects.filter(phone=mobile).exists():
            context = {'message': 'Phone Number is already exists', 'class': 'danger'}
            return render(request, 'website/register.html', context)

        type = UserTypes.objects.get(type=user_type)
        request.session['user_type'] = type.type

        check_user = User.objects.filter(email=email).first()
        check_profile = Profile.objects.filter(user=check_user).first()

        if check_user or check_profile:
            context = {'message': 'User already exists', 'class': 'danger'}
            return render(request, 'website/register.html', context)
        if not validate_Coupon(coupon_code):
            context = {'message': 'Invalid Coupon Code', 'class': 'danger'}
            return render(request, 'website/register.html', context)
        
        coupon = Coupon.objects.get(code__iexact=coupon_code, valid_from__lte=datetime.now(),
                           valid_to__gte=datetime.now(), is_active=True)
        journey = Channel.objects.filter(id=coupon.journey, closure_date__gt=datetime.now()).first()
        request.session['company_id'] = str(journey.company.id)
        request.session['company_name'] = journey.company.name

        user = User(email=email, first_name=name, phone=mobile, username=username,
                    coupon_code=coupon_code, is_term_and_conditions_apply=term_and_conditions, is_whatsapp_enable=is_whatsapp_enable)
        password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
        print(password)
        user.set_password(password)
        user.save()
        user.userType.add(type.id)
        user.save()
        default_space_join_user(user)
        applyCouponCode(user, coupon_code)

        otp = str(random.randint(100000, 999999))

        profile = Profile(user=user, otp=otp)
        profile.save()
        vonage_sms_otp_sender(user, otp)
        register_email(user, password)
        if user.phone and user.is_whatsapp_enable:
            user_credentail_info(user, password)
        else:
            print("Mobile info not provided")
        NotificationAndPoints(user, title="registration")
        request.session['mobile'] = mobile
        return redirect('user:otp_login')
    return render(request, 'website/register.html')


def assessment_question(request, journey):
    profile_assest = ProfileAssestQuestion.objects.filter(
        question_for=request.GET.get('type'), is_active=True, is_delete=False, journey=journey)
    return render(request, "partials/assessment_question_list.html", {"profile_assest": profile_assest})


def user_enroll_check(request):
    if request.method == 'POST':
        print("data ", request.POST)
        user = User.objects.filter(email=request.POST.get('email'))
        user_type = request.POST.get('type')
        journey_id = request.POST.get('journey_id')
        response = {"success": True}
        if user:
            user = user.first()
            type = ",".join(str(type.type) for type in user.userType.all())
            print("user_type", user_type)
            data = update_signup_lite(user, type, user_type, journey_id)
            print('data1 ', data)
            if not data:
                print('data2 ', response)
                return JsonResponse(response, safe=False)
            return JsonResponse(data, safe=False)
        print('data3 ', response)
        return HttpResponse(response)
    else: return HttpResponse("Method not allowed", status=405)

class UserEnrollCheck(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        data = request.data
        serializer = UserEnrollCheckSerializer(data=data)
        if serializer.is_valid():
            print("data ", request.data)
            user = User.objects.filter(email=request.data['email'])
            user_type = request.data['type']
            journey_id = request.data['journey_id']
            response = {"success": True}
            if user:
                user = user.first()
                type = ",".join(str(type.type) for type in user.userType.all())
                print("user_type", user_type)
                data = update_signup_lite(user, type, user_type, journey_id)
                print('data1 ', data)
                if not data:
                    print('data2 ', response)
                    return JsonResponse(response, safe=False)
                return JsonResponse(data, safe=False)
            print('data3 ', response)
            return HttpResponse(response)
        else:
            HTTPResponse({"message":"missing parameter", "success":False})

class AssesmentQuestions(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        data = request.query_params
        serializer = AssesmentQuestionSerializer(data=data)
        if serializer.is_valid():
            profile_assest = ProfileAssestQuestion.objects.filter(
                question_for=request.query_params['type'], is_active=True, is_delete=False, journey=request.query_params['journey_id'])
            return render(request, "partials/assessment_question_list.html", {"profile_assest": profile_assest})
        else: return HTTPResponse({"message":"missing params", "success": False})

class SignupLite(View):
    def get(self, request, journey_id):
        journey = Channel.objects.get(pk=journey_id)
        coupon_code = Coupon.objects.filter(valid_from__lte=datetime.now(),
                                            valid_to__gte=datetime.now(), is_active=True, journey=journey_id)
        coupon = coupon_code.first().code if coupon_code else ''
        journey_page_content = journeyContentSetup.objects.filter(
            journey_id=journey_id, is_active=True, is_delete=False)
        cta_button_title = pdpa_statement = cta_button_action = video_url = overview = learn_label = pdpa_label = ""
        journey_page_content = journey_page_content.first()
        print("journey_page_content", journey_page_content)
        if journey_page_content:
            # journey_page_content = journey_page_content.first()
            pdpa_statement = journey_page_content.pdpa_description
            pdpa_label = journey_page_content.pdpa_label
            learn_label = journey_page_content.learn_label
            overview = journey_page_content.overview
            video_url = journey_page_content.video_url
            cta_button_action = journey_page_content.cta_button_action
            cta_button_title = journey_page_content.cta_button_title

        print("hello 343 ", video_url)
        print("journey_page_content ", journey_page_content)
        ordering = JourneyContentSetupOrdering.objects.filter(content_setup=journey_page_content, is_active=True)
        request.session['list_signup_journey'] = str(journey_id)
        data = {"coupon_code": coupon}
        # profile_assest = ProfileAssestQuestion.objects.filter(question_for="Learner")
        return render(request, 'website/signup-lite.html',
                      {"journey": journey, "data": data, "pdpa_statement": pdpa_statement, "pdpa_label": pdpa_label, "cta_button_action": cta_button_action,
                       "cta_button_title": cta_button_title, "overview": overview, "learn_label": learn_label, "video_url": video_url, "ordering": ordering})

    def post(self, request, journey_id):
        journey = Channel.objects.get(pk=journey_id)
        user = User.objects.filter(Q(email=request.POST.get('email')) | Q(phone=request.POST.get('mobile')))
        data = {"coupon_code": request.POST.get('coupon_code')}
        user_type = request.POST.get('type')
        if not User.objects.filter(username=request.POST.get('username')).exists() and not re.match("^[a-z]+$", request.POST.get('username')):
            print("request.session['username'] ", request.POST.get('username'))
            context = {'message': 'you have entered incorrect username',
                       'class': 'danger', "journey": journey, "data":data}
            return render(request, 'website/signup-lite.html', context)
        # if user:
        #     user = user.first()
        #     type = ",".join(str(type.type) for type in user.userType.all())
        #     print("user_type", user_type)
        #     data = update_signup_lite(user, type, user_type, journey_id)
        #     if not user.phone:
        #         if not '+' in request.POST.get('mobile'):
        #             context = {'message': 'you have entered incorrect country code or phone number',
        #                        'class': 'danger', "journey": journey}
        #             return render(request, 'website/signup-lite.html', context)
        #         if User.objects.filter(phone=request.POST.get('mobile')).exists():
        #             context = {'message': 'Phone Number is already exists', 'class': 'danger', "journey": journey}
        #             return render(request, 'website/signup-lite.html', context)
        request.session['email'] = request.POST.get('email')
        request.session['username'] = request.POST.get('username')
        request.session['name'] = request.POST.get('name')
        request.session['temp_mobile'] = request.POST.get('mobile')
        request.session['session_type'] = request.POST.get('type')
        request.session['term_and_conditions'] = request.POST.get('term_and_conditions')
        request.session['is_whatsapp_enable'] = request.POST.get('is_whatsapp_enable')
        request.session['pdpa_statement'] = request.POST.get('pdpa_statement')
        request.session['coupon_code'] = request.POST.get('coupon_code')
        request.session['is_lite_signup'] = True
        question = request.POST.getlist('question[]')
        response = request.POST.getlist('response[]')
        question_list = []
        for x in range(len(question)):
            profile_question = ProfileAssestQuestion.objects.get(pk=question[x])
            question_list.append({
                "question": profile_question.question,
                "question_id": profile_question.pk,
                "response": response[x],
                "question_type": profile_question.question_type,
                "options": profile_question.options
            })
        request.session['question_list'] = question_list
        # print("data", data)
        return render(request, 'website/signup-preview.html', {"data": request.POST, "question_list": question_list, "journey_id": journey_id, "user_type": user_type})

def check_user_name(request):
    if not User.objects.filter(username__iexact=request.GET.get('username')).exists():
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

def signup_lite_post(request):
    email = request.session['email']
    username = request.session['username']
    name = request.session['name']
    mobile = request.session['temp_mobile']
    coupon_code = request.session['coupon_code']
    user_type = request.session['session_type']
    term_and_conditions = check_check_box(request.session['term_and_conditions'])
    is_whatsapp_enable = check_check_box(request.session['is_whatsapp_enable'])
    pdpa_statement = check_check_box(request.session['pdpa_statement'])
    journey = Channel.objects.get(pk=request.session['list_signup_journey'])
    type = UserTypes.objects.get(type=user_type)
    request.session['user_type'] = type.type
    request.session['mobile'] = mobile
    request.session['company_id'] = str(journey.company.id)
    request.session['company_name'] = journey.company.name
    user = User.objects.filter(username=username, email=email)
#     modified_date =convert_to_utc(datetime.now(), request.session['timezone'])
    modified_date = datetime.now()

    if not user:
        data = {"coupon_code": coupon_code}
        print(username)
        try:
            validate_email(email)
        except:
            context = {'message': 'you have entered incorrect email address', 'class': 'danger', "journey": journey, "data":data}
            return render(request, 'website/signup-lite.html', context)

        if not '+' in mobile:
            context = {'message': 'you have entered incorrect country code or phone number',
                       'class': 'danger', "journey": journey, "data":data}
            return render(request, 'website/signup-lite.html', context)

        # if not re.match("^[a-zA-Z0-9_.@.+-]+$", request.session['username']):
        #     print("request.session['username'] ", request.session['username'])

        #     context = {'message': 'you have entered incorrect username',
        #                'class': 'danger', "journey": journey}
        #     return render(request, 'website/signup-lite.html', context)
        if not User.objects.filter(username=request.session['username']).exists() and not re.match("^[a-z]+$", request.session['username']):
            print("request.session['username'] ", request.session['username'])
            context = {'message': 'you have entered incorrect username',
                       'class': 'danger', "journey": journey, "data":data}
            return render(request, 'website/signup-lite.html', context)
            
        if User.objects.filter(phone=mobile).exists():
            context = {'message': 'Phone Number is already exists', 'class': 'danger', "journey": journey, "data":data}
            return render(request, 'website/signup-lite.html', context)

        check_user = User.objects.filter(email=email).first()
        check_profile = Profile.objects.filter(user=check_user).first()
        print("line 340", check_user, check_profile)
        if check_user or check_profile:
            context = {'message': 'User already exists', 'class': 'danger', "journey": journey, "data":data}
            return render(request, 'website/signup-lite.html', context)

        if not validate_Coupon(coupon_code):
            context = {'message': 'Invalid Coupon Code', 'class': 'danger', "journey": journey, "data":data}
            return render(request, 'website/signup-lite.html', context)
        user = User(email=email, first_name=name, phone=mobile, username=username, coupon_code=coupon_code,
                    is_whatsapp_enable=is_whatsapp_enable,
                    pdpa_statement=pdpa_statement, is_lite_signup=True, is_email_verified=True,
                    is_term_and_conditions_apply=term_and_conditions, date_modified=modified_date)
        
        password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
        print(password)
        user.set_password(password)
        user.save()
    else:
        user = user.first()
        if user.phone is None:
            user.phone = mobile
        if f"{user.first_name} {user.last_name}" != name:
            name = name.split(" ")
            user.first_name = name[0]
            user.last_name = " ".join(name[1:])
        user.is_whatsapp_enable = is_whatsapp_enable
        user.pdpa_statement = pdpa_statement
        user.is_lite_signup = True
        user.is_email_verified = True
        user.date_modified = modified_date
        password = None

    user_types = ",".join(str(type.type) for type in user.userType.all())
    if request.session['user_type'] not in user_types:
        user.userType.add(type.id)

    user.save()
    default_space_join_user(user)
    if coupon_code:
        applyCouponCode(user, coupon_code)

    for question in request.session['question_list']:
        print(question['question'])
        profile_question = ProfileAssestQuestion.objects.get(pk=question['question_id'])
        user_profile_question = UserProfileAssest.objects.filter(
            assest_question=profile_question, question_for=user_types).first()
        if user_profile_question:
            UserProfileAssest.objects.create(user=user, question_for=request.session['user_type'],
                                             assest_question=profile_question, response=question['response'])
    otp = str(random.randint(100000, 999999))
    print(otp)
    try:
        profile = Profile.objects.get(user=user)
        profile.otp = otp
        profile.save()
    except Exception:
        Profile.objects.create(user=user, otp=otp)
    vonage_sms_otp_sender(user, otp)
    register_email(user, password)

    NotificationAndPoints(user, title="registration")

    return redirect('user:otp_login')


def check_coupon_code(request):
    coupon_code = request.POST['coupon_code']
    journey_id = request.POST['journey_id']
    response = Coupon.objects.filter(code__iexact=coupon_code, valid_from__lte=datetime.now(),
                                     valid_to__gte=datetime.now(), is_active=True, journey=journey_id).exists()
    return JsonResponse({"success": response})


def check_phone(request):
    mobile = request.POST['phone']
    print(f"mobile: {mobile}")
    try:
        user = User.objects.get(phone__iexact=mobile)
    except User.DoesNotExist:
        return JsonResponse({"data": {"success": False}})
    response = {
        "phone": str(user.phone),
        "username": user.username,
        "success": True
    }
    return JsonResponse({"data": response})


def check_username(request):
    username = request.POST['username']
    print(f"username: {username}")
    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        return JsonResponse({"data": {"success": False}})
    response = {
        "username": str(user.username),
        "phone": user.phone,
        "success": True
    }
    return JsonResponse({"data": response})



def get_user_company(request):

    data = request.POST['email']
    try:
        user = User.objects.get(Q(email=data) | Q(username=data) | Q(phone=data), is_delete=False, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({"data": {"success": False}})

    company_list = []
    for comp in user.company.all():
        company_list.append({
            "id": comp.id,
            "name": comp.name
        })
    response = {
        "company": company_list,
        "success": True
    }
    return JsonResponse({"data": response})


def save_user_company(request):
    try:
        company_id = request.POST['company_id']
        request.session['company_id'] = company_id
        company = Company.objects.get(pk=company_id)
        print("company", company.logo)
        request.session['company_name'] = company.name
        response = {
            "success": True,
            "company": company.name,
            "company_id": company.id,
            "company_logo": company_logo(company)
        }
    except:
        response = {
            "success": False
        }
    return JsonResponse({"data": response})


def check_lite_signup_user(request):
    email = request.POST['email']
    phone = request.POST['phone']

    journey_id = request.POST['journey_id']
    combo_user = User.objects.filter(email=email, phone=phone, is_active=True, is_delete=False)
    print("edewc", email, phone)
    users = User.objects.filter(Q(email=email) | Q(phone=phone), is_active=True, is_delete=False)
    all_users = combo_user | users
    user_list = []
    if not all_users:
        context = {
            "success": False,
            "message": "User does not exist"
        }
        return JsonResponse(context)
    for user in all_users:
        userr_type = ",".join(str(type.type) for type in user.userType.all())
        user_list.append({
            "is_active": user.is_active,
            "user_type": userr_type,
            "email": user.email if user else "",
            "username": user.username if user else "",
            "mobile": str(user.phone) if user else "",
            "first_name": user.first_name if user else "",
            "last_name": user.last_name if user else ""
        })

    codee = ''
    if code := Coupon.objects.filter(journey=journey_id, valid_from__lte=datetime.now(), valid_to__gte=datetime.now(),
                                     is_active=True):
        codee = code.first().code
    context = {
        "success": True,
        "coupon_code": codee if user else "",
        "users": user_list
    }
    return JsonResponse(context)


def merge_user_record(request):
    account = request.POST['account']
    email = account.split("and")[0]
    phone = account.split("and")[1]
    combo_user = User.objects.filter(email=email, phone=phone, is_active=True, is_delete=False)
    users = User.objects.filter(Q(email=email) | Q(phone=phone), is_active=True, is_delete=False)
    all_users = combo_user | users
    all_users.filter(~Q(email=email) & ~Q(phone=phone)).update(is_active=False, is_delete=True)
    return JsonResponse({"success": True})


def lite_signup_edit(request, journey_id):
    journey_page_content = journeyContentSetup.objects.filter(
        journey_id=journey_id, is_active=True, is_delete=False).first()

    ordering = JourneyContentSetupOrdering.objects.filter(content_setup=journey_page_content, is_active=True)
    data = {
        "email": request.session['email'],
        "username": request.session['username'],
        "name": request.session['name'],
        "mobile": request.session['temp_mobile'],
        "coupon_code": request.session['coupon_code'],
        "user_type": request.session['session_type']
    }
    print(request.session['question_list'])
    journey = Channel.objects.get(pk=journey_id)
    print(data)
    return render(request, 'website/signup-lite.html',
                  {"question_list": request.session['question_list'], "data": data, "journey": journey,
                   "pdpa_statement": journey_page_content.pdpa_description, "ordering": ordering, "pdpa_label": journey_page_content.pdpa_label})


def resend_Verify_Email(request):
    try:
        user = User.objects.get(id=request.user.id)
    except User.DoesNotExist:
        return HttpResponse("User Does not exist")
    print("email ", user.email)
    sendVerificationMail(user, user.email)
    return render(request, 'auth/resend_mail_verification.html')


def Email_Verify(request, uidb64, token):
    try:
        id = urlsafe_base64_decode(uidb64).decode("utf-8")
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        user = None
    if not (user and user.token):
        return render(request, 'auth/invalid_email_link.html')
    user.is_email_verified = True
    user.token = ''
    if validate_Coupon(user.coupon_code):
        code = Coupon.objects.get(code__iexact=user.coupon_code)
        journey = Channel.objects.get(id=code.journey)
        if journey.whatsapp_notification_required and (user.phone and user.is_whatsapp_enable):
            journey_enrolment(user, journey)
        else:
            print("phone does not exist")

    user.save()
    return render(request, 'auth/mail_verification_complete.html')


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'website/login.html'

    def get(self, request):
        user_agent = get_user_agent(request)
        if request.user.is_authenticated:
            if request.session['user_type'] == "Admin":
                return redirect(reverse('user:user-dashboard'))
            elif request.user.is_email_verified:
                user_device(user_agent, request.user)
                if request.COOKIES.get('course_detail_url'):
                    url = request.COOKIES.get('course_detail_url')
                    return redirect(url)
                return redirect(reverse('user:user-dashboard'))
            else:
                return render(request, 'auth/resend_mail_verification.html')
        else:
            return render(request, 'website/login.html', {'form': self.authentication_form})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        type = request.POST.get('type')

        user_type = UserTypes.objects.get(id=type)
        request.session['user_type'] = user_type.type

        # print(user_type)
        check_user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username), userType=user_type)
        # print("line 304", check_user)
        if not check_user:
            # context = {'message': '', 'class': 'danger'}
            messages.error(
                request, "Please enter a correct username and password. Note that both fields may be case-sensitive.")

            return redirect(reverse('user:login'))
            # return render(request, 'website/login.html',{'form': self.authentication_form, 'messages':context})

        user = authenticate(username=username, password=password)
        if user:
            if not request.POST.get('company'):
                messages.error(
                    request, "Company is required, You must be associated with a company to login.")
                return redirect(reverse('user:login'))
            if user.is_active:
                if user_type.type != 'Admin' and request.POST.get('company'):
                    company_id = request.POST['company']
                    request.session['company_id'] = company_id
                    company = Company.objects.get(pk=company_id)
                    request.session['company_name'] = company.name
                else:
                    request.session['company_id'] = None

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                UserSiteVisit(user)
                UpdateUserStreakCount(user)
                AddUserStreak(user)
                token, created = Token.objects.get_or_create(user=user)
                request.session['token'] = token.key
                user_agent = get_user_agent(request)
                user_device(user_agent, request.user)
                # asynmail(user, request.user.email)
                next_url = request.GET.get('next')
                if next_url:
                    return HttpResponseRedirect(next_url)
                else:
                    if request.session['user_type'] == "Admin":
                        return redirect(reverse('user:user-dashboard'))
                    elif user.is_email_verified:
                        if request.COOKIES.get('course_detail_url'):
                            url = request.COOKIES.get('course_detail_url')
                            return redirect(url)
                        return redirect(reverse('user:user-dashboard'))
                    else:
                        return render(request, 'auth/resend_mail_verification.html')

            else:

                # context = {'messages': 'Your account is deactivted', 'class': 'danger'}
                # return render(request, 'website/login.html',{'form': self.authentication_form, 'messages':context})
                messages.error(request, "Your account is deactivted")
                return redirect(reverse('user:login'))
        else:
            messages.error(
                request, "Please enter a correct username and password. Note that both fields may be case-sensitive.")
            return redirect(reverse('user:login'))


@method_decorator(login_required, name='dispatch')
class DashBorad(TemplateView):
    '''
       Redirect to the DashBorad Page.
    '''
    content_type = 'text/html'
    template_name = "users/dashboard.html"

    def get(self, request):
        if 'UserDashboardView' in request.session:
            del request.session['UserDashboardView']
            del request.session['dashbordId']

        if 'MentorDashboardView' in request.session:
            del request.session['MentorDashboardView']
            del request.session['dashbordId']
        try:
            UserTypes.objects.get(type=request.session['user_type'])
        except:
            return redirect(reverse('user:logout'))
        user_type = request.session['user_type']
        if UserTypes.objects.get(type=user_type) in request.user.userType.all():
            if 'company_id' not in request.session:
                request.session['company_id'] = None
            if user_type == "Admin":
                return render(request, self.template_name)
            elif user_type == "Mentor":
                data = mentor_dashboard(request.user, user_type, request.session['timezone'])
                return render(request, 'mentor/dashboard.html', data)
            elif request.session['user_type'] == "ProgramManager":
                # if user_profile_assessment(request.user) > 0 and not request.user.profile_assest_enable:
                return redirect(reverse('program_manager:manage'))
                # else:
                    # user_channel = UserChannel.objects.filter(
                        # user=request.user, Channel__is_active=True, Channel__is_delete=False).first()
                    # if user_channel:
                        # return redirect(reverse('content:Channel_content', kwargs={"Channel": user_channel.Channel.pk}))
                    # return redirect(reverse('content:user-content'))
            elif request.session['user_type'] == "Learner":
                if request.user.email == "":
                    return render(request, 'info.html')
                return redirect(reverse('user:userdashboard')) 
            return redirect(reverse('user:logout'))
        return redirect(reverse('user:logout'))


@login_required
def MentorDashboardForAdmin(request, pk):
    if UserTypes.objects.get(type=request.session['user_type']) in request.user.userType.all():
        request.session["MentorDashboardView"] = True
        StrPk = str(pk)
        request.session["dashbordId"] = StrPk
        uuidpk = uuid.UUID(StrPk).hex
        user = User.objects.get(id=uuidpk)
        data = mentor_dashboard(user, "Mentor", request.session['timezone'])
        print(data, "MentorDashboardView")
        return render(request, 'mentor/dashboard.html', data)


@login_required
def UsersDashboardForAdmin(request, pk):
    if UserTypes.objects.get(type=request.session['user_type']) in request.user.userType.all():
        request.session["UserDashboardView"] = True
        StrPk = str(pk)
        request.session["dashbordId"] = StrPk
        uuidpk = uuid.UUID(StrPk).hex
        user = User.objects.get(id=uuidpk)
        data = user_dashboard(user, "Learner")
        print(data, "UserDashboardView")
        return render(request, 'users/user_dashboard.html', data)
        # return render(request, 'Dashboard/dashboard.html')


@method_decorator(login_required, name='dispatch')
class UserDashBoard(TemplateView):
    '''
       Redirect to the User DashBorad Page.
    '''
    content_type = 'text/html'
    template_name = "users/user_dashboard.html"

    def get(self, request):

        try:
            UserTypes.objects.get(type=request.session['user_type'])
        except:
            return redirect(reverse('user:logout'))
        if not request.session.get('company_id'):
            request.session['company_id'] = None

        if UserTypes.objects.get(type=request.session['user_type']) in request.user.userType.all():
            if request.session['user_type'] == "Admin":
                return render(request, self.template_name)
            elif request.session['user_type'] == "Mentor":
                print("User profile assessment", user_profile_assessment(request.user))
                if user_profile_assessment(request.user) > 0:
                    data = mentor_dashboard(request.user, "Mentor", request.session['timezone'])
                    return render(request, 'mentor/dashboard.html', data)
                else:
                    user_channel = UserChannel.objects.filter(
                        user=request.user, Channel__is_active=True, Channel__is_delete=False).first()
                    print(user_channel)
                    if user_channel:
                        data = mentor_dashboard(request.user, "Mentor", request.session['timezone'])
                        # return redirect(reverse('content:Channel_content', kwargs={"Channel": user_channel.Channel.pk}))
                        return render(request, 'mentor/dashboard.html', data)
                    data = mentor_dashboard(request.user, "Mentor", request.session['timezone'])
                    return render(request, 'mentor/dashboard.html', data)
            elif request.session['user_type'] == "ProgramManager":
                return redirect(reverse('program_manager:manage'))
            elif request.session['user_type'] == "Learner":
                if request.user.email == "":
                    return render(request, 'info.html')
                data = user_dashboard(request.user, request.session['user_type'], request.session.get('timezone', None))
                return render(request, 'users/user_dashboard.html', data)
            return redirect(reverse('user:logout'))
        return redirect(reverse('user:logout'))


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CreateAdmin(CreateView):
    '''
        Redirect to Create-Admin page.
    '''
    model = User
    form_class = CustomAdminCreationForm
    success_url = reverse_lazy('user:admin_list')
    template_name = "users/create_user.html"

    def form_valid(self, form):
        company_id = self.request.POST.getlist('company')
        f = form.save()
        for i in self.request.POST.getlist('userType'):
            f.userType.add(i)
        f.save()
        # user_type = [type.type for type in f.userType.all()]
        # user_company_data(self.request.user, user_type)
        # subject = "Welcome to Growatpace"
        # email_template_name = "email/register_mail.txt"

        # c = {
        #     "email": f.email,
        #     'domain': 'growatpace.com',
        #     'site_name': 'Growatpace',
        #     "uid": urlsafe_base64_encode(force_bytes(f.pk)),
        #     "user": f,
        #     'token': default_token_generator.make_token(f),
        #     'protocol': 'https',
        #     'password': self.request.POST['password1']
        # }
        # email = render_to_string(email_template_name, c)
        # try:
        #     # sendVerificationMail(user, user.email)
        #     send_mail(subject, email, 'info@growatpace.com', [f.email], fail_silently=False)
        # except BadHeaderError:
        #     return HttpResponse('Invalid header found.')
        if not company_id:
            company = None
        else:
            for id in company_id:
                company = Company.objects.get(pk=id)
                f.company.add(company)
                UserCompany.objects.create(user=f, company=company)
        NotificationAndPoints(user=f, title="registration")
        return super(CreateAdmin, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class AdminList(ListView):
    '''
        Render all the admins.
    '''
    template_name = "users/user_list.html"

    def get(self, request):
        user = AdminUser.objects.all()
        self.request.session['last_url'] = request.path
        context = {
            "users": user
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class MentorList(ListView):
    '''
        Render all the Mentors.
    '''
    template_name = "users/user_list.html"

    def get(self, request):
        user = Mentor.objects.all()
        self.request.session['last_url'] = request.path
        context = {
            "users": user
        }
        return render(request, self.template_name, context)


#     def get_queryset(self):
#         return self.model.objects.filter(is_active=False, is_delete=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class ContentCreaterList(ListView):
    '''
        Render all the ProgramManager.
    '''
    template_name = "users/user_list.html"

    def get(self, request):
        user = ProgramManager.objects.all()
        self.request.session['last_url'] = request.path
        context = {
            "users": user
        }
        return render(request, self.template_name, context)
#     def get_queryset(self):
#         return self.model.objects.filter(is_active=False, is_delete=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CreateUser(CreateView):
    '''
       Redirect to the Creat-User Page.
    '''
    model = Learner
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('user:user-list')
    template_name = "users/create_user.html"

    def form_valid(self, form):
        company_id = self.request.POST.getlist('company')
        type = UserTypes.objects.get(type="Learner")
        f = form.save()
        f.username = f.username
        f.userType.add(type.id)
        f.save()
        # user_type = [type.type for type in f.userType.all()]
        # user_company_data(self.request.user, user_type)
        register_email(f, self.request.POST['password1'])
        if not company_id:
            company = None
        else:
            for id in company_id:
                company = Company.objects.get(pk=id)
                f.company.add(company)
                UserCompany.objects.create(user=f, company=company)
        return super(CreateUser, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class CreateUsersFromCSV(View):
    '''
       Redirect to the Create-User Page where admin can upload bulk user.
    '''

    def get(self, request):
        return render(request, "users/create-bulk-users.html")

    def post(self, request, *args, **kwargs):
        if request.session['user_type'] == 'Admin':
            comapny = Company.objects.get(pk=request.POST['company_id'])
        else:
            comapny = Company.objects.get(pk=request.session['company_id'])
        is_marketplace = update_boolean(self.request.GET.get('marketplace_user'))
        file = request.FILES['file']
        decoded_file = file.read().decode('utf-8').splitlines()
        decoded_file = decoded_file[1:]
        print(decoded_file)
        missing_details_user = []

        try:
            reader = csv.reader(decoded_file)
            exist_user_list = []
            uploaded_user = 0
            for data in reader:
                if not User.objects.filter(email__iexact=data[3]).exists():
                    try:
                        country_code = data[5] if '+' in data[5] else '+'+data[5]
                        user = User.objects.create(first_name=data[0], last_name=data[1], username=data[2],
                                                        email=data[3], phone=country_code+data[6], address=data[7], city=data[8], state=data[9], country=data[10])
                        user.company.add(comapny)
                        user_type = UserTypes.objects.get(type=data[4])
                        user.userType.add(user_type)
                        password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
                        print(password)
                        user.set_password(password)
                        user.save()
                        uploaded_user = uploaded_user + 1
                        # if is_marketplace:
                        #     marketplace_user_email(user, password)
                    except Exception:
                        missing_details_user.append(data[3])
                else:
                    exist_user_list.append(data[3])
            exist_mail = ", ".join(exist_user_list)
            missing_details_user_email = ", ".join(missing_details_user)
            message = f"Users uploaded successfully!"
            if exist_mail or missing_details_user_email:
                message = f"{uploaded_user} users are uploaded successfully, and {exist_mail}, {missing_details_user_email} emails are already exist or the information is incorrect"
                if is_marketplace:
                    message = f"{uploaded_user} users are uploaded successfully and the details will be sent to you by email."
                    send_missing_existing_users(request.user.get_full_name(), request.user.email, missing_details_user_email, exist_mail)
            messages.success(request, message)

        except Exception:
            messages.error(request, "Invalid csv file or data format incorrect")
        if request.session['user_type'] == "ProgramManager" and not is_marketplace:
            return redirect(reverse('program_manager:security'))
        elif is_marketplace:
            return redirect(reverse('program_manager:marketplace'))
        return redirect('user:create-bulk-user')


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class ActiveUserList(ListView):
    '''
        Render All the Users.
    '''
    model = Learner
    context_object_name = "users"
    template_name = "users/user_list.html"

    def get_queryset(self):
        if 'UserDashboardView' in self.request.session:
            del self.request.session['UserDashboardView']
            del self.request.session['dashbordId']
        return Learner.objects.filter(is_active=True, is_delete=False, is_archive=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class InactiveUserList(ListView):
    '''
        Render All the Users.
    '''
    model = Learner
    context_object_name = "users"
    template_name = "users/user_list.html"

    def get_queryset(self):
        return Learner.objects.filter(is_active=False, is_delete=False)

# def update_phone(request):
#     if request.method == "POST":
#         phone = request.POST['phone']
#         request.session['phone'] = phone
#         if not '+' in phone:
#             return JsonResponse({
#                 "message": "you have entered incorrect country code or phone number"
#             })
#         user = User.objects.filter(id=request.POST['id']).first()
#         if User.objects.filter(phone__iexact=request.POST['phone']).exists():
#             return JsonResponse({
#                 "message": "Phone already exist",
#                 "success": False
#             })
#         if user:
#             otp = str(random.randint(100000, 999999))
#             if user_profile := Profile.objects.filter(user=user).first():
#                 user_profile.otp = otp
#                 user_profile.save()
#             else:
#                 user_profile = Profile.objects.create(user=user, otp=otp)
#             vonage_sms_otp_sender(None, otp, phone)
#             return JsonResponse({
#                 "message": "Please check your phone for otp",
#                 "success": True
#             })
#         return JsonResponse({
#             "message": "User Not Found",
#             "success": False
#         })

def update_email(request):
    if request.method == "POST":
        email = request.POST['email']
        request.session['email'] = email
        user = User.objects.filter(id=request.POST['id']).first()
        if User.objects.filter(email=request.POST['email']).exists():
            return JsonResponse({
                "message": "Email already exist",
                "success": False
            })
        elif user:
            otp = str(random.randint(100000, 999999))
            if user_profile := Profile.objects.filter(user=user).first():
                user_profile.otp = otp
                user_profile.save()
            else:
                user_profile = Profile.objects.create(user=user, otp=otp)
            send_email_otp(email, otp)
            return JsonResponse({
                "message": "Please check your email for otp",
                "success": True
            })
        return JsonResponse({
            "message": "User Not Found",
            "success": False
        })

def update_phone(request):
    if request.method == "POST":
        phone = request.POST['phone']
        request.session['phone'] = phone
        if not '+' in phone:
            return JsonResponse({
                "message": "You have entered incorrect country code or phone number"
            })
        user = User.objects.filter(id=request.POST['id']).first()
        if User.objects.filter(phone__iexact=request.POST['phone']).exists():
            return JsonResponse({
                "message": "Phone number already exist",
                "success": False
            })
        if user:
            otp = str(random.randint(100000, 999999))
            if user_profile := Profile.objects.filter(user=user).first():
                user_profile.otp = otp
                user_profile.save()
            else:
                user_profile = Profile.objects.create(user=user, otp=otp)
            vonage_sms_otp_sender(None, otp, phone)
            return JsonResponse({
                "message": "Please check your phone for otp",
                "success": True
            })
        return JsonResponse({
            "message": "User Not Found",
            "success": False
        })
        
def verify_phone_otp(request):
    if request.method == "POST":
        otp = request.POST['otp']
        user = User.objects.filter(id=request.POST['id']).first()
        if user:
            user_profile = Profile.objects.filter(user=user).first()
            if user_profile.otp == otp:
                UserPhoneChangeRecord.objects.create(user=user, old_phone=str(user.phone), current_phone=request.session['phone'])
                user.phone = request.session['phone']
                user.save()
                return JsonResponse({
                    "message": "Phone updated successfully.",
                    "success": True
                })
            return JsonResponse({
                "message": "OTP verification failed.",
                "success": False
            })
        return JsonResponse({
            "message": "User Not Found.",
            "success": False
        })    

def verify_email_otp(request):
    if request.method == "POST":
        otp = request.POST['otp']
        user = User.objects.filter(id=request.POST['id']).first()
        if user:
            user_profile = Profile.objects.filter(user=user).first()
            if user_profile.otp == otp:
                UserEmailChangeRecord.objects.create(user=user, old_email=user.email, current_email=request.session['email'])
                user.email = request.session['email']
                user.save()
                return JsonResponse({
                    "message": "Email updated successfully.",
                    "success": True
                })
            return JsonResponse({
                "message": "OTP verification failed.",
                "success": False
            })
        return JsonResponse({
            "message": "User Not Found.",
            "success": False
        })
                    

@method_decorator(login_required, name='dispatch')
class UserProfile(View):
    '''
        Render individual User.
    '''

    template_name = "users/user-profile.html"

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['pk'])
            # user_type = request.GET.get('user_type') or request.session['user_type']
            # user_types = user.userType.all()
            user_type_list = []
            if self.request.session['company_id'] != "null":
                company_list = user_company(user, self.request.session['company_id'])
            else:
                company_list = user_company(user)
            # user_profile_assest = []
            # for user_type in user_types:
            # user_type_list.append(user_type)
            user_profile_assest = UserProfileAssest.objects.filter(user=user)
            # user_profile_assest.append(profile_assest)

            print("profile_assest", user_profile_assest)
            for assest in user_profile_assest:
                # print("question", assest.assest_question.question_for)
                user_type = assest.assest_question.question_for
                if user_type not in user_type_list:
                    user_type_list.append(user_type)
                # print("user_type", user_type_list)

            #     for ques in assest:
            #         print("ques", ques.assest_question.question)

            # if "," in user_type:
            # user_type = user_type.split(",")[0]
            # user_profile_assest = UserProfileAssest.objects.filter(
            # user=user, assest_question__question_for=user_type)
            badges = UserBadgeDetails.objects.filter(user=request.user).last()
            try:
                total_points = user.user_earned_points.total_points
            except UserEarnedPoints.DoesNotExist:
                total_points = 0
            # lastbadgePoints = BadgeDetails.objects.all().first()
            badgePoints = BadgeDetails.objects.filter(points_required__gt=total_points)
            streak_count = userStreakCount(user)
            next_badge_points = total_points
            if badgePoints:
                next_badge_points = badgePoints.last().points_required

            # badges_points = []
            # for badge in badgePoints:
            #     # print("badgePoints", badge.points_required)
            #     if badge.points_required > total_points:
            #         badges_points.append(badge.points_required)
            # print("badgePoints", badges_points)
            # else:
            #     badges_points.append(total_points)
            # next_badge_points = badges_points
            if total_points != 0:
                percentage = (total_points * 100) / next_badge_points
            elif next_badge_points <= total_points:
                percentage = 0
            else:
                percentage = 100
            # print("percentage", percentage)
            StreakPoint = StreakPoints.objects.filter(duration_in_days__gte=streak_count)
            StreakPointsList = []
            daysList = []
            for points in StreakPoint:
                StreakPointsList.append(points.points)
                daysList.append(points.duration_in_days)
            print("daysloist", daysList)
            if StreakPointsList:
                points_for_streak = min(StreakPointsList, default=1)
            else:
                points_for_streak = 0
            if daysList:
                days_for_points = min(daysList, default=1)
            else:
                days_for_points = 0
            if streak_count != 0 and days_for_points != 0:
                streakPercent = (streak_count * 100) / days_for_points
            elif streak_count == 0:
                streakPercent = 100
            else:
                streakPercent = 0
            streakPercent = (streak_count * 100) / days_for_points if days_for_points else 0
            streakActivity = lineChartData(request.user, request.session['user_type'], request.session['company_id'])
            # print("userstreakAllActivity", streakActivity)
            data = {
                "user": user,
                "company": company_list,
                "user_type_list": user_type_list,
                "user_profile_assest": user_profile_assest,
                "total_points": total_points,
                "badges": badges,
                "streak_count": streak_count,
                "next_badge_points": next_badge_points,
                "percentage": int(percentage),
                "points_for_streak": points_for_streak,
                "days_for_points": days_for_points,
                "streakPercent": int(streakPercent),
                "streakActivity": streakActivity,
                "user_id": str(request.user.id)

            }
            return render(request, self.template_name, data)
        except User.DoesNotExist:
            raise response.Http404

        user = User.objects.get(pk=request.user.pk)
        user_profile_assest = UserProfileAssest.objects.filter(user=user)
        if request.session['user_type'] != "Admin":
            user = User.objects.get(pk=request.user.pk)
        else:
            user = User.objects.get(pk=self.kwargs['pk'])
        # try:
        #     user = User.objects.get(pk=self.kwargs['pk'])
        #     user_profile_assest = UserProfileAssest.objects.filter(user=user)
        #     return render(request, self.template_name, {"user": user, "user_profile_assest": user_profile_assest})
        # except User.DoesNotExist:
        #     raise response.Http404

        user_profile_assest = UserProfileAssest.objects.filter(user=user)
        return render(request, self.template_name, {"user": user, "user_profile_assest": user_profile_assest})


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class DeleteUser(View):
    '''
        Delete User from database.
    '''

    def get(self, request, pk):
        User.objects.filter(pk=pk).update(is_active=False, is_delete=True)
        return redirect(reverse('user:user-list'))


class BulkIncativeArchieveUser(View):
    def post(self, request):
        action = request.POST['action']
        user_list = request.POST.getlist('user_id')
        user_obj = User.objects.filter(pk__in=user_list)
        if action == "InActive":
            for user_id in user_list:
                User.objects.filter(pk=user_id).update(is_active=False)
        elif action == "Active":
            for user_id in user_list:
                User.objects.filter(pk=user_id).update(is_active=True, is_delete=False)
        elif action == "Archive":
            print("user_list", user_list)
            for user_id in user_list:
                User.objects.filter(pk=user_id).update(is_archive=True, is_active=False, is_delete=False)
        elif action == "wp_enable":
            print("user_list", user_list)
            for user_id in user_list:
                userObj = User.objects.get(pk=user_id)
                if userObj.is_whatsapp_enable == False:
                    userObj.is_whatsapp_enable = True
                    userObj.save()
        elif action == "wp_disable":
            print("user_list", user_list)
            for user_id in user_list:
                userObj = User.objects.get(pk=user_id)
                if userObj.is_whatsapp_enable == True:
                    userObj.is_whatsapp_enable = False
                    userObj.save()

        return redirect(reverse('user:user-list'))


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class UpdateUser(UpdateView):
    '''
        Update User to database.
    '''
    model = User
    form_class = CustomUserUpdateForm
    template_name = "users/create_user.html"

    def form_valid(self, form):
        f = form.save()
        print(f)
        if self.request.POST['company']:
            company = Company.objects.get(pk=self.request.POST['company'])
        else:
            company = None
        user_company = UserCompany.objects.filter(user=f)
        if user_company.count() > 0:
            user_company.update(company=company)
        else:
            UserCompany.objects.create(user=f, company=company)
        # user_type = [type.type for type in f.userType.all()]
        # user_company_data(self.request.user, user_type)
        return super(UpdateUser, self).form_valid(form)

    def get_success_url(self):
        if 'last_url' in self.request.session and "/user-admin/list/" == self.request.session['last_url']:
            return reverse('user:admin_list')
        elif 'last_url' in self.request.session and "/mentor/list/" == self.request.session['last_url']:
            return reverse('user:mentor_list')
        elif 'last_url' in self.request.session and "/content-creater/list/" == self.request.session['last_url']:
            return reverse('user:content_creator_list')
        else:
            return reverse('user:user-list')


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CreateCompany(CreateView):
    '''
        Redirect to Create Company Page where admin can register a company.
    '''
    models = Company
    form_class = CompanyCreationFrom
    success_url = reverse_lazy('user:company_list')
    template_name = "users/create_company.html"


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CompanyList(ListView):
    '''
       Render the list of comapnies.
    '''
    model = Company
    context_object_name = "company"
    template_name = "users/company_list.html"

    def get_queryset(self):
        return Company.objects.filter(is_delete=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class DeleteCompany(View):
    def get(self, request, **kwargs):
        role = self.kwargs['pk']
        Company.objects.filter(pk=role).update(is_delete=True)
        return redirect(reverse_lazy('user:company_list'))


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class UpdateCompany(UpdateView):
    '''
        Update Company.
    '''
    model = Company
    form_class = CompanyCreationFrom
    success_url = reverse_lazy('user:company_list')
    template_name = "users/create_company.html"


@method_decorator(login_required, name="dispatch")
@method_decorator(admin_only, name="dispatch")
class CompanyUser(ListView):
    model = Learner
    context_object_name = "users"
    template_name = "users/user_list.html"

    def get_queryset(self):
        return Learner.objects.filter(company=self.kwargs['company'], is_delete=False)


@method_decorator(login_required, name='dispatch')
class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    url = '/login/'

    def get(self, request, *args, **kwargs):
        user_visit = UserVisit.objects.filter(user=request.user).last()
        UserEngagement.objects.create(user=request.user, login_time=user_visit.timestamp)
        auth_logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class AlloteChannelToUser(View):
    template_name = "users/allote_channel_to_user.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        channel = Channel.objects.get(pk=request.POST['channel'])
        userlist = request.POST.getlist('user')
        try:
            is_wp_enable = request.POST['is_wp_enable']
        except:
            is_wp_enable = False
        print("is_wp_enable", is_wp_enable)
        for user in userlist:
            user = User.objects.get(pk=user)
            user_channel = UserChannel.objects.filter(user=user, Channel=channel)
            if not user_channel.exists():
                UserChannel.objects.create(Channel=channel, user=user, status="Joined",
                                           alloted_by=request.user, is_alloted=True)
                add_user_to_company(request.user, channel.company)
                context = {
                    "screen": "ProgramJourney",
                    "navigationPayload": {
                        "courseId": str(channel.id)
                    }
                }
                send_push_notification(user, channel.title, f"You're enrolled in {channel.title}", context)
                if channel.whatsapp_notification_required and (user.phone and is_wp_enable):
                    journey_enrolment(user, channel)
                else:
                    print("phone does not exist")
                if channel.is_community_required:
                    add_member_to_space(channel, user)
            elif user_channel.filter(status="removed"):
                user_channel.update(status="Joined")
                if channel.whatsapp_notification_required and (user.phone and is_wp_enable):
                    journey_enrolment(user, channel)
                else:
                    print("phone does not exist")
            else:
                messages.error(request, "Journey already alloted")
                return render(request, self.template_name)
        return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CreateRole(CreateView, ListView):
    model = UserRoles
    form_class = CreateRoleForm
    success_url = reverse_lazy('user:create_role')
    template_name = "users/add_roles.html"
    context_object_name = "roles"

    def get_queryset(self):
        return UserRoles.objects.filter(is_delete=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class UpdateRole(UpdateView):
    model = UserRoles
    form_class = CreateRoleForm
    success_url = reverse_lazy('user:create_role')
    template_name = "users/add_roles.html"


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class DeleteRole(View):
    def get(self, request, **kwargs):
        role = self.kwargs['pk']
        UserRoles.objects.filter(pk=role).update(is_delete=True)
        return redirect(reverse_lazy('user:create_role'))


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    # sendVerificationMail(user, user.email)
                    subject = "Password Reset Requested"
                    email_template_name = "email/password_reset_email.txt"

                    c = {
                        "email": user.email,
                        'domain': DOMAIN,
                        'site_name': SITE_NAME,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': PROTOCOL,
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        # sendVerificationMail(user, user.email)
                        send_mail(subject, email, 'info@growatpace.com', [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect("/password_reset/done/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="auth/password_reset.html",
                  context={"password_reset_form": password_reset_form})


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class UserReport(View):
    def get(self, request, pk):
        get_user = Learner.objects.get(pk=pk)
        return render(request, 'users/report.html', {'user': get_user})


@method_decorator(login_required, name='dispatch')
class EditProfile(UpdateView):
    model = User
    form_class = UserProfileUpdateForm
    template_name = "users/edit-profile.html"

    def get_form_kwargs(self):
        """
        Passes the request object to the form class
        """
        kwargs = super(EditProfile, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('user:user-profile', kwargs={'pk': self.request.user.pk})
    # def form_valid(self, form):
    #     print(self.request.POST['industry'])
    #     # f = form.save()

    #     # return super(EditProfile, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
class AdvanceProfile(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'mentor/advance_profile.html')


@method_decorator(login_required, name='dispatch')
class AdvanceProfilePreview(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'mentor/advance_profile_preview.html')

@method_decorator(login_required, name='dispatch')
class CompleteProfileAssessment(View):

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token', None)
        if token:
            user_id = jwt_decoding(token)
            print("user_id: ", user_id)
            print("request_id: ", request.user.id)
            if str(request.user.id) != str(user_id):
                return redirect('user:logout')
        profile_assest = ProfileAssestQuestion.objects.filter(
            question_for=request.session['user_type'], is_active=True, is_delete=False)
        # if profile_assest.filter()

        return render(request, 'mentor/profile_assessment.html', {'profile_assest': profile_assest})

    def post(self, request, *args, **kwargs):
        question = request.POST.getlist('question[]')
        response = request.POST.getlist('response[]')
        for x in range(len(question)):
            profile_question = ProfileAssestQuestion.objects.get(pk=question[x])
            UserProfileAssest.objects.create(user=request.user, assest_question=profile_question,
                                             response=response[x], question_for=profile_question.question_for)
        user_code = Coupon.objects.filter(code=request.user.coupon_code).first()
        if not user_code:
            return render(request, "assessment/assessment-thank-you.html")
        journey = Channel.objects.get(id=user_code.journey, parent_id=None)
        subject = journey.title
        email_template_name = "email/assessment_complete.txt"

        c = {
            'name': request.user.first_name,

            "user_role": request.session['user_type'],
            'space_id': "",
            "journey_name": journey.title,
            "program_team_1": f"{journey.program_team_1.first_name} {journey.program_team_1.last_name}",
            "program_team_2": f"{journey.program_team_2.first_name} {journey.program_team_2.last_name}",
            "program_team_email": journey.program_team_email,
            "closure_date": journey.closure_date
        }
        email = render_to_string(email_template_name, c)
        try:
            # sendVerificationMail(user, user.email)
            send_mail(subject, email, INFO_CONTACT_EMAIL, [request.user.email], fail_silently=False)
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        # return redirect(reverse('user:user-dashboard'))
        return render(request, "assessment/assessment-thank-you.html",
                      {"program_team": f"{journey.program_team_1.first_name} {journey.program_team_1.last_name}",
                       "program_team_email": journey.program_team_email})


@method_decorator(login_required, name='dispatch')
class EditProfileAssessment(View):

    def get(self, request, *args, **kwargs):
        profile_assest = UserProfileAssest.objects.filter(
            user=request.user, assest_question__question_for=request.session['user_type'])
        for assest in profile_assest:
            print(f"options: {assest.assest_question.options}")
            print(type(assest.assest_question.options))
        return render(request, 'mentor/edit-profile-assessment.html', {'profile_assest': profile_assest})

    def post(self, request, *args, **kwargs):
        question = request.POST.getlist('question[]')
        response = request.POST.getlist('response[]')
        for x in range(len(question)):
            profile_question = ProfileAssestQuestion.objects.get(pk=question[x])
            UserProfileAssest.objects.filter(
                user=request.user, assest_question=profile_question).update(response=response[x])
        # subject = "3rd ASEAN Mentorship Program 2022 (9 March 2022 – 8 June 2022)"
        # email_template_name = "email/assessment_complete.txt"

        # c = {
        #     'name': request.user.first_name,
        # }
        # email = render_to_string(email_template_name, c)
        # try:
        #     # sendVerificationMail(user, user.email)
        #     send_mail(subject, email, INFO_CONTACT_EMAIL, [request.user.email], fail_silently=False)
        # except BadHeaderError:
        #     return HttpResponse('Invalid header found.')
        # return redirect(reverse('user:user-dashboard'))
        return render(request, "assessment/assessment-thank-you.html")


@method_decorator(login_required, name='dispatch')
class Calendar(View):
    def get(self, request):
        company_list = request.user.company.all()
        if request.session.get('company_id'):
            company_list = company_list.filter(pk=request.session.get('company_id'))
        company_journey = company_journeys(
            request.session['user_type'], request.user, request.session.get('company_id'))
        learners = AssignMentorToUser.objects.filter(
            mentor=request.user, journey__in=company_journey, is_assign=True, is_revoked=False).values('user')
        print("learener", learners, company_journey)
        mentor_calendar = mentorCalendar.objects.filter(Q(slot_status='Available') | Q(
            participants__in=learners), mentor=request.user, is_cancel=False)
        calendar_data = []
        backgroundColor = "#33FF4F"
        borderColor = "#33FF4F"

        for mentor_calendar in mentor_calendar:
            title = mentor_calendar.title
            backgroundColor = "#33FF4F"
            borderColor = "#33FF4F"
            if mentor_calendar.slot_status == "Booked":
                backgroundColor = "#3379FF"
                borderColor = "#3379FF"
                title = f"{mentor_calendar.title}- Click here To start "

            calendar_data.append({
                "id": mentor_calendar.id,
                "title": title,
                "start": local_time(mentor_calendar.start_time).isoformat(),
                "end": local_time(mentor_calendar.end_time).isoformat(),
                "allDay": False,
                "backgroundColor": backgroundColor,
                "borderColor": borderColor,
                "url": mentor_calendar.url,
                "type": "mentor_calendar",
                "session_type": "Mentor Session"
            })
        all_mettings = Collabarate.objects.filter(Q(speaker=request.user) | Q(
            company__in=company_list) | Q(participants__in=[request.user]), is_cancel=False)

        Collabarate_data = [
            {"id": collabarate.id, "title": f"{collabarate.title}-{collabarate.type}- Click here To start ",
             "start": collabarate.start_time.strftime("%Y-%m-%dT%H:%M:%S"), "end": collabarate.end_time.strftime(
                 "%Y-%m-%dT%H:%M:%S"), "allDay": False, "backgroundColor": '#3379FF', "borderColor": '#3379FF',
             "url": collabarate.custom_url, "type": "collabarate", "session_type": collabarate.type} for collabarate in
            all_mettings if collabarate.start_time is not None]

        calendar_data.extend(Collabarate_data)
        return render(request, "mentor/calendar.html", {"calendar_data": calendar_data})


@method_decorator(login_required, name='dispatch')
class UserCalendar(View):
    def get(self, request, pk=None):
        calendar_data = []
        backgroundColor = "#33FF4F"
        borderColor = "#33FF4F"
        if pk is None:
            if request.session.get('company_id'):
                company_list = request.user.company.filter(pk=request.session['company_id'])
            else:
                company_list = request.user.company.all()
            company_journey = company_journeys(
                request.session['user_type'], request.user, request.session.get('company_id'))
            mentor = AssignMentorToUser.objects.filter(
                user=request.user, journey__in=company_journey, is_assign=True, is_revoked=False).values('mentor')
            print("mentor", mentor)
            mentor_calendar = mentorCalendar.objects.filter(
                participants__in=[request.user], is_cancel=False, mentor__in=mentor)
            all_mettings = Collabarate.objects.filter(Q(participants__in=[request.user]) | Q(
                company__in=company_list), is_cancel=False)

        else:
            user = User.objects.get(id=pk)
            if request.session.get('company_id'):
                company_list = user.company.filter(pk=request.session['company_id'])
            else:
                company_list = user.company.all()
            company_journey = company_journeys(
                request.session['user_type'], request.user, request.session.get('company_id'))
            mentor = AssignMentorToUser.objects.filter(
                user=user, journey__in=company_journey, is_assign=True, is_revoked=False).values('mentor')
            print("mentor", mentor)
            mentor_calendar = mentorCalendar.objects.filter(
                participants__in=[user], is_cancel=False, mentor__in=mentor)
            all_mettings = Collabarate.objects.filter(Q(participants__in=[user]) | Q(
                company__in=company_list), is_cancel=False)

        for mentor_calendar in mentor_calendar:
            title = mentor_calendar.title
            if mentor_calendar.slot_status == "Booked":
                backgroundColor = "#3379FF"
                borderColor = "#3379FF"
                title = f"{mentor_calendar.title}- Click here To start "

            calendar_data.append({
                "id": mentor_calendar.id,
                "title": title,
                "start": local_time(mentor_calendar.start_time).isoformat(),
                "end": local_time(mentor_calendar.end_time).isoformat(),
                "allDay": False,
                "backgroundColor": backgroundColor,
                "borderColor": borderColor,
                "url": mentor_calendar.url,
                "type": "mentor_calendar",
                "session_type": "Mentor Session"
            })

        Collabarate_data = [
            {"id": collabarate.id, "title": f"{collabarate.title}-{collabarate.type}- Click here To start ",
             "start": local_time(collabarate.start_time).isoformat(),
             "end": local_time(collabarate.end_time).isoformat(
             ), "allDay": False, "backgroundColor": '#3379FF', "borderColor": '#3379FF',
             "url": collabarate.custom_url, "type": "collabarate", "session_type": collabarate.type} for collabarate
            in all_mettings if collabarate.start_time]

        calendar_data.extend(Collabarate_data)
        # print("caaa", calendar_data)
        return render(request, "users/user_calendar.html", {"calendar_data": calendar_data})


# def UserDeviceDetail(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')

#     device_type = ""
#     if request.user_agent.is_mobile:
#         device_type = "Mobile"
#     if request.user_agent.is_tablet:
#         device_type = "Tablet"
#     if request.user_agent.is_pc:
#         device_type = "PC"

#     device_type_family = request.user_agent.device.family
#     device_type_brand = request.user_agent.device.brand
#     device_type_model = request.user_agent.device.model
#     browser_type = request.user_agent.browser.family
#     browser_version = request.user_agent.browser.version_string
#     os_type = request.user_agent.os.family
#     os_version = request.user_agent.os.version_string
#     device = UserDeviceDetails(ip_address = ip, device_type=device_type, device_type_family=device_type_family, device_type_brand=device_type_brand, device_type_model=device_type_model,
#                                browser_type_family=browser_type, browser_version=browser_version, os_type=os_type, os_version=os_version)
#     device.save()

#     context = {
#         "ip": ip,
#         "device_type": device_type,
#         "browser_type": browser_type,
#         "browser_version": browser_version,
#         "os_type":os_type,
#         "os_version":os_version,
#         "device_type_family":device_type_family,
#         "device_type_brand":device_type_brand,
#         "device_type_model":device_type_model
#     }
#     # return device
#     return render(request, "users/deviceInfo.html", context)


@method_decorator(login_required, name='dispatch')
class ChatModule(View):
    def get(self, request, pk=None):
        all_rooms_list = []
        if pk is None:
            user = request.user
        else:
            user = User.objects.get(id=pk)
        all_rooms = AllRooms.objects.filter(Q(user1=user) | Q(
            user2=user) | Q(members__in=[user]), user1__is_active=True, user2__is_active=True, user1__is_delete=False, user2__is_delete=False)
        print("all_rooms line 1410", all_rooms)
        logged_user = user
        for rooms in all_rooms:
            if (rooms.type == 'OneToOne'):
                unread_msg = Chat.objects.filter(
                    Q(to_user=user) & Q(from_user=rooms.user2) | Q(to_user=user) & Q(
                        from_user=rooms.user1), ~Q(read_by__in=[user])).count()
                print("unread_msg", unread_msg)
                # if rooms.user1 and rooms.user2:
                all_rooms_list.append({
                    "type": rooms.type,
                    "username": rooms.user1.username,
                    "user1_avatar": rooms.user1.avatar,
                    "user2_avatar": rooms.user2.avatar,
                    "user1_full_name": rooms.user1.first_name + " " + rooms.user1.last_name,
                    "user2_full_name": rooms.user2.first_name + " " + rooms.user2.last_name,
                    "room_name": rooms.name,
                    "unread_msg": unread_msg

                })
            else:
                unread_msg = Chat.objects.filter(~Q(read_by__in=[user]) & ~Q(
                    from_user=user), room=rooms).count()
                all_rooms_list.append({
                    "type": rooms.type,
                    "group_name": rooms.group_name,
                    "group_avatar": rooms.group_image,
                    "room_name": rooms.name,
                    "unread_msg": unread_msg,
                    "members_count": rooms.members.count()
                })
        # all_group = Group.objects.filter(members__in=[request.user])
        # print("All group", all_group)
        # print(all_rooms_list)
        return render(request, "mentor/chat.html",
                      {"all_rooms": all_rooms_list, "room_name": "", 'logged_user': logged_user})


@method_decorator(login_required, name='dispatch')
class UserChatModule(View):
    def get(self, request, room_name):
        all_rooms = AllRooms.objects.filter(Q(user1=request.user) | Q(
            user2=request.user) | Q(members__in=[request.user]), user1__is_active=True, user2__is_active=True, user1__is_delete=False, user2__is_delete=False)
        print("line 1444")
        my_room = AllRooms.objects.get(name=room_name)
        # print("chat views file", all_rooms.values())
        # print(my_room.user2, my_room.user1)

        chats = Chat.objects.filter(
            Q(from_user=my_room.user1) & Q(to_user=my_room.user2) | Q(from_user=my_room.user2) & Q(
                to_user=my_room.user1) | Q(room=my_room)).order_by('timestamp')
        print(chats)
        chats.update(is_read=True)
        for chat in chats:
            chat.read_by.add(request.user)
            chat.save()
        # print(chats)
        logged_user = request.user
        all_rooms_list = []
        for rooms in all_rooms:
            if (rooms.type == 'OneToOne'):
                # unread_msg = Chat.objects.filter(Q(from_user=request.user) & Q(to_user=rooms.user2) | Q(from_user=request.user) & Q(
                #     to_user=rooms.user1), is_read=False).count()
                unread_msg = Chat.objects.filter(
                    Q(to_user=request.user) & Q(from_user=rooms.user2) | Q(to_user=request.user) & Q(
                        from_user=rooms.user1), ~Q(read_by__in=[request.user])).count()
                print("unread_msg", unread_msg)
                all_rooms_list.append({
                    "type": rooms.type,
                    "username": rooms.user1.username,
                    "user1_avatar": rooms.user1.avatar,
                    "user2_avatar": rooms.user2.avatar,
                    "user1_full_name": rooms.user1.first_name + " " + rooms.user1.last_name,
                    "user2_full_name": rooms.user2.first_name + " " + rooms.user2.last_name,
                    "room_name": rooms.name,
                    "unread_msg": unread_msg

                })
            else:
                unread_msg = Chat.objects.filter(~Q(read_by__in=[request.user]) & ~Q(
                    from_user=request.user), room=rooms).count()
                all_rooms_list.append({
                    "type": rooms.type,
                    "group_name": rooms.group_name,
                    "group_avatar": rooms.group_image,
                    "room_name": rooms.name,
                    "unread_msg": unread_msg,
                    "members_count": rooms.members.count()

                })
        if my_room.type == 'OneToOne':
            if (logged_user == my_room.user1):
                name = my_room.user2.first_name + " " + my_room.user2.last_name
            else:
                name = my_room.user1.first_name + " " + my_room.user1.last_name
        else:
            name = my_room.group_name
        # all_group = Group.objects.filter(members__in=[request.user])
        # print(all_rooms_list)
        context = {
            "name": name,
            "all_rooms": all_rooms_list,
            # "all_group": all_group,
            'room_name': room_name,
            'chats': chats,
            'logged_user': logged_user
        }
        return render(request, "mentor/chat.html", context)


@login_required
def user_chat_status(request):
    if request.method == "POST":
        print("logged_user", request.user.id)
        try:
            user = User.objects.get(pk=request.user.id)
        except User.DoesNotExist:
            return "User not found"
        print(user)
        if (request.POST['WebSocket'] == "connected"):
            user.user_status = True
            user.save()
            print("connected")
        else:
            print("disconnected")
            user.user_status = False
            user.save()
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class ProgramUserList(ListView):
    def get(self, request):
        # pool = Pool.objects.all()
        # try:
        #     company = UserCompany.objects.get(user=request.user)
        #     company = company.company
        # except:
        user = User.objects.get(pk=request.user.pk)
        context = registration_list(user)
        return render(request, "ProgramManager/user-list.html", context)

    def post(self, request):
        # print("manager", request.POST['user'])
        user = User.objects.get(pk=request.user.pk)
        filter_user = request.POST['user']
        filter_assessment = request.POST['assessment']
        filter_journey = request.POST['journey']
        context = registration_list(user, filter_user, filter_assessment, filter_journey)
        return render(request, "ProgramManager/user-list.html", context)


@method_decorator(login_required, name='dispatch')
class MatchingMentor(FormView):
    def get(self, request):
        return render(request, "mentor/matching-mentor.html", )

    def post(self, request):
        user_list = []
        validate = False
        poll_mentor_list = []
        journey = Channel.objects.get(pk=request.POST['journey'])
        company = Company.objects.get(pk=request.POST['company'])
        match_type = request.POST['match']

        pool = Pool.objects.get(pk=request.POST['pool'])

        if match_type == "Manual":
            user_channel = UserChannel.objects.filter(Channel=journey)
            pool_mentor = PoolMentor.objects.filter(pool=pool)

            poll_mentor_list_data = []
            for pool_mentor in pool_mentor:
                mentor = pool_mentor.mentor
                if UserTypes.objects.get(type="Mentor") in mentor.userType.all():
                    poll_mentor_list_data.append({
                        "name": mentor.first_name + " " + mentor.last_name,
                        "id": mentor.id,

                    })

            for user_channel in user_channel:
                new_pool_list = []

                for mentor in poll_mentor_list_data:
                    assign_check = AssignMentorToUser.objects.filter(
                        journey=journey, mentor_id=mentor['id'], user=user_channel.user)
                    new_pool_list.append({
                        "name": mentor['name'],
                        "id": mentor['id'],
                        "already_checked": assign_check.first().mentor.id if assign_check else ""
                    })

                if UserTypes.objects.get(type="Learner") in user_channel.user.userType.all():
                    user_list.append({
                        "user": user_channel.user,
                        "poll_mentor_list": new_pool_list
                    })
            context = {
                "selected_journey": journey,
                "selected_pool": pool,
                "match_type": match_type,
                "user_list": user_list
            }
        else:
            data = matching_mentor(journey, pool, company, request.user)
            context = {
                "selected_journey": journey,
                "selected_pool": pool,
                "match_type": match_type,
                "user_list": data
            }
        return render(request, "mentor/matching-mentor.html", context)


@login_required
def company_journey(request):
    journeys = Channel.objects.filter(~Q(channel_type='SelfPaced'), company=request.GET.get(
        'company'), parent_id=None, is_active=True, is_delete=False)
    all_journey = [{"id": journey.id, "title": journey.title} for journey in journeys]
    # return JsonResponse({"all_journey": all_journey})
    return render(request, "partials/journey_list.html", {"all_journey": all_journey})


@login_required
def journey_pool(request):
    pools = Pool.objects.filter(journey=request.GET.get('journey'), is_active=True)
    all_pool = [{"id": pool.id, "name": pool.name} for pool in pools]
    # return JsonResponse({"all_pool": all_pool})
    return render(request, "partials/pool_list.html", {"all_pool": all_pool})


@method_decorator(login_required, name='dispatch')
class MatchingMentorPreview(View):
    def post(self, request):
        res = ast.literal_eval(request.POST['user'])
        journey = Channel.objects.get(pk=res['journey_id'])
        company = Company.objects.get(pk=res['company_id'])
        # match_config = MatchQuesConfig.objects.filter(journey=journey, company=company).first()
        # match_question = MatchQuestion.objects.filter(ques_config=match_config)
        user = User.objects.get(pk=res['user'])
        # question_list = []
        # for question in match_question:

        #     user_profile_question = UserProfileAssest.objects.filter(
        #         user=user, assest_question_id=question.learner_ques.pk).first()
        #     if user_profile_question:
        #         question_list.append({
        #             "question": user_profile_question.assest_question.question,
        #             "response": user_profile_question.response,
        #             "is_dependent": question.is_dependent
        #         })

        #         if question.dependent_option == user_profile_question.response:
        #             print(question.dependent_learner.pk)
        #             user_profile_question = UserProfileAssest.objects.filter(
        #                 user=user, assest_question_id=question.dependent_learner.pk).first()
        #             if user_profile_question:
        #                 question_list.append({
        #                     "question": user_profile_question.assest_question.question,
        #                     "response": user_profile_question.response,
        #                     "is_dependent": question.is_dependent
        #                 })

        # criteria_1 = []
        # criteria_2 = []
        criteria = []
        for poll in res['poll_mentor_list']:
            mentor = Mentor.objects.get(pk=poll['id'])
            if not poll['already_checked']:
                # user_profile_assest = UserProfileAssest.objects.get(id=poll['question_id'])
                print(f"profile_image: {avatar(mentor)}")
                criteria.append({
                    "mentor": mentor,
                    "match_percentage": poll['match_percentage'],
                    "profile_question": '',
                    "avatar": avatar(mentor)
                })

        # for poll in res['poll_mentor_2']:
        #     mentor = Mentor.objects.get(pk=poll['id'])
        #     if not poll['already_checked']:
        #         user_profile_assest = UserProfileAssest.objects.get(id=poll['question_id'])
        #         criteria_2.append({
        #             "mentor": mentor,
        #             "match_percentage": poll['match_percentage'],
        #             "profile_question": user_profile_assest
        #         })

        # for poll in res['poll_mentor_3']:
        #     mentor = Mentor.objects.get(pk=poll['id'])
        #     if not poll['already_checked']:
        #         user_profile_assest = UserProfileAssest.objects.get(id=poll['question_id'])
        #         criteria_3.append({
        #             "mentor": mentor,
        #             "match_percentage": poll['match_percentage'],
        #             "profile_question": user_profile_assest
        #         })
        print("poll: ", poll)
        print("criteria: ",criteria)
        context = {
            "user": user,
            "company": company.name,
            "match_question": [],
            "criteria_1": criteria,
            "criteria_2": [],
            "criteria_3": []
        }
        print(context)

        return render(request, "mentor/matching-assign-preview.html", context)


@method_decorator(login_required, name='dispatch')
class assign_mentor(View):
    def post(self, request):
        user = request.POST['user']
        mentor = request.POST['mentor']
        journey = request.POST['journey']
        journey = Channel.objects.get(pk=request.POST['journey'])
        user = Learner.objects.get(pk=user)
        mentor = Mentor.objects.get(pk=mentor)
        ratio = menter_mentee_capacity(company=journey.company, user=user)
        assign_menter = AssignMentorToUser.objects.filter(mentor=mentor, journey=journey).count()
        if ratio:
            max_mentor = ratio.max_mentor
            if max_mentor <= assign_menter:
                return HttpResponse("Mentor has reached the total mentee capacity")
        assign_menter = AssignMentorToUser.objects.filter(user=user, mentor=mentor, journey=journey)
        if assign_menter.count() > 0:
            return HttpResponse("Already Assigned")
        assign_menter_check = AssignMentorToUser.objects.filter(user=user, journey=journey)
        if assign_menter_check.count() > 0:
            assign_menter_check.update(is_assign=False, is_revoked=True, revoked_by=request.user)
        AssignMentorToUser.objects.create(user=user, mentor=mentor, journey=journey, assign_by=request.user)
        return HttpResponse("Assigned")


@method_decorator(login_required, name='dispatch')
class ManualAssign(View):
    def get(self, request):
        return render(request, "mentor/manual_assign.html")

    def post(self, request):
        user = request.POST['user']
        mentor = request.POST['mentor']
        journey = request.POST['journey']
        journey = Channel.objects.get(pk=request.POST['journey'])
        user = Learner.objects.get(pk=user)
        mentor = Mentor.objects.get(pk=mentor)
        if user == mentor:
            messages.error(request, "Mentor and Learner can not be same")
            return redirect(reverse_lazy('user:manual_assign'))
        assign_menter = AssignMentorToUser.objects.filter(user=user, mentor=mentor, journey=journey)
        if assign_menter.count() > 0:
            messages.error(request, "Already Assigned ")
            return redirect(reverse_lazy('user:manual_assign'))
        else:
            assign_menter_check = AssignMentorToUser.objects.filter(user=user, journey=journey)
            if assign_menter_check.count() > 0:
                assign_menter_check.update(is_assign=False, is_revoked=True, revoked_by=request.user)
            AssignMentorToUser.objects.create(user=user, mentor=mentor, journey=journey, assign_by=request.user)
            messages.success(request, "Assigned ")
            return redirect(reverse_lazy('user:manual_assign'))


@method_decorator(login_required, name='dispatch')
class mentor_users(ListView):
    model = AssignMentorToUser
    context_object_name = "mentor_user"
    template_name = "mentor/student_list.html"

    def get_queryset(self):
        company_journey = company_journeys(
            self.request.session['user_type'], self.request.user, self.request.session.get('company_id'))
        return AssignMentorToUser.objects.filter(mentor=self.request.user, is_revoked=False, is_assign=True, journey__in=company_journey)


@method_decorator(login_required, name='dispatch')
class mentor_users_details(View):
    def get(self, request, *args, **kwargs):
        user = User.objects.get(pk=self.kwargs['user_id'])
        print("to_user_id", user.id)
        print("logged_user", request.user.id)
        room = get_chat_room(user, request.user)
        room = Room.objects.get(name=room)

        chats = Chat.objects.filter(
            Q(from_user=room.user1) & Q(to_user=room.user2) | Q(from_user=room.user2) & Q(
                to_user=room.user1)).order_by('timestamp')
        print("chats", chats)
        journey = Channel.objects.get(pk=self.kwargs['journey_id'])
        assign_mentor = AssignMentorToUser.objects.filter(mentor=request.user, user=user, journey=journey).first()
        print(assign_mentor.journey)
        user_activity = UserActivityData.objects.filter(journey=journey, submitted_by=user, is_draft=False, is_active=True, is_delete=False)
        print("user_activity", user_activity)
        call_lsit = mentorCalendar.objects.filter(
            mentor=request.user, participants=user, slot_status="Booked", start_time__gte=datetime.now())
        exp_call_lsit = mentorCalendar.objects.filter(
            mentor=request.user, participants=user, slot_status="Booked", start_time__lte=datetime.now())
        mentoring_journey = MentoringJourney.objects.filter(journey=assign_mentor.journey, is_delete=False)
        assessment = []
        curriculum = []
        display_content = []
        channel = assign_mentor.journey
        for mentoring_journey in mentoring_journey:

            type = mentoring_journey.meta_key
            print(type)
            read_status = ""
            content_image = ""
            output_key = ""
            if type == "quest":
                content = Content.objects.get(pk=mentoring_journey.value)
                content_image = content.image
                try:
                    user_read_status = UserCourseStart.objects.get(
                        user=user, content=content, channel_group=mentoring_journey.journey_group, channel=channel.pk)
                    print(user_read_status)
                    read_status = user_read_status.status
                except UserCourseStart.DoesNotExist:
                    read_status = ""
                data = content
                output_key = LearningJournals.objects.filter(
                    journey_id=channel.pk, email=user.email, microskill_id=content.pk).first()
            elif type == "assessment":
                test_series = TestSeries.objects.get(pk=mentoring_journey.value)
                test_attempt = TestAttempt.objects.filter(
                    test=test_series, user=user, channel=mentoring_journey.journey)
                if test_attempt.count() > 0:
                    read_status = "Complete"
                data = test_series
                output_key = test_attempt.first()
            elif type == "survey":
                survey = Survey.objects.get(pk=mentoring_journey.value)
                survey_attempt = SurveyAttempt.objects.filter(
                    survey=survey, user=user)
                if survey_attempt.count() > 0:
                    read_status = "Complete"
                data = survey
                output_key = survey_attempt.first()
            elif type == "journals":
                weekely_journals = WeeklyLearningJournals.objects.get(
                    pk=mentoring_journey.value, journey_id=channel.pk)
                learning_journals = LearningJournals.objects.filter(
                    weekely_journal_id=weekely_journals.pk, journey_id=channel.pk, email=user.email)
                if learning_journals.count() > 0:
                    read_status = "Complete"
                data = weekely_journals
                output_key = learning_journals.first()
            else:
                content_image = ""

            display_content.append({
                "type": type,
                "data": data,
                "read_status": read_status,
                "read_data": output_key,
            })
        learning_journals = LearningJournals.objects.filter(
            email=user.email, journey_id=journey.pk, is_draft=False, is_private=False,
            is_weekly_journal=False).order_by("-created_at")
        print(learning_journals)
        # print("room details",room.name)
        
        context = {
            "user": user,
            "meetings": call_lsit,
            "expire_meetings": exp_call_lsit,
            "display_content": display_content,
            "room": room.name,
            "learning_journals": learning_journals,
            "chats": chats,
            "user_activity": user_activity
        }
        return render(request, "mentor/student_details.html", context)


@login_required
def weeklyjournalComment(request):
    if request.method == 'POST':
        user = User.objects.get(pk=request.user.pk)
        learning_journal_id = request.POST['learningjournal_id']
        learningjournal = LearningJournals.objects.get(pk=request.POST['learningjournal_id'])
        comment = request.POST['answer']
        # try block is to edit the comment
        try:
            comment_id = request.POST['answer_id']
            journal_comment = LearningJournalsComments.objects.filter(id=comment_id)
            if journal_comment:
                journal_comment = journal_comment.first()
                journal_comment.body = comment
                journal_comment.save()
        # except block is to ad  the comment
        except:
            if request.session['user_type'] == 'Mentor':
                if learningjournal.journey_id:
                    journey = Channel.objects.filter(id=learningjournal.journey_id).first()
                    if journey:
                        assign_mentor = AssignMentorToUser.objects.filter(user__email=learningjournal.email, mentor=user, journey=journey, is_assign=True, is_revoked=False).first()
                        print("ASSIgn mentor", assign_mentor)
                        if assign_mentor:
                            description = f"""Hi {assign_mentor.mentor.first_name} {assign_mentor.mentor.last_name}!
                            {user.first_name} {user.last_name} has posted comment on a journal."""

                            context = {
                                "screen": "Journal",
                            }
                            send_push_notification(assign_mentor.mentor, 'Comment Posted', description, context)
            elif request.session['user_type'] == 'Learner':
                journal_user = User.objects.filter(pk=learningjournal.user_id).first()
                if journal_user:
                    description = f"""Hi {journal_user.first_name} {journal_user.last_name}!
                    {user.first_name} {user.last_name} has posted comment on a journal."""

                    context = {
                        "screen": "Journal",
                    }
                    send_push_notification(journal_user, 'Comment Posted', description, context)
            LearningJournalsComments.objects.create(learning_journal=learningjournal,
                                                    user_email=user.email, user_name=user.get_full_name(),
                                                    user_id=user.pk, body=comment)
        return redirect(reverse('user:learning_journal_post', kwargs={"user_id": user.pk, "pk": learning_journal_id}))
    return redirect(reverse('user:learning_journal_post', kwargs={"user_id": user.pk, "pk": learning_journal_id}))


@method_decorator(login_required, name='dispatch')
class WeeklyJournalPost(View):
    def get(self, request, *args, **kwargs):
        user = User.objects.get(id=self.kwargs['user_id'])
        learning_journals = LearningJournals.objects.get(pk=self.kwargs['pk'])
        print("learning_journals", learning_journals)
        attachments = LearningJournalsAttachment.objects.all()
        for attachment in attachments:
            print("attachment", attachment.file_upload)

        learning_journals_attachments = LearningJournalsAttachment.objects.filter(
            post=learning_journals, upload_for="Post")
        print(learning_journals_attachments)
        comments = LearningJournalsComments.objects.filter(learning_journal=learning_journals)
        context = {
            "learning_journal": learning_journals,
            "comment": comments,
            "attachments": learning_journals_attachments,
            "user_id": str(request.user.id)
        }
        return render(request, 'mentor/learning_journal.html', context)


@method_decorator(login_required, name='dispatch')
class alloted_journeys(ListView):
    model = PoolMentor
    context_object_name = "journey_list"
    template_name = "mentor/journeys_list.html"

    def get_queryset(self):
        company_journey = company_journeys(
            self.request.session['user_type'], self.request.user, self.request.session.get('company_id'))
        journey_list = []
        pool_mentor_list = PoolMentor.objects.filter(
            mentor=self.request.user, pool__journey__is_active=True, pool__journey__is_delete=False, pool__journey__in=company_journey)
        journey_list = [{
            "pool_name": pool_mentor.pool.name,
            "journey_id": pool_mentor.pool.journey.id,
            "journey_name": pool_mentor.pool.journey.title,
            "journey_description": pool_mentor.pool.journey.short_description,
            "journey_category": pool_mentor.pool.journey.category,
            "journey_type": pool_mentor.pool.journey.channel_type,
        }
            for pool_mentor in pool_mentor_list]

        if not journey_list:
            user_channel_list = UserChannel.objects.filter(
                user=self.request.user, Channel__is_active=True, Channel__is_delete=False, Channel__in=company_journey)
            journey_list = [{
                "pool_name": '',
                "journey_id": user_channel.Channel.id,
                "journey_name": user_channel.Channel.title,
                "journey_description": user_channel.Channel.short_description,
                "journey_category": user_channel.Channel.category,
                "journey_type": user_channel.Channel.channel_type,
            }
                for user_channel in user_channel_list]
        return journey_list


@login_required
def update_events(request):
    start = request.POST['start']
    end = request.POST['end']
    title = request.POST['title']
    id = request.POST['id']
    user = User.objects.get(pk=request.user.pk)
    mentorCal = mentorCalendar.objects.filter(pk=id)
    mentorCal.update(start_time=convert_to_utc(start, request.session['timezone']), end_time=convert_to_utc(end, request.session['timezone']))
    mentorcal = mentorCal.first()
    if mentorcal.url:
        participants = mentorcal.participants
        send_update_booking_mail(participants, mentorcal.mentor, mentorcal.mentor.first_name,
                                 user.first_name, url_shortner(mentorcal.url, BASE_URL), convert_to_utc(mentorcal.start_time, request.session['timezone']), title, request.session['timezone'])

    return HttpResponse("Update")

@login_required
def update_manager_task(request):
    start = request.POST['start']
    end = request.POST['end']
    title = request.POST['title']
    id = request.POST['id']
    user = User.objects.get(pk=request.user.pk)
    task_obj = ProgramManagerTask.objects.filter(pk=id)
    task_obj.update(start_time=start, due_time=end)

    return HttpResponse("Update")


@login_required
def add_events(request):
    print("creating event man")
    start = request.POST['start']
    end = request.POST['end']
    title = request.POST['title']
    id = request.POST['id']
    company = Company.objects.get(id=request.session['company_id'])
    from apps.users.utils import convert_to_utc
    mentorCalendar.objects.create(id=id, mentor=request.user, title=title, start_time=convert_to_utc(start, request.session['timezone']),
                                  end_time=convert_to_utc(end, request.session['timezone']), created_by="Mentor", created_by_id=request.user.pk, company=company)
    return HttpResponse("Create")


@method_decorator(login_required, name='dispatch')
class JourneyReport(View):
    def get(self, request, journey):
        journey = Channel.objects.get(pk=journey)
        total_enroll = UserChannel.objects.filter(Channel=journey).count()
        today_enroll = UserChannel.objects.filter(Channel=journey, created_at__gte=datetime.now()).count()

        context = {
            "journey": journey,
            "total_enroll": total_enroll,

            "today_enroll": today_enroll

        }
        return render(request, "users/journey_reporting.html", context)


@method_decorator(login_required, name='dispatch')
class CreateCouponCode(CreateView):
    form_class = CouponCodeForm
    success_url = reverse_lazy('user:list_coupon')
    template_name = "coupon/Create_coupon.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.journey = self.request.POST['journey']
        f.save()
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class EditCouponCode(UpdateView):
    model = Coupon
    form_class = CouponCodeForm
    success_url = reverse_lazy('user:list_coupon')
    template_name = "coupon/Create_coupon.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.journey = self.request.POST['journey']
        f.save()
        return super().form_valid(form)


# def CouponCode(request):
#     if request.method == "POST":
#         form = CouponCodeForm(request.POST)
#         if form.is_valid():

#             f = form.save(commit=False)
#             f.created_by = request.user
#             f.journey = request.POST['journey']
#             f.save()
#             context = {
#                 "form": form,
#                 "message": "Coupon Created Successfully",
#             }
#             return redirect('user:list_coupon')
#             return render(request, "coupon/coupon_list.html", context=context)
#         context = {
#             "form": form,
#             "message": "Form Not Valid",
#         }
#         return render(request, "coupon/Create_coupon.html", context=context)
#     else:
#         form = CouponCodeForm()
#         return render(request, "coupon/Create_coupon.html", {"form": form})


@method_decorator(login_required, name='dispatch')
class ALLCouponCodes(ListView):
    model = Coupon
    context_object_name = "all_coupon"
    template_name = "coupon/coupon_list.html"

    def get_queryset(self):
        return Coupon.objects.filter(is_delete=False)


# def FreeJourenyEnroll(request, journey):
#     channel = Channel.objects.get(pk=journey)
#     try:
#         coupon = Coupon.objects.get(type=channel, active=True)
#     except Coupon.DoesNotExist:
#         context = {"message":"You're not authorize for free enrollment"}
#         return False
#     status= "Joined"
#     coupon.active = False
#     try:
#         UserChannel.objects.create(user=request.user, Channel=channel, status=status)
#     except Exception as e:
#         print(e)
#     return True

@method_decorator(login_required, name='dispatch')
class CreateAssessment(View):
    def get(self, request, *args, **kwargs):
        return render(request, "assessment/create_assessment.html")

    def post(self, request, *args, **kwargs):
        print("data ", request.POST)
        journey = request.POST['journey']
        question = request.POST['question']
        options = request.POST['options']
        question_type = request.POST['question_type']
        question_for = request.POST.getlist('question_for')
        display_order = int(request.POST['display_order'])
        try:
            is_active = check_check_box(request.POST['is_active'])
        except:
            is_active = False
        try:
            is_multichoice = check_check_box(request.POST['is_multichoice'])
        except:
            is_multichoice = False
        for user_type in question_for:
            profile_assest_ques = ProfileAssestQuestion.objects.create(journey=journey, question=question, question_type=question_type, question_for=user_type, display_order=display_order, is_active=is_active, is_multichoice=is_multichoice)

            if options:
                profile_assest_ques.options = ast.literal_eval(options)
                profile_assest_ques.save()

        messages.success(request, "Profile Assessment Created.")
        return redirect('user:assessment_list')


@method_decorator(login_required, name='dispatch')
class ALLAssessment(ListView):
    model = ProfileAssestQuestion
    context_object_name = "assessment"
    template_name = "assessment/assesment_list.html"

    def get_queryset(self):
        profile_assest_question = ProfileAssestQuestion.objects.filter(is_delete=False)
        if self.request.GET.get('type'):
            profile_assest_question = profile_assest_question.filter(question_for=self.request.GET['type'])
        profile_assest_list = []
        for question in profile_assest_question:
            journey = None
            print(question.journey)
            if question.journey:
                journey = Channel.objects.filter(pk=question.journey, parent_id=None,
                                                 is_active=True, is_delete=False).first()
            profile_assest_list.append({
                "pk": question.pk,
                "journey": '' if not journey else journey.title,
                "question": question.question,
                "options": question.options,
                "question_type": question.question_type,
                "question_for": question.question_for,
                "is_multichoice": question.is_multichoice,
                "display_order": question.display_order,
            })
        return profile_assest_list


@login_required
def UserSetPassword(request, pk):
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['new_password1']
            password2 = form.cleaned_data['new_password2']
            print("1", password2)
            form.save(commit=False)
            if len(password2) < 7:
                messages.error(request, "password length should be mininum 8 character")
                return render(request, 'auth/set_password.html', {'form': form})
            if password != password2:
                messages.error(request, "both password does not match")
                return render(request, 'auth/set_password.html', {'form': form})
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.save()
            print("2", user.password)
            return redirect(reverse('user:user-dashboard'))
        messages.error(request, "Invalid form")
        return render(request, 'auth/set_password.html', {'form': form})
    else:
        form = SetPasswordForm()
        return render(request, 'auth/set_password.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class EditAssessment(View):
    def get(self, request, *args, **kwargs):
        profile_assest = ProfileAssestQuestion.objects.get(pk=self.kwargs['pk'])
        return render(request, "assessment/create_assessment.html", {"profile_assest": profile_assest})

    def post(self, request, *args, **kwargs):
        journey = request.POST['journey']
        question = request.POST['question']
        options = request.POST['options']
        print("options", options, type(options))
        question_type = request.POST['question_type']
        question_for = request.POST.getlist('question_for')
        display_order = int(request.POST['display_order'])
        try:
            is_active = check_check_box(request.POST['is_active'])
        except:
            is_active = False
        try:
            is_multichoice = check_check_box(request.POST['is_multichoice'])
        except:
            is_multichoice = False

        ProfileAssestQuestion.objects.filter(pk=self.kwargs['pk']).update(journey=journey, question=question, options=ast.literal_eval(options),
                                                                          question_type=question_type, display_order=display_order, is_active=is_active, is_multichoice=is_multichoice)

        messages.success(request, "Profile Assessment Updated.")
        return redirect('user:assessment_list')


@login_required
def question_reorder(request):
    if request.method == "POST":
        value = request.POST['value']
        pk = request.POST['pk']
        ProfileAssestQuestion.objects.filter(pk=pk).update(display_order=value)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@login_required
def DeleteAssessmentQuestion(request, pk):
    ProfileAssestQuestion.objects.filter(pk=pk).update(is_delete=True, is_active=False)
    return redirect(reverse('user:assessment_list'))


@login_required
def DeleteCouponCode(request, pk):
    Coupon.objects.filter(id=pk).update(is_delete=True, is_active=False)
    return redirect(reverse('user:list_coupon'))


@method_decorator(login_required, name='dispatch')
class AddMentorToPool(View):
    def post(self, request):
        pool_id = request.POST['pool']
        pool = Pool.objects.get(pk=pool_id)
        print(pool)
        user_id = request.POST['user_id']
        try:
            mentor = Mentor.objects.get(pk=user_id)
        except Mentor.DoesNotExist:
            return JsonResponse({"message": "Mentor does not exist"}, safe=False)
        print(user_id)
        PoolMentor.objects.create(pool=pool, mentor=mentor)
        response = ({
            "message": "Mentor successfully added to pool",
            'pool': pool.name,
            'mentor': mentor.first_name + " " + mentor.last_name,
        })
        print(response)
        return JsonResponse(response, safe=False)


@login_required
def archive_user(request):
    if request.method == "POST":
        User.objects.filter(pk=request.POST['user_id']).update(is_archive=True, is_active=False)

    return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class ProgramUserReport(View):
    def get(self, request):
        return render(request, 'mentor/user_repost_list.html')


@method_decorator(login_required, name='dispatch')
class mentorMatchingRepost(View):
    def get(self, request):
        assigned_mentor = AssignMentorToUser.objects.all()
        context = {
            "data": assigned_mentor
        }
        return render(request, 'mentor/mentor_matching_report.html', context)


@method_decorator(login_required, name='dispatch')
class UserProfileCheck(View):
    def get(self, request):

        return render(request, 'mentor/user_report_list.html')

    def post(self, request):
        user_type = UserTypes.objects.filter(type__in=['Learner', 'Mentor', 'ProgramManager'])
        all_users = User.objects.filter(is_delete=False, is_active=True, userType__in=user_type)
        if request.POST.get('company'):
            print("get_co")
            company = Company.objects.get(pk=request.POST.get('company'))
            all_users = all_users.filter(company=company)
        if request.POST.get('coupon_code'):
            print("get_cop")
            all_users = all_users.filter(coupon_code=request.POST.get('coupon_code'))
        if request.POST.get('user_type'):
            user_type = UserTypes.objects.get(type=request.POST.get('user_type'))
            all_users = all_users.filter(userType=user_type)
        context = {
            "users": all_users
        }
        return render(request, 'mentor/user_report_list.html', context)


@method_decorator(login_required, name='dispatch')
class CreateCollabarate(CreateView):
    model = Collabarate
    form_class = CollabarateForm
    template_name = 'ProgramManager/create_meet.html'

    def get_form_kwargs(self):
        """
        Passes the request object to the form class
        """
        kwargs = super(CreateCollabarate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        f = form.save(commit=False)
        f.type = "LiveStreaming"
        f.start_time = convert_to_utc(self.request.POST['start_time'].replace('T',' ')+":00", self.request.session.get('timezone',None))
        f.end_time = convert_to_utc(self.request.POST['end_time'].replace('T',' ')+":00", self.request.session.get('timezone',None))
        f.journey = self.request.POST['journey']
        company_obj = Company.objects.filter(pk=self.request.session['company_id']).first()
        f.company = company_obj
        custom_url = self.request.POST.get('custom_url') or None
        print("CUSTOM URL from requests", custom_url)
        if not custom_url:
            meet, f.token = lives_streaming_room(f.title,"livestream", f.journey, self.request.user, f.speaker) # token is the meet_id here
            if f.token == 400:
                messages.error(self.request, meet['message'])
                return redirect(reverse('user:create_meet'))
            # f.custom_url = meet['url'] + "?t=" + f.token
            f.url_title = f.token
            f.custom_url = f"{BASE_URL}/config/dyte/{f.token}"
        else:
            f.custom_url = custom_url

        f.created_by = self.request.user
        description = f"""Hi {f.speaker.get_full_name()}!
        You have been assigned to a Livestream as a speaker:
        {f.title} {strf_format(convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))}"""
        context = {
            "screen": "Calendar",
            "navigationPayload":{
            "meet_id": str(f.id),
            "meet_type": 'LiveStreaming'
            }
        }
        send_push_notification(f.speaker, "LiveStream Assigned As Speaker", description, context)
        if f.speaker.phone and f.speaker.is_whatsapp_enable:
            live_stream_event(f.speaker, f.title, f.speaker, convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))

        space_id = self.request.POST['space_name']

        # print("REQUEST FILEs", self.request.FILES)
        # print("FILE COUSTOM", self.request.FILES['custom_background'])
        f.custom_background = self.request.FILES['custom_background']

        if f.add_to_community:
            add_to_community_event(f, self.request.user, space_id, self.request.session.get('timezone', None))
        f.save()

        journey_obj = Channel.objects.filter(pk=self.request.POST['journey']).first()
        users_list = getJourneyUsers(journey_obj)
        for user_obj in users_list:
            if str(user_obj.id) != str(f.speaker.id):
                f.participants.add(user_obj)
                description = f"""Hi {user_obj.get_full_name()}! 
                You have been assigned to a Livestream as an attendee:
                {f.title} {strf_format(convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))}
                Would you like to RSVP now?"""
                context = {
                    "screen": "Calendar",
                    "navigationPayload":{
                    "meet_id": str(f.id),
                    "meet_type": 'LiveStreaming'
                    }
                }
                send_push_notification(user_obj, "LiveStream Assigned Attendance", description, context)
        return super().form_valid(form)


    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:communication')
        else:
            return reverse('user:list_meeting')


@method_decorator(login_required, name='dispatch')
class EditCollabarate(UpdateView):
    model = Collabarate
    form_class = EditCollabarateForm
    template_name = 'ProgramManager/edit_meet.html'

    def get_form_kwargs(self):
        """
        Passes the request object to the form class
        """
        kwargs = super(EditCollabarate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        f = form.save(commit=False)
        f.type = "LiveStreaming"
        f.start_time = convert_to_utc(self.request.POST['start_time'].replace('T',' ')+":00", self.request.session.get('timezone',None))
        f.end_time = convert_to_utc(self.request.POST['end_time'].replace('T',' ')+":00", self.request.session.get('timezone',None))
        f.journey = self.request.POST['journey']
        company_obj = Company.objects.filter(pk=self.request.session['company_id']).first()
        f.company = company_obj
        speaker_id = self.request.POST['speaker']
        print("Already saved custom url", f.custom_url)
        if "config/dyte" in f.custom_url:
            meet_id = f.custom_url.split("/")[-1]
            res, message = edit_dyte_call(meet_id, "livestream", f.journey, self.request.user, speaker_id) # token is the meet_id here
            if not res:
                messages.error(self.request, message)
                return redirect(reverse('user:create_meet'))
            f.url_title = f.token

        f.created_by = self.request.user

        if f.speaker.phone and f.speaker.is_whatsapp_enable:
            description = f"""Hello {f.speaker}, livestream {f.title} has been scheduled at {strf_format(convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))}"""
            meeting_notification(f.speaker, f.title, description)
            live_stream_event(f.speaker, f.title, f.speaker, convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))

        space_id = self.request.POST['space_name']
        add_to_community_event(f, self.request.user, space_id, self.request.session.get('timezone',None))

        # print("REQUEST FILEs", self.request.FILES)
        # print("FILE COUSTOM", self.request.FILES['custom_background'])
        f.custom_background = self.request.FILES['custom_background']

        f.save()

        journey_obj = Channel.objects.filter(pk=self.request.POST['journey']).first()
        users_list = getJourneyUsers(journey_obj)
        f.participants.clear()
        for user_obj in users_list:
            if str(user_obj.id) != str(f.speaker.id):
                f.participants.add(user_obj)
                description = f"""Hello {user_obj.get_full_name()}, livestream {f.title} has been scheduled at {strf_format(convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))}. Please join accordingly"""
                meeting_notification(user_obj, f.title, description)
        return super().form_valid(form)

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:communication')
        else:
            return reverse('user:list_meeting')


@method_decorator(login_required, name='dispatch')
class ListCollabarate(ListView):
    model = Collabarate
    context_object_name = "meetings"
    template_name = 'ProgramManager/Meeting_List.html'

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_cancel=False, type__in=['LiveStreaming'])


@login_required
def delete_Collabarate(request, pk):
    meeting = Collabarate.objects.filter(pk=pk).first()
    # meet = delete_meet_link(meeting.title)
    meeting.is_active = False
    meeting.is_cancel = True
    meeting.save()
    if meeting.add_to_community:
        event = Event.objects.get(collabarate_id=pk)
        post = Post.objects.get(pk=event.post_id.id)
        post.is_active = False
        post.is_delete = True
        post.save()
    # if meet == 400:
    #     messages.error(request, meet['message'])
    #     return redirect(reverse('user:list_meeting'))
    if meeting.type == "GroupStreaming":
        return redirect(reverse('user:list_group_meeting'))
    else:
        return redirect(reverse('user:list_meeting'))


@method_decorator(login_required, name='dispatch')
class CreateGroupCollabarate(CreateView):
    model = Collabarate
    form_class = CollabarateGroupForm
    # success_url = reverse_lazy('user:list_group_meeting')
    # success_url = reverse_lazy('program_manager:communication')
    template_name = 'ProgramManager/create_meet.html'

    def get_form_kwargs(self):
        """
        Passes the request object to the form class
        """
        kwargs = super(CreateGroupCollabarate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        f = form.save(commit=False)
        participants = self.request.POST.getlist('participants') or None
        speaker = self.request.POST.get('speaker')
        meet, f.token = lives_streaming_room(f.title,"group-call", f.journey, self.request.user, speaker, participants) # token is the meet_id here
        if f.token == 400:
            messages.error(self.request, meet['message'])
            return redirect(reverse('user:create_meet'))
        f.url_title = f.token
        f.type = "GroupStreaming"
        company = self.request.session['company_id']
        f.company = Company.objects.filter(pk=company).first()

        f.start_time = convert_to_utc(self.request.POST['start_time'].replace('T',' ')+":00", self.request.session.get('timezone',None))
        f.end_time = convert_to_utc(self.request.POST['end_time'].replace('T',' ')+":00", self.request.session.get('timezone',None))

        if not f.custom_url:
            f.custom_url = f"{BASE_URL}/config/dyte/{f.token}"
        f.created_by = self.request.user
        
        description = f"""Hi {f.speaker.get_full_name()}!
            You have been assigned to a Group Call as a speaker:
            {f.title} {strf_format(convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))}"""
        context = {
            "screen": "Calendar",
            "navigationPayload":{
                "meet_id": str(f.id),
                "meet_type": 'GroupStreaming'
            }
        }
        send_push_notification(f.speaker, "Group Call Assigned As Speaker", description, context)

        f.custom_background = self.request.FILES['custom_background']

        if f.speaker.phone and f.speaker.is_whatsapp_enable:
            live_stream_event(f.speaker, f.title, f.speaker, convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))
        for participant in form.cleaned_data['participants']:
            description = f"""Hi {participant.get_full_name()}!
            You have been assigned to a Group Call as an attendee:
            {f.title} {strf_format(convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))}"""
            context = {
                "screen": "Calendar",
                "navigationPayload":{
                    "meet_id": str(f.id),
                    "meet_type": 'GroupStreaming'
                }
            }
            send_push_notification(participant, "Group Call Assigned Attendance", description, context)
            if participant.phone and participant.is_whatsapp_enable:
                live_stream_event(participant, f.title, f.speaker, convert_to_local_time(f.start_time, self.request.session.get('timezone',None)))
        return super().form_valid(form)


    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:communication')
        else:
            return reverse('user:list_group_meeting')


@method_decorator(login_required, name='dispatch')
class EditGroupCollabarate(UpdateView):
    model = Collabarate
    form_class = EditCollabarateGroupForm
    # success_url = reverse_lazy('user:list_group_meeting')
    # success_url = reverse_lazy('program_manager:communication')
    template_name = 'ProgramManager/edit_meet.html'

    def get_form_kwargs(self):
        """
        Passes the request object to the form class
        """
        kwargs = super(EditGroupCollabarate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        f = form.save(commit=False)
        participants = self.request.POST.getlist('participants') or None
        speaker = self.request.POST.get('speaker')

        meet, f.token = lives_streaming_room(f.title,"group-call", f.journey, self.request.user, speaker, participants)
        if f.token == 400:
            messages.error(self.request, meet['message'])
            return redirect(reverse('user:edit_group_meet'))
        # f.type = "GroupStreaming"
        # f.custom_url = meet['url']+"?t="+f.token
        f.updated_by = self.request.user
        f.start_time = convert_to_utc(self.request.POST['start_time'].replace('T',' ')+":00", self.request.session.get('timezone',None))
        f.end_time = convert_to_utc(self.request.POST['end_time'].replace('T',' ')+":00", self.request.session.get('timezone',None))
        # if f.speaker.phone and f.speaker.is_whatsapp_enable:
        #     live_stream_event(f.speaker, f.title, f.speaker, f.start_time)
        # for participant in f.participants.all():
        #     if participant.phone and participant.is_whatsapp_enable:
        #         live_stream_event(participant, f.title, f.speaker, f.start_time)
        f.custom_background = self.request.FILES['custom_background']
        return super().form_valid(form)

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:communication')
        else:
            return reverse('user:list_group_meeting')


@method_decorator(login_required, name='dispatch')
class ListGroupCollabarate(ListView):
    model = Collabarate
    context_object_name = "meetings"
    template_name = 'ProgramManager/Meeting_List.html'

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_cancel=False, type__in=['GroupStreaming'])


@method_decorator(login_required, name='dispatch')
class StartMeeting(View):
    def get(self, request, *args, **kwargs):
        meeting = Collabarate.objects.get(id=self.kwargs['pk'])
        context = {
            "meeting": meeting,
        }
        return render(request, 'ProgramManager/start_meet.html', context)


@login_required
def MeetingDetails(request, id):
    collabarate = Collabarate.objects.get(id=id)
    title = collabarate.url_title
    title = get_title(collabarate)
    data = meeting(title)['data']
    participants = []
    for data in data:
        # log_data = meeting_logs(data['id'])
        participants.append(data['participants'])
        try:
            meet_details = AllMeetingDetails.objects.get(id=data['id'])
        except AllMeetingDetails.DoesNotExist:
            meet_details = AllMeetingDetails.objects.create(id=data['id'], collaborate_meeting=collabarate,
                                                            ongoing=data['ongoing'],
                                                            max_participants=data['max_participants'],
                                                            title=data['room'],
                                                            start_time=unixTimstamp(data['start_time']),
                                                            duration=minutes(data['duration']))
    if participants:
        for user in participants[0]:
            try:
                MeetingParticipants.objects.get(id=user['participant_id'])
            except MeetingParticipants.DoesNotExist:
                MeetingParticipants.objects.create(id=user['participant_id'], session=meet_details,
                                                   user_name=user['user_name'],
                                                   join_time=unixTimstamp(user['join_time']),
                                                   duration=minutes(user['duration']))

    meet = AllMeetingDetails.objects.filter(collaborate_meeting=collabarate)
    user_list = MeetingParticipants.objects.filter(session__in=meet)
    context = {"data": meet, "users": user_list}
    print("context ", context)
    return render(request, 'ProgramManager/meeting_details.html', context)


@method_decorator(login_required, name='dispatch')
class UserMentorList(View):
    def get(self, request, pk=None, *args, **kwargs):

        # if request.session.get('company_id'):
        journey = company_journeys(request.session['user_type'], request.user, request.session['company_id'])
        # else:
        #     journey = company_journeys(request.session['user_type'], request.user)

        if pk is None:
            mentor = AssignMentorToUser.objects.filter(user=request.user, is_assign=True, journey__in=journey)
        else:
            user = User.objects.get(id=pk)
            mentor = AssignMentorToUser.objects.filter(user=user, is_assign=True, journey__in=journey)
        context = {
            "mentor": mentor
        }
        return render(request, 'users/mentor_list.html', context)


@method_decorator(login_required, name='dispatch')
class UserMentorProfile(View):
    def get(self, request, *args, **kwargs):
        mentor = Mentor.objects.get(pk=self.kwargs['mentor_id'])
        company = mentor.company.filter(id=request.session["company_id"]).first()
        user_profile_assest = UserProfileAssest.objects.filter(user=mentor)
        data = available_slots(participant=request.user.pk, date="", mentor=mentor.pk, company=company, offset=self.request.session.get('timezone',None))
        # print("Available slots data", data)
        return render(request, 'users/user-mentor-profile.html',
                      {"data": data, "user": mentor, "user_profile_assest": user_profile_assest})


@login_required
def BookMentorSlot(request, *args, **kwargs):
    if request.method == 'POST':
        mentorCal = mentorCalendar.objects.get(id=request.POST['pk'])
        data, meet_id = book_appointment(mentorCal.id, mentorCal.title, request.user, mentorCal.mentor, request.session['timezone'])
        if data['success'] == False:
            return data['message']
        return HttpResponse("Success")


@login_required
def cancelMentorSlot(request, *args, **kwargs):
    if request.method == "POST":
        print("test")
        mentorCal = mentorCalendar.objects.get(pk=request.POST['pk'])
        data = cancel_appointment(mentorCal.id, request.user, mentorCal.mentor, request.session['timezone'])
        if data['success'] == False:
            return data['message']
        return HttpResponse("Success")

@login_required
def deleteMentorSlot(request, *args, **kwargs):
    if request.method == "POST":
        mentorCalendar.objects.filter(pk=request.POST['pk']).delete()
        return HttpResponse("Success")

@login_required
def removeUserSlot(request, *args, **kwargs):
    if request.method == "POST":
        data = removeUserSlotFun(request.POST['pk'], request.POST['slot_type'], request.user)
        if data['Success'] == False:
            return data['Message']
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class BookMentorSlots(View):
    def get(self, request, pk=None, *args, **kwargs):
        result = []
        journey = company_journeys(request.session['user_type'], request.user, request.session['company_id'])
        # if request.session.get('company_id'):
        #     print("journey1 ",journey)
        # else:
        #     journey = company_journeys(request.session['user_type'], request.user)
        #     print("journey2 ",journey)

        if pk is None:
            assigned_mentors = AssignMentorToUser.objects.filter(
                user=request.user, is_assign=True, journey__in=journey)
            print("assigned_mentors1 ", assigned_mentors)
        else:
            user = User.objects.get(id=pk)
            assigned_mentors = AssignMentorToUser.objects.filter(user=user, is_assign=True, journey__in=journey)
            print("assigned_mentors2 ", assigned_mentors)
        company = Company.objects.get(pk=request.session['company_id'])
        for assigned_mentor in assigned_mentors:
            mentor = Mentor.objects.get(pk=assigned_mentor.mentor.pk)
            data = available_slots(participant=assigned_mentor.user.pk, date="", mentor=None, company=company)
            if "response" in data:
                result.extend(data['response'])
        return render(request, 'users/book-mentor-slot.html', {"data": {"message": "", "response": result}, })


@method_decorator(login_required, name='dispatch')
class ContactProgramTeamS(CreateView):
    model = ContactProgramTeam
    form_class = ContactProgramTeamForm
    success_url = reverse_lazy('user:contact_program_team')
    template_name = 'ProgramManager/contact_program_team.html'

    def form_valid(self, form):
        f = form.save(commit=False)
        f.user = self.request.user
        f.company = self.request.user.company.all().first()
        f.save()

        subject = self.request.POST['subject']
        issue = self.request.POST['issue']

        if not self.request.session['company_id']:
            messages.error(self.request, "Please select organization from side navigation")
            return redirect('user:contact_program_team')
        company = Company.objects.filter(pk=self.request.session['company_id']).first()
        type = UserTypes.objects.get(type="ProgramManager")
        # for program_manager email to send issues to program team
        program_managers = User.objects.filter(company=company, userType=type)
        email_list = [program_manager.email for program_manager in program_managers]

        try:
            files = self.request.FILES.getlist('image')
            mail = EmailMessage(subject=subject, body=issue, from_email=INFO_CONTACT_EMAIL,
                                to=email_list,  bcc=["Info@growatpace.com"])
            for file in files:
                name = file.name
                content = file.read()
                content_type = file.content_type
                ContactProgramTeamImages.objects.create(contact_program=f, image=file)
                mail.attach(name, content, content_type)
            mail.send()
            print(("mailed"))
            messages.success(self.request,
                             "Thank You, for raising an issue! We will try to fix it as soon as possible.")
        except BadHeaderError:
            messages.error(self.request, "Something went wrong!")
            return HTTPResponse('Invalid header found.')

        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ContactProgramTeamMember(View):
    def get(self, request, *args, **kwargs):
        company = self.request.user.company.all()
        data = ContactProgramTeam.objects.filter(company__in=company)
        ProgramTeam = []
        for obj in data:
            image = ContactProgramTeamImages.objects.get(contact_program=obj)
            ProgramTeam.append({

                "name": f"{obj.user.first_name} {obj.user.last_name}",
                "subject": obj.subject,
                "issue": obj.issue,
                "company": obj.company,
                "image": image.image,
            })
        context = {
            "ProgramTeam": ProgramTeam,
        }
        return render(request, 'ProgramManager/program-team.html', context)


@method_decorator(login_required, name='dispatch')
class GenerateAttendenceReport(View):
    def get(self, request):

        company = request.user.company.all()
        all_journey = Channel.objects.filter(channel_type="MentoringJourney",
                                             company__in=company, is_delete=False, is_active=True)
        context = {
            "journey": all_journey
        }
        return render(request, 'ProgramManager/attendance_report.html', context)

    def post(self, request):
        journey = request.POST['journey']
        mentor_channel = Channel.objects.get(pk=journey)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Attandance.csv"'
        fields = ['Group', 'Role', 'Name', 'Overall', 'Learn', 'Journal',
                  'Calls', 'Live Session', 'Group Session', 'One To One']

        for i in range(1, 16):
            fields.append("Journal " + str(i))

        temp_2 = MentoringJourney.objects.filter(journey=mentor_channel, meta_key="quest", is_delete=False)
        for j in range(len(temp_2)):
            fields.append("Learn " + str(j + 1))

        collabarate = Collabarate.objects.filter(journey=journey, is_cancel=False, start_time__lte=date.today())
        live_session = collabarate.filter(type="LiveStreaming")
        for k in range(len(live_session)):
            fields.append("Live Session " + str(k + 1))

        group_session = collabarate.filter(type="GroupStreaming")
        for x in range(len(group_session)):
            fields.append("Group Session " + str(x + 1))

        Fields = (fields)
        print(Fields)
        file = csv.DictWriter(response, fieldnames=Fields)

        res = generate_attendence(request.user, mentor_channel)
        file.writeheader()
        file.writerows(res)
        return response


@login_required
def UserActivity(request):
    return render(request, 'users/user_activity.html')


@login_required
def AllAssessmentReport(request):
    return render(request, 'assessment/Assessment-report.html')


@method_decorator(login_required, name='dispatch')
class ProgramJourneys(View):
    template_name = "ProgramManager/journeys_list.html"

    def get(self, request):
        company = request.user.company.all()
        journey_list = Channel.objects.filter(company__in=company, is_delete=False, is_active=True, parent_id=None)
        # journey_list = Channel.objects.filter(Q(program_team_1=request.user)|Q(program_team_2=request.user), company__in=company, is_delete=False, is_active=True, parent_id=None)
        context = {
            "journey_list": journey_list
        }
        return render(request, self.template_name, context)


@login_required
def journey_mentor(request):
    journey = Channel.objects.get(pk=request.GET.get('journey'))
    all_pools = Pool.objects.filter(journey=journey)
    all_poolmentor = PoolMentor.objects.filter(pool__in=all_pools)
    mentor_list = []
    for poolmentor in all_poolmentor:
        mentor_list.append(poolmentor.mentor)
    print("line 2603", mentor_list)
    return render(request, "partials/mentor_list.html", {"mentors": mentor_list})


@login_required
def assign_survey_list(request, pk=None):
    if pk is None:
        user = request.user
    else:
        user = User.objects.get(id=pk)

    journey = company_journeys(request.session['user_type'], request.user, request.session['company_id'])
    # if request.session.get('company_id'):
    # else:
    #     journey = company_journeys(request.session['user_type'], request.user)

    if request.session['user_type'] == "Mentor":
        joined_channel = []
        final_data = []
        pool_mentor = PoolMentor.objects.filter(mentor=user)
        for pools in pool_mentor:
            channel = pools.pool.journey
            if channel.is_active is True and channel.is_delete is False and channel not in joined_channel:
                surveys_ids = MentoringJourney.objects.filter(journey=channel, meta_key="survey",
                                                              is_delete=False).values("value")

                survey_id_list = [ids['value'] for ids in surveys_ids]
                all_survey = Survey.objects.filter(pk__in=survey_id_list)
                for survey in all_survey:
                    final_data.append({
                        "journey_id": channel.pk,
                        "journey_title": channel.title,
                        "name": survey.name,
                        "id": survey.pk
                    })
    else:
        final_data = []
        user_channel = UserChannel.objects.filter(
            user=user, Channel__channel_type="MentoringJourney", Channel__in=journey)
        for user_channel in user_channel:
            channel = user_channel.Channel
            surveys_ids = MentoringJourney.objects.filter(journey=channel, meta_key="survey", is_delete=False).values(
                "value")

            survey_id_list = [ids['value'] for ids in surveys_ids]
            all_survey = Survey.objects.filter(pk__in=survey_id_list)
            for survey in all_survey:
                final_data.append({
                    "journey_id": channel.pk,
                    "journey_title": channel.title,
                    "name": survey.name,
                    "id": survey.pk
                })
    return render(request, "comman/assign_survey_list.html", {"survey": final_data})


@method_decorator(login_required, name='dispatch')
class UserJourneyList(View):
    def get(self, request):
        user_journeys = UserChannel.objects.filter(status="Joined")
        return render(request, "users/user-journey-list.html", {"journey": user_journeys})


@method_decorator(login_required, name='dispatch')
class ProgramAnnouncement(View):
    def get(self, request):
        company_list = request.user.company.all()
        return render(request, "ProgramManager/program-announcement.html", {"company_list": company_list})

    def post(self, request):
        mentors = check_check_box(request.POST.get('mentors')) or False
        learners = check_check_box(request.POST.get('mentees')) or False
        program_team = check_check_box(request.POST.get('program_team')) or False
        everyone = check_check_box(request.POST.get('everyone')) or False
        journey_id = request.POST['journey']
        company_id = request.POST['company']
        journey = Channel.objects.get(id=journey_id, parent_id=None)
        topic = request.POST['topic']
        summary = request.POST['summary']
        company = Company.objects.get(pk=company_id)
        announcement = ProgramTeamAnnouncement.objects.create(
            journey=journey, topic=topic, summary=summary, created_by=request.user, announce_date=datetime.now(),
            company=company)
        user_channel = UserChannel.objects.filter(Channel_id=journey_id, status="Joined")
        user_list = []
        if user_channel:
            if mentors:
                user_channel = user_channel.filter(user__userType__type="Mentor")
                user_list.extend([channel.user for channel in user_channel])
            if learners:
                user_channel = user_channel.filter(user__userType__type="Learner")
                user_list.extend([channel.user for channel in user_channel])
            if everyone:
                user_list.extend([channel.user for channel in user_channel])
        print(user_list)
        program_data = User.objects.filter(~Q(id=request.user.id), company=company, userType__type="ProgramManager")
        print("program_data ", program_data)
        if program_team or everyone:
            user_list.extend(list(program_data))
        elif program_team and everyone:
            user_list.extend(list(program_data))
        lis = set(user_list)
        user_list = list(lis)
        print("ls", user_list)
        email_list = [user.email for user in user_list]
        message = f"""
                Hello,\n
                Your Program team has posted the following updates for your attention\n\n
                By: {request.user.first_name} {request.user.last_name}\n
                Topic: {topic}\n
                Summary Text: {summary}\n
                http://dev.growatpace.com\n
                Regards,\n
                Program Team
            """
        if user_list:
            # for user in user_list:
            #     room = get_chat_room(request.user, user)
            #     room = AllRooms.objects.get(name=room)
            #     Chat.objects.create(from_user=request.user, to_user=user, message=message, room=room)
            #     if user.phone and user.is_whatsapp_enable:
            #         program_team_broadcast(user, announcement, request.user)
            #     else:
            #         print("no phone number exist")
            program_announcement_email(topic, summary, email_list, request.user)
        messages.success(request, "Journey Announcement Successful.")
        return redirect('user:program_announcement')


@method_decorator(login_required, name='dispatch')
class ProgramAnnouncementList(ListView):
    model = ProgramTeamAnnouncement
    context_object_name = "program_announcements"
    template_name = "ProgramManager/program-announcement-list.html"


@login_required
def user_jourey_removed(request, user_channel_id):
    user_journey = UserChannel.objects.get(id=user_channel_id)
    print("usser_journey", user_journey)
    user_journey.status = "removed"
    user_journey.is_removed = True
    user_journey.removed_by = request.user
    user_journey.save()
    return redirect(reverse('user:user-journeys-list'))


@method_decorator(login_required, name='dispatch')
class BulkUserJourneyRemoved(View):
    def post(self, request):
        id_list = request.POST.getlist('journey_id')
        status = request.POST['action']
        for id in id_list:
            UserChannel.objects.filter(pk=id).update(is_removed=True, removed_by=request.user, status=status)
            print("removed", status, id)
        return redirect(reverse('user:user-journeys-list'))


@method_decorator(login_required, name='dispatch')
class ShowUserRewards(View):
    def get(self, request, *args, **kwargs):

        points = UserPoints.objects.filter(user=request.user)
        try:
            user_points = UserEarnedPoints.objects.get(user=request.user)
            total_points = user_points.total_points
        except:
            total_points = 0

        badges = UserBadgeDetails.objects.filter(user=request.user)
        streakActivity = userStreakActivity(request.user)
        print("streakActivity", streakActivity)
        streak_count = userStreakCount(request.user)
        # print("badges", badges)
        data = {
            "data": {
                "message": "",
                "points": points,
                "total_points": total_points,
                "badges": badges,
                "streak_count": streak_count,
                "streakActivity": streakActivity
            }
        }
        return render(request, 'users/user_rewards.html', data)


@login_required
def create_group(request):
    # print(request.POST, request.FILES, request.FILES.get("image"))
    name = request.POST['name']
    description = request.POST['description']
    members = request.POST.getlist('members')
    image = request.FILES.get('image', None)
    group_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    group = Room.objects.create(name=group_id, group_name=name, description=description,
                                type='OneToMany', created_by=request.user)
    if image:
        group.group_image=image
    group.save()
    for member in members:
        print("member", member)
        member = User.objects.get(pk=member)
        group.members.add(member)
        description = f"""Hi {member.get_full_name()}!
        You have been assigned to {name} chat group.
        Come say hi to your newly made Group Chat Group"""
        context = {
            "screen": "Chat"
        }
        send_push_notification(member, 'Chat Group Assigned', description, context)

    group.members.add(request.user)
    group.group_admin.add(request.user)


    if request.session['user_type'] == "Mentor":
        return redirect(reverse('mentor:mentor_mentees'))
    elif request.session['user_type'] == "ProgramManager":
        return redirect(reverse('program_manager:communication'))
    return redirect(reverse('user:chat'))


@method_decorator(login_required, name='dispatch')
class MatchingMentorAlgo(View):
    template_name = 'ProgramManager/matching_mentor.html'

    def get(self, request, *args, **kwargs):
        users = User.objects.filter(userType__type="Mentor")
        return render(request, self.template_name, {"user_list": users})

    def post(self, request):
        mentor_id = request.POST['mentor_id']
        question_1 = request.POST['question_1']
        ans_1 = request.POST['ans_1']
        question_2 = request.POST['question_2']
        ans_2 = request.POST['ans_2']
        question_3 = request.POST['question_3']
        ans_3 = request.POST['ans_3']
        try:
            user = User.objects.get(id=mentor_id, userType__type="Mentor")
        except User.DoesNotExist:
            return render(request, self.template_name)
        users = User.objects.filter(Q(first_name__exact=ans_1) | Q(username__exact=ans_1), userTypes__type="Learner")
        profile_assests_2 = UserProfileAssest.objects.filter(
            assest_question__question=question_2, question_for="Learner").values("user", "response")
        profile_assests_3 = UserProfileAssest.objects.filter(
            assest_question__question=question_3, question_for="Learner").values("user", "response")
        matchlist = []
        if users:
            for user in users:
                matchlist.append(user)
        if profile_assests_2:
            for profile_assest in profile_assests_2:
                if fuzz.token_set_ratio(ans_2, profile_assest["response"]) >= 80:
                    matchlist.append(profile_assest["user"])
        if profile_assests_3:
            for profile_assest in profile_assests_3:
                if fuzz.token_set_ratio(ans_3, profile_assest["response"]) >= 80:
                    matchlist.append(profile_assest["user"])
        return render(request, self.template_name, {"Learners": matchlist})


@login_required
def check_match_ques_config(request):
    if request.method == "POST":
        company = Company.objects.get(pk=request.POST['company'])
        journey = Channel.objects.get(pk=request.POST['journey'])
        ques_config = MatchQuesConfig.objects.filter(company=company, journey=journey).first()
        if ques_config:
            response = {
                "success": True,
                "message": f"The Configuration of Company {company.name} and Journey {journey.title} already exist"
            }
            return JsonResponse(response)
        return JsonResponse({"success": False})


@method_decorator(login_required, name='dispatch')
class MatchingQuestion(View):
    def get(self, request):
        program_manager = User.objects.get(pk=request.user.id)
        # company_list = []
        company = program_manager.company.filter(pk=request.session['company_id'])
        # company_list.append(company)
        journey = Channel.objects.filter(
            company__in=company, channel_type="MentoringJourney", closure_date__gt=datetime.now())
        mentor_ques = ProfileAssestQuestion.objects.filter(question_for="Mentor", is_active=True, is_delete=False)
        learner_ques = ProfileAssestQuestion.objects.filter(question_for="Learner", is_active=True, is_delete=False)

        print("company 2795", journey)
        context = {
            # "company_list": company_list,
            "journey": journey,
            "mentor_ques": mentor_ques,
            "learner_ques": learner_ques
        }
        return render(request, 'ProgramManager/match_question.html', context)

    def post(self, request):
        journey = Channel.objects.get(pk=request.POST['journey'])
        company = Company.objects.get(pk=request.session['company_id'])
        ques_config = MatchQuesConfig.objects.filter(company=company, journey=journey).first()
        if ques_config:
            messages.error(
                request,
                'The Configuration of Company {company.name} and Journey {journey.title} already exist'
            )
            return redirect(reverse('user:create_match_question'))
        ques_config = MatchQuesConfig.objects.create(company=company, journey=journey, created_by=request.user)
        for i in range(3):
            mentor_ques = ProfileAssestQuestion.objects.get(pk=request.POST['mentor' + str(i + 1)])
            learner_ques = ProfileAssestQuestion.objects.get(pk=request.POST['learner' + str(i + 1)])
            question_type = request.POST['type' + str(i + 1)]
            try:
                is_dependent = request.POST['is_dependent' + str(i + 1)]
            except:
                is_dependent = False

            print("is_dependent", is_dependent)

            if is_dependent:
                print("is_dependent", is_dependent)
                print(request.POST)
                mentor_ques_opt = ProfileAssestQuestion.objects.get(pk=request.POST['mentor_ques_opt' + str(i + 1)])
                learner_ques_opt = ProfileAssestQuestion.objects.get(pk=request.POST['learner_ques_opt' + str(i + 1)])
                ques_opt = request.POST['ques_opt' + str(i + 1)]
                # ques_op = ques_opt.split("', '")
                print(mentor_ques_opt, learner_ques_opt, ques_opt)
                MatchQuestion.objects.create(ques_config=ques_config, question_type=question_type,
                                             mentor_ques=mentor_ques, dependent_option=ques_opt,
                                             learner_ques=learner_ques, dependent_mentor=mentor_ques_opt,
                                             dependent_learner=learner_ques_opt, is_dependent=True)

            else:
                match_ques = MatchQuestion.objects.filter(ques_config=ques_config, mentor_ques=mentor_ques).first()
                if not match_ques:
                    MatchQuestion.objects.create(ques_config=ques_config, question_type=question_type,
                                                 mentor_ques=mentor_ques, learner_ques=learner_ques)
                else:
                    match_ques.learner_ques = learner_ques
                    match_ques.save()
        if request.session['user_type'] == "ProgramManager":
            return redirect(reverse('program_manager:matching'))
        return redirect(reverse('user:all_match_question'))


@login_required
def question_options1(request):
    ques_id = request.GET.get('mentor1')
    ques = ProfileAssestQuestion.objects.get(pk=ques_id)
    return render(request, "partials/question_options1.html", {"ques": ques})


@login_required
def question_options2(request):
    ques_id = request.GET.get('mentor2')
    ques = ProfileAssestQuestion.objects.get(pk=ques_id)
    return render(request, "partials/question_options2.html", {"ques": ques})


@login_required
def question_options3(request):
    ques_id = request.GET.get('mentor3')
    ques = ProfileAssestQuestion.objects.get(pk=ques_id)
    return render(request, "partials/question_options3.html", {"ques": ques})


@method_decorator(login_required, name='dispatch')
class MatchQuestionList(ListView):
    model = MatchQuesConfig
    context_object_name = "matchconfig"
    template_name = "ProgramManager/all_match_configuration.html"


@method_decorator(login_required, name='dispatch')
class DetailMatchQuestion(View):
    model = MatchQuesConfig
    template_name = "ProgramManager/match_question_view.html"

    def get(self, request, *args, **kwargs):
        match_config = MatchQuesConfig.objects.get(id=self.kwargs['config_id'])
        match_questions = MatchQuestion.objects.filter(ques_config_id=match_config, )
        return render(request, self.template_name, {"match_config": match_config, "match_questions": match_questions})


@method_decorator(login_required, name='dispatch')
class EditMatchQuestion(View):
    def get(self, request, *args, **kwargs):
        program_manager = User.objects.get(pk=request.user.id)
        match_config = MatchQuesConfig.objects.get(id=self.kwargs['config_id'])
        print("match_config", match_config)
        config = {
            "id": match_config.id,
            "company": match_config.company,
            "journey": match_config.journey
        }
        question_list = []
        match_questions = MatchQuestion.objects.filter(ques_config_id=match_config)
        for question in match_questions:
            question_list.append({
                "mentor_ques": question.mentor_ques,
                "learner_ques": question.learner_ques,
                "is_dependent": question.is_dependent,
                "dependent_learner": question.dependent_learner,
                "question_type": question.question_type,
                "dependent_mentor": question.dependent_mentor,
                "dependent_option": question.dependent_option
            })
        company_list = []
        for company in program_manager.company.all():
            company_list.append(company)
        journey = Channel.objects.filter(company__in=program_manager.company.all(), channel_type="MentoringJourney")
        mentor_ques = ProfileAssestQuestion.objects.filter(question_for="Mentor")
        learner_ques = ProfileAssestQuestion.objects.filter(question_for="Learner")

        context = {
            "company_list": company_list,
            "journey": journey,
            "mentor_ques": mentor_ques,
            "learner_ques": learner_ques,
            "config": config,
            "question_1": question_list[0],
            "question_2": question_list[1],
            "question_3": question_list[2]
        }
        return render(request, 'ProgramManager/edit-match-question.html', context)

    def post(self, request, *args, **kwargs):
        company = Company.objects.get(pk=request.POST['company'])
        journey = Channel.objects.get(pk=request.POST['journey'])
        program_manager = User.objects.get(pk=request.user.id)
        ques_config = MatchQuesConfig.objects.filter(id=self.kwargs['config_id'])
        ques_config.update(company=company, journey=journey)
        ques_config = ques_config.first()
        for i in range(3):
            mentor_ques = ProfileAssestQuestion.objects.get(pk=request.POST['mentor' + str(i + 1)])
            learner_ques = ProfileAssestQuestion.objects.get(pk=request.POST['learner' + str(i + 1)])
            question_type = request.POST['type' + str(i + 1)]
            try:
                is_dependent = request.POST['is_dependent' + str(i + 1)]
            except:
                is_dependent = False

            print("is_dependent", is_dependent)

            if is_dependent:
                print("is_dependent", is_dependent)
                print(request.POST)
                mentor_ques_opt = ProfileAssestQuestion.objects.get(pk=request.POST['mentor_ques_opt' + str(i + 1)])
                learner_ques_opt = ProfileAssestQuestion.objects.get(pk=request.POST['learner_ques_opt' + str(i + 1)])
                ques_opt = request.POST['ques_opt' + str(i + 1)]

                print(mentor_ques_opt, learner_ques_opt, ques_opt)
                MatchQuestion.objects.filter(ques_config=ques_config, question_type=question_type).update(
                    mentor_ques=mentor_ques, dependent_option=ques_opt, learner_ques=learner_ques,
                    dependent_mentor=mentor_ques_opt, dependent_learner=learner_ques_opt, is_dependent=True)

            else:
                MatchQuestion.objects.filter(ques_config=ques_config, question_type=question_type).update(
                    mentor_ques=mentor_ques, learner_ques=learner_ques, is_dependent=False)
        if request.session['user_type'] == "ProgramManager":
            return redirect(reverse('program_manager:matching'))
        return redirect(reverse('user:all_match_question'))


def google_login(request):
    redirect_uri = f"{request.scheme}://{request.get_host()}{reverse('user:google_login')}"
    # redirect_uri = "http://127.0.0.1:8000/login/"
    print("data ", request.GET)
    print('code' in request.GET)
    if ('code' in request.GET):
        params = {
            'grant_type': 'authorization_code',
            'code': request.GET.get('code'),
            'redirect_uri': redirect_uri,
            'client_id': settings.GOOGLE_CLIENT_KEY,
            'client_secret': settings.GOOGLE_CLIENT_SECRET
        }

        url = 'https://accounts.google.com/o/oauth2/token'
        response = requests.post(url, data=params)
        url = 'https://www.googleapis.com/oauth2/v1/userinfo'
        access_token = response.json().get('access_token')
        response = requests.get(url, params={'access_token': access_token})
        print(response.text)
        user_data = response.json()
        email = user_data.get('email')
        google_account_id = user_data.get('id')
        if not email:
            messages.error(
                request,
                'Unable to login with Gmail Please try again'
            )
            return redirect(reverse('user:login'))
        if user := User.objects.filter(email__iexact=email).first():
            if not user.is_social_login:
                user = social_type(user, "Google", google_account_id)
            elif user.social_login_type != "Google":
                messages.error(
                    request,
                    f"You're already registered with {user.social_login_type}. Please try to Login with {user.social_login_type} or using Email & Password"
                )
                return redirect(reverse('user:login'))
            if not user.is_active:
                user.is_active = True
            print("login ", user)
            user_type = user.userType.all()
            user_company = user.company.all()
            # print("user_company", company_id)
            if user_type.count() > 1 or user_company.count() > 1:
                print(user_type)
                return render(request, 'website/select-login-type..html', {"data": user_data, "type": user_type, "company": user_company})
            request.session['user_type'] = user_type.first().type
            if user_type.first().type != 'Admin' and user_company:
                company_id = user_company.first().id
                print("user_company", company_id)
                request.session['company_id'] = str(company_id)
                company = Company.objects.get(pk=company_id)
                request.session['company_name'] = company.name
            else:
                request.session['company_name'] = None
                request.session['company_id'] = None
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            print(request.session, "3162")
            UserSiteVisit(user)
            UpdateUserStreakCount(user)
            AddUserStreak(user)
            token, created = Token.objects.get_or_create(user=user)
            request.session['token'] = token.key
            user_agent = get_user_agent(request)
            user_device(user_agent, user)
            return redirect(reverse('user:user-dashboard'))
        return render(request, 'website/login-with-google.html', {"data": user_data})
        # first_name =  user_data.get('name', '').split()[0]
        # last_name = user_data.get('family_name')
        # avatar = user_data.get('picture')
        # user = User.objects.filter(email__iexact=email).first()
        # print("checking ",user)
        # if not user:
        #     user = User(email=email, first_name=first_name, last_name=last_name, username=email, is_term_and_conditions_apply=True, avatar=avatar)
        #     password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
        #     print(password)
        #     type = UserTypes.objects.get(type="Learner")
        #     request.session['user_type'] = type.type
        #     user.set_password(password)
        #     user.save()
        #     user.userType.add(type.id)
        #     default_space_join_user(user)
        #     register_email(user, password)
        #     NotificationAndPoints(user, title="registration")
        #     return redirect('user:user-dashboard')
        # else:
        #     user_type = ",".join(str(type.type) for type in user.userType.all())
        #     print("user_type",user_type)
        #     if user.is_active:
        #         print("login ",user)
        #         request.session['user_type'] = "Learner"
        #         login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        #         print(request.session, "3162")
        #         UserSiteVisit(user)
        #         UpdateUserStreakCount(user)
        #         AddUserStreak(user)
        #         user_agent = get_user_agent(request)
        #         user_device(user_agent, request.user)
        #         return redirect(reverse('user:user-dashboard'))
        #     else:
        #         messages.error(request, "Your account is deactivted")
        #         return redirect(reverse('user:login'))

    else:
        url = "https://accounts.google.com/o/oauth2/auth?client_id=%s&response_type=code&scope=%s&redirect_uri=%s&state=google"
        scope = [
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ]
        scope = " ".join(scope)
        url = url % (settings.GOOGLE_CLIENT_KEY, scope, redirect_uri)
    return redirect(url)

def google_register(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        fullname = request.POST['name']
        phone = request.POST['mobile']
        coupon_code = request.POST['coupon_code']
        user_type = request.POST['type']
        try:
            enable_whatsapp = check_check_box(request.POST['is_whatsapp_enable'])
        except:
            enable_whatsapp = False
        res = ast.literal_eval(request.POST['user_data'])
        print(res)
        first_name = res.get('given_name')
        last_name = res.get('family_name')
        avatar = res.get('picture')
        google_account_id = res.get('id')
        if not validate_Coupon(coupon_code):
            context = {'message': 'Invalid Coupon Code', 'class': 'danger'}
            return render(request, 'website/login.html', context)
        user = get_or_create_user(first_name, last_name, email, "Google", user_type, avatar, google_account_id)
        user.is_whatsapp_enable = enable_whatsapp
        user.phone = phone
        user.username = username
        user.coupon_code = coupon_code
        user.save()
        applyCouponCode(user, coupon_code)
        coupon = Coupon.objects.get(code__iexact=coupon_code)
        request.session['user_type'] = user_type
        journey = Channel.objects.get(id=coupon.journey)
        request.session['company_id'] = str(journey.company.id)
        company = Company.objects.get(pk=journey.company.id)
        request.session['company_name'] = company.name
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        token, created = Token.objects.get_or_create(user=user)
        request.session['token'] = token.key
        user_agent = get_user_agent(request)
        user_device(user_agent, request.user)
        return redirect(reverse('user:user-dashboard'))
    return redirect(reverse('user:login'))

class SocialLoginType(View):
    def post(self, request):
        email = request.POST['email']
        user_type = request.POST['type']
        request.session['user_type'] = user_type
        company_id = request.POST['company']
        request.session['company_id'] = company_id
        company = Company.objects.get(pk=company_id)
        request.session['company_name'] = company.name
        user = User.objects.get(email=email)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        print(request.session, "3162")
        UserSiteVisit(user)
        UpdateUserStreakCount(user)
        AddUserStreak(user)
        user_agent = get_user_agent(request)
        user_device(user_agent, request.user)
        return redirect(reverse('user:user-dashboard'))

class SocialLoginCompany(View):
    def post(self, request):
        email = request.POST['email']
        user_type = request.POST['type']
        request.session['user_type'] = user_type
        user = User.objects.get(email=email)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        print(request.session, "3162")
        UserSiteVisit(user)
        UpdateUserStreakCount(user)
        AddUserStreak(user)
        user_agent = get_user_agent(request)
        user_device(user_agent, request.user)
        return redirect(reverse('user:user-dashboard'))


def create_apple_client_secret():
    import jwt
    from datetime import timedelta
    from django.utils import timezone
    headers = {
    'alg': "ES256",
    'kid': settings.APPLE_KEY_ID
    }
    payload = {
    'iss': settings.APPLE_TEAM_ID,
    'iat': timezone.now(),
    'exp': timezone.now() + timedelta(days=180),
    'aud': 'https://appleid.apple.com',
    'sub': settings.APPLE_SERVICE_ID
    }
    client_secret = jwt.encode(
    payload, 
    settings.APPLE_PRIVATE_KEY, 
    algorithm='ES256', 
    headers=headers
    )
    return client_secret

def verify_and_decode_identity_token(identity_token, client_id, apple_public_keys_url):
    # Fetch the JSON Web Key Set from Apple
    jwks = requests.get(apple_public_keys_url).json()
    # print("JWK RESPONSE", jwks)

    # Verify and decode the identity token
    public_key = None
    for key in jwks['keys']:
        if key['kid'] == jwt.get_unverified_header(identity_token).get('kid'):
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
            # print(public_key)
            break

    if public_key:
        try:
            decoded_token = jwt.decode(identity_token, public_key, algorithms=['RS256'], audience=client_id)
            return decoded_token
        except jwt.ExpiredSignatureError as e:
            print(e)
            # Handle token expiration error
            return None
        except jwt.JWTClaimsError as er:
            print(er)
            # Handle invalid claims error
            return None
        except jwt.JWTError as err:
            print(err)
            # Handle other JWT verification errors
            return None
    else:
        # Public key not found, token cannot be verified
        return None

def apple_login(request):
    redirect_uri = f"{request.scheme}://{request.get_host()}{reverse('user:apple_login')}"
    redirect_url = f"https://appleid.apple.com/auth/authorize?client_id={settings.APPLE_SERVICE_ID}&redirect_uri=https://{request.get_host()}/apple-login-callback&response_mode=form_post&scope=name&response_type=code%20id_token&state=bIMh7GGMABzk%20email"
    return redirect(redirect_url)

@csrf_exempt
def apple_login_callback(request, *args, **kwargs):
    if request.method == "POST":
        data = request.POST
        print("CALLBACK DATA", data)
        authorization_code = request.POST.get('code')
        csrf_token = request.POST.get('csrfmiddlewaretoken')
        id_token = request.POST.get('id_token')

        user_info = verify_and_decode_identity_token(id_token, settings.APPLE_SERVICE_ID, 'https://appleid.apple.com/auth/keys')
        print("USER INFO",user_info)

        CLIENT_SECRET = create_apple_client_secret()
        # print("CLIENT SECRET", CLIENT_SECRET)

        token_url = 'https://appleid.apple.com/auth/token'
        data = {
            'client_id': settings.APPLE_SERVICE_ID,
            'client_secret': CLIENT_SECRET,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': f"https://{request.get_host()}/apple-login-callback",
        }
        response = requests.post(token_url, data=data)
        # print("TOKEN RESPONSE",response.json())
        if response.status_code == 200:
            access_token = response.json()['access_token']
            print("ACCESS TOKEN RECEIVED")
            access_id_token = response.json()['id_token']
            # if access_id_token:
                # user_info_access = verify_access_token(access_token)
                # print("USER INFO ACCESS", user_info_access)
                # decoded = jwt.decode(access_id_token,settings.APPLE_PRIVATE_KEY,['RS256'])
                # print(decoded)
                # response_data = {}
                # response_data.update(
                #     {"email": decoded["email"], "name": decoded["name"]}
                # ) if "email" in decoded else None
                # response_data.update({"uid": decoded["sub"]}) if "sub" in decoded else None

            return redirect(reverse('user:user-dashboard'))
        else: 
            print("THE USER REDIRECTION BECAUSE OF STATUS CODE", response.status_code, response.text)
            return redirect(reverse('user:login'))
    print("THE USER REDIRECTION BECAUSE IT WAS NOT A POST REQUEST")
    return redirect(reverse('user:login'))


# @method_decorator(login_required, name='dispatch')
class RedirectShortUrl(View):
    def get(self, request, short_url):
        url = UrlShortner.objects.filter(short_url=short_url).first()
        # long_url = request.build_absolute_uri('/')[:-1]+"/"+url[0].long_url
        return redirect(url.long_url)

@method_decorator(login_required, name="dispatch")
class UserCertificates(View):
    def get(self, request):
        return render(request, 'users/certificates.html')


class Check_lite_signup_user_data(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        data = request.data
        serializer = CheckLiteSignupUserSerializer(data=data)

        if serializer.is_valid():
            email = data['email']
            phone = data['phone']

            journey_id = data['journey_id']

            combo_user = User.objects.filter(email=email, phone=phone, is_active=True, is_delete=False)
            print("edewc", email, phone)
            users = User.objects.filter(Q(email=email) | Q(phone=phone), is_active=True, is_delete=False)
            all_users = combo_user | users
            user_list = []
            if not all_users:
                context = {
                    "success": False,
                    "message": "User does not exist"
                }
                return JsonResponse(context)
            for user in all_users:
                userr_type = ",".join(str(type.type) for type in user.userType.all())
                user_list.append({
                    "is_active": user.is_active,
                    "user_type": userr_type,
                    "email": user.email if user else "",
                    "username": user.username if user else "",
                    "mobile": str(user.phone) if user else "",
                    "first_name": user.first_name if user else "",
                    "last_name": user.last_name if user else ""
                })

            codee = ''
            if code := Coupon.objects.filter(journey=journey_id, valid_from__lte=datetime.now(), valid_to__gte=datetime.now(),
                                            is_active=True):
                codee = code.first().code
            context = {
                "success": True,
                "coupon_code": codee if user else "",
                "users": user_list
            }
            return JsonResponse(context)
        return JsonResponse({"message": "missing paramerters", "success":False})        