import os
from ravinsight.settings.base import BASE_DIR
import ast
import string
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
import math, re, jwt
from django.core.mail import BadHeaderError, EmailMessage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from http.client import HTTPResponse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls.base import reverse_lazy
from apps.api.utils import User_firebase_details, check_valid_user, get_journey_content, get_journey_progress, get_or_create_user, get_user_profile_data, translate_data, update_boolean
from apps.atpace_community.utils import add_member_to_space, avatar, default_space_join_user, ques_image
from apps.atpace_community.models import SpaceJourney
from apps.chat_app.models import Chat, Room as AllRooms
from apps.community.models import CommunityPost, LearningJournals, WeeklyLearningJournals
from apps.community.utils import create_post, delete_post, get_space_post, post_Comment
from apps.content.models import ChannelGroup, ChannelGroupContent, Content, ContentData, ContentDataOptions, ContetnOptionSubmit, ProgramTeamAnnouncement, PublicProgramAnnouncement, \
    TestAttempt, UserChannelLevel, UserCourseStart, UserReadContentData, UserTestAnswer, MentoringJourney
from apps.leaderboard.models import UserEngagement
from apps.leaderboard.views import CheckEndOfJourney, CourseCompletion, NotificationAndPoints, SubmitPreFinalAssessment, UserSiteVisit, UpdateUserStreakCount, AddUserStreak, send_push_notification
from apps.mentor.models import PoolMentor, DyteAuthToken
from ravinsight.constants import LANGUAGES
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
import pandas as pd
import pyotp
import random, csv
from django.contrib.auth import authenticate
from apps.survey_questions.models import Survey, SurveyAttempt
from apps.test_series.models import TestOptions, TestQuestion
from apps.users.helper import add_user_to_company
from apps.users.models import Company, ContactProgramTeamImages, Profile, ContactProgramTeam, UserEmailChangeRecord, CSVFile, Collabarate, ProgramManager, SaveRasaManagerFiles
from apps.users.utils import register_email, validate_Coupon, sendVerificationMail, send_email_otp, validate_Coupon_for_rasa, update_signup_lite, send_activity_email
from apps.utils.models import Industry, Tags
from apps.utils.utils import generate_attendence_for_rasa
from ravinsight.web_constant import INFO_CONTACT_EMAIL
from apps.vonage_api.utils import journey_enrolment
from ..serializers import *
from django.core.files import File
from datetime import datetime, date, timedelta
from time import time
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets
from apps.utils.utils import all_categories_list, reset_passwordMail, send_otp, vonage_sms_otp, generate_attendence, vonage_sms_otp_sender
from apps.content.utils import company_journeys, is_parent_channel, public_announcement_list, public_channel_list, public_channel_list_search
from apps.kpi.Models.Learner import NoActivityMenteeData, NoActivityMentorData, NoActivityPairData
from apps.mentor.models import AssignMentorToUser
from apps.users.models import Company, Coupon
from apps.users.cron import users_risk_data_update, mentors_risk_data_update, pair_risk_data_update
from django.template.loader import render_to_string

class Logout(APIView):
    permission_classes = [AllowAny]
    """
    logout and token will be deleted
    """

    def get(self, request):
        request.user.auth_token.delete()
        return Response({"Message": "Logout Successful",
                         "Status": "True"},
                        status=status.HTTP_200_OK)

class GetUserCompany(APIView):
    permission_classes = [AllowAny]
    serializer_class = GetUserCompanySerializer
    def post(self, request):
        print("data Rishabh: ",request.data)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = request.data['data']
            try:
                user = User.objects.get(Q(email=data) | Q(username=data) | Q(phone=data), is_delete=False, is_active=True)
            except User.DoesNotExist:
                return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

            company_list = []
            for comp in user.company.all():
                company_list.append({
                    "company_id": comp.id,
                    "company_name": comp.name
                })
            response = {
                "message": "company data",
                "success": True,
                "company": company_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"messages": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)

class resetPassword(APIView):
    permission_classes = [AllowAny]
    """
    reset password to create new password
    """
    serializer_class = ForgetPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = request.data['email']
            associated_users = User.objects.filter(Q(email=email))

            if associated_users.exists():
                for user in associated_users:
                    # sendVerificationMail(user, user.email)
                    otp = str(random.randint(100000, 999999))
                    reset_passwordMail(user, otp)
                    if user:
                        user_profile = Profile.objects.filter(user=user)
                        if user_profile.count() > 0:
                            user_profile = Profile.objects.filter(user=user).first()
                            user_profile.otp = otp
                            user_profile.save()
                        else:
                            user_profile = Profile.objects.create(user=user, otp=otp)

                return Response({"success": True, "message": "Password reset request successfully sent to your email."}, status=status.HTTP_200_OK)
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def SMPTMail(email, data):
    Receiver = email
    Subject = "Password Reset"
    Message = 'mail.txt'
    mail = render_to_string(Message, data)
    # return send_mail(Subject, mail, EMAIL_HOST_USER, [Receiver], fail_silently=False,)


class ConfirmPassword(APIView):
    permission_classes = [AllowAny]
    serializer_class = ConfirmPasswordSerializer
    """
    confirmation and create new password
    """

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password Successfully Created", "success": True}, status=status.HTTP_200_OK)
        return Response({"messages": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class ChangePassword(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordChangeSerializer
    """
    change password
    """

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=request.data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

            print(user.password)
            password = request.data['password']
            new_password = request.data['new_password']
            confirm_password = request.data['confirm_password']
            if not check_password(password, user.password):
                return Response({"message": "Old Password does not match", "success": False}, status=status.HTTP_200_OK)
            if new_password != confirm_password:
                return Response({"message": "Both Password should be same", "success": False}, status=status.HTTP_200_OK)
            password = serializer.validated_data.get('new_password')
            serializer.validated_data['new_password'] = make_password(password)
            print(serializer.validated_data['new_password'])
            user.set_password(request.data['new_password'])
            user.save()
            return Response({"message": "Password Successfully changed", "success": True}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "status": False}, status=status.HTTP_400_BAD_REQUEST)


class AllChannels(APIView):
    permission_classes = [AllowAny]
    serializer_class = ChannelSerializer
    """
    All channels
    """

    def get(self, request, *args, **kwargs):
        user = User.objects.get(id=self.kwargs['user_id'])
        channel = public_channel_list(user, self.request.query_params.get('company_id'))
        serializ = self.serializer_class(instance=channel, many=True)
        return Response(serializ.data)


class BrowseChannel(APIView):
    permission_classes = [AllowAny]
    serializer_class = BrowseChannelSerializer

    """
    Show all channels of user 
    """

    def get(self, request, *args, **kwargs):
        user = User.objects.get(id=self.kwargs['user_id'])
        queryset = UserChannel.objects.filter(user=user)
        serializer = self.serializer_class(instance=queryset, many=True)
        return Response(serializer.data)


class SentOtpRequest(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginWithOtpSerializer
    """
    sent otp request
    """

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            phone = request.data['phone']
            print("phone", phone)
            user = User.objects.filter(phone__iexact=phone)
            if len(user) > 0:
                user = user.first()
                otp = str(random.randint(100000, 999999))
                if data.get('device_id') and data.get('firebase_token'):
                    User_firebase_details(user, data.get('device_id'), data.get('firebase_token'))
                vonage_sms_otp_sender(user, otp)
                user_profile = Profile.objects.filter(user=user)
                if user_profile.count() > 0:
                    user_profile = Profile.objects.filter(user=user).first()
                    user_profile.otp = otp
                    user_profile.save()
                else:
                    user_profile = Profile.objects.create(user=user, otp=otp)

                return Response({'message': otp, "status": True}, status=status.HTTP_200_OK)
            return Response({"message": "User not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "serializer.errors", "status": False}, status=status.HTTP_400_BAD_REQUEST)


def GenerateOtp():
    otp = pyotp.TOTP('base32secret3232', interval=60)
    print(otp)
    return otp


class SignUp(APIView):
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            host = self.request.query_params.get('host_name') or "Mobile"
            email = request.data['email']
            try:
                validate_email(email)
            except Exception as e:
                return Response({'messgage': "Email is incorrect", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email=email)
                return Response({'messgage': "Email already exists.", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                user = serializer.save()
            if data.get('password'):
                password = serializer.validated_data.get('password')
                serializer.validated_data['password'] = make_password(password)
            user = serializer.save()
            email = request.data['email']
            type = data.get('userType') if data.get('userType') else "Learner"
            user_type = UserTypes.objects.get(type=type)
            user.userType.add(user_type.id)
            user.is_active = True
            default_space_join_user(user)
            if not data.get('coupon_code') and host == "Mobile":
                return Response ({"message": "Coupon code required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            elif data.get('coupon_code') and host != "Forum":
                print(f"data.get('coupon_code'): {data.get('coupon_code')}")
                coupon_code = data.get('coupon_code')
                validate_Coupon(data.get('coupon_code'))
                user.coupon_code = data.get('coupon_code')
                applyCouponCode(user, data.get('coupon_code'))
            NotificationAndPoints(user, "registration")
            password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=8))
            print(password)
            user.set_password(password)
            user.save()
            user = User.objects.filter(email=email)
            user = user.first()
            if user:
                otp = str(random.randint(100000, 999999))
                print("Signup OTP", otp)
                profile = Profile(user=user, otp=otp)
                profile.save()

                vonage_sms_otp_sender(user, otp)
                register_email(user, password)
            token, created = Token.objects.get_or_create(user=user)
            token = token.key
            return Response({'messgage': otp, "success": True}, status=status.HTTP_201_CREATED)
        return Response({'messgage': serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class LoginWithEmailOrOtp(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginWithEmailOrOtpSerializer
    """
    Login with email & password/ mobile & otp
    """

    def post(self, request):
        data = request.data
        type = request.data.get('user_type') or "Learner"
        print(type)
        if data.get('email'):
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):

                email = request.data['email']
                password = request.data['password']
                try:
                    try:
                        user = User.objects.get(Q(username__iexact=email) | Q(
                            email__iexact=email), userType__type=type)
                    except Exception:
                        return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
                    print("Check Login", user)
                    if user:
                        user = authenticate(username=email, password=password)
                        if user:
                            if data.get('device_id') and data.get('firebase_token'):
                                User_firebase_details(user, data.get('device_id'), data.get('firebase_token'))
                            UserSiteVisit(user)
                            UpdateUserStreakCount(user)
                            AddUserStreak(user)
                            token, created = Token.objects.get_or_create(user=user)
                            token = token.key
                            print("line 297 --- ", token)
                            if user.is_active:
                                print(user)
                                industry_list = []
                                expertize_list = []
                                for industry in user.industry.all():
                                    industry_list.append(industry.name)
                                for expertize in user.expertize.all():
                                    expertize_list.append(expertize.name)
                                response = {
                                    "data":
                                        {
                                            "username": user.username,
                                            "id": user.id,
                                            "email": user.email,
                                            "is_email_verified": user.is_email_verified,
                                            "phone": str(user.phone),
                                            "is_phone_verified": user.is_phone_verified,
                                            "user_type": type,
                                            "private_profile": user.private_profile,
                                            "token": token,
                                            "first_name": user.first_name,
                                            "last_name": user.last_name,
                                            "gender": user.gender,
                                            "age": user.age,
                                            "prefer_not_say": user.prefer_not_say,
                                            "organization": user.organization,
                                            "current_status": user.current_status,
                                            "position": user.position,
                                            "avatar": avatar(user),
                                            "expertize": expertize_list,
                                            "industry": industry_list,
                                            "linkedin_profile": user.linkedin_profile,
                                            "favourite_way_to_learn": user.favourite_way_to_learn,
                                            "interested_topic": user.interested_topic,
                                            "upscaling_reason": user.upscaling_reason,
                                            "time_spend": user.time_spend

                                        },
                                    "success": True,
                                    "message": "Login successfull",
                                }
                                return Response(response, status=status.HTTP_200_OK)

                            return Response({"message": "Inactive User", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                        return Response({"message": "Invalid email and Password", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                except User.DoesNotExist:
                    return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

        elif data.get('phone'):
            serializer = LoginWithOtpSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                phone = request.data['phone']
                user = User.objects.filter(phone__iexact=phone, userType__type=type)

                if user:
                    UserSiteVisit(user.first())
                    if data.get('device_id') and data.get('firebase_token'):
                        User_firebase_details(user.first(), data.get('device_id'), data.get('firebase_token'))
                    user = user.first()
                    otp = str(random.randint(100000, 999999))
                    vonage_sms_otp_sender(user, otp)
                    user_profile = Profile.objects.filter(user=user)
                    if user_profile.count() > 0:
                        user_profile = Profile.objects.filter(user=user).first()
                        user_profile.otp = otp
                        user_profile.save()
                    else:
                        user_profile = Profile.objects.create(user=user, otp=otp)

                    return Response({'messgae': otp, "success": True}, status=status.HTTP_200_OK)

                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"Error": "Enter Valid Credentials", "success": False}, status=status.HTTP_400_BAD_REQUEST)


class CommunityLoginWithEmailOrOtp(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginWithEmailOrOtpSerializer
    """
    Login with email & password/ mobile & otp
    """

    def post(self, request):
        data = request.data
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):

            email = request.data['email']
            password = request.data['password']
            try:
                print("line 392")
                try:
                    user = User.objects.get(Q(username__iexact=email) | Q(email__iexact=email))
                except Exception:
                    print("line 395")
                    return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
                print("Check Login", user)
                if user:
                    user = authenticate(username=email, password=password)
                    if user:
                        if data.get('device_id') and data.get('firebase_token'):
                            User_firebase_details(user, data.get('device_id'), data.get('firebase_token'))
                        UserSiteVisit(user)
                        UpdateUserStreakCount(user)
                        AddUserStreak(user)
                        token, created = Token.objects.get_or_create(user=user)
                        token = token.key
                        print("line 297 --- ", token)
                        if user.is_active:
                            print(user)
                            industry_list = []
                            expertize_list = []
                            for industry in user.industry.all():
                                industry_list.append(industry.name)
                            for expertize in user.expertize.all():
                                expertize_list.append(expertize.name)
                            response = {
                                "data":
                                    {
                                        "username": user.username,
                                        "id": user.id,
                                        "email": user.email,
                                        "is_email_verified": user.is_email_verified,
                                        "phone": str(user.phone),
                                        "is_phone_verified": user.is_phone_verified,
                                        "private_profile": user.private_profile,
                                        "token": token,
                                        "first_name": user.first_name,
                                        "last_name": user.last_name,
                                        "gender": user.gender,
                                        "age": user.age,
                                        "prefer_not_say": user.prefer_not_say,
                                        "organization": user.organization,
                                        "current_status": user.current_status,
                                        "position": user.position,
                                        "expertize": expertize_list,
                                        "industry": industry_list,
                                        "linkedin_profile": user.linkedin_profile,
                                        "favourite_way_to_learn": user.favourite_way_to_learn,
                                        "interested_topic": user.interested_topic,
                                        "upscaling_reason": user.upscaling_reason,
                                        "time_spend": user.time_spend

                                    },
                                "success": True,
                                "message": "Login successfull",
                            }
                            return Response(response, status=status.HTTP_200_OK)

                        return Response({"message": "Inactive User", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                    return Response({"message": "Invalid email and Password", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class VerifyOtpRequest(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOtpSerializer
    """
    verify otp
    """

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        type = request.data.get('user_type') or "Learner"
        print(type)
        if serializer.is_valid(raise_exception=True):
            verify_otp = request.data['otp']
            # phone = request.data['phone']
            if data.get('email'):
                user = User.objects.filter(email__iexact=request.data['email'], userType__type=type)
            elif data.get('phone'):
                user = User.objects.filter(phone__iexact=request.data['phone'], userType__type=type)
            print(user)
            if user:
                if data.get('device_id') and data.get('firebase_token'):
                    User_firebase_details(user.first(), data.get('device_id'), data.get('firebase_token'))
                profile = Profile.objects.filter(user=user.first())
                print("Profile", profile.first())
                if verify_otp == profile[0].otp:
                    user.is_phone_verified = True
                    print("phon line 332 ----- ", user)
                    if user:
                        user = user.first()
                        token, created = Token.objects.get_or_create(user=user)
                        token = token.key
                        print(token)
                        user.is_active = True
                        # UserSiteVisit(user)
                        industry_list = []
                        expertize_list = []
                        for industry in user.industry.all():
                            industry_list.append(industry.name)
                        for expertize in user.expertize.all():
                            expertize_list.append(expertize.name)
                        response = {
                            "data":
                            {
                                "username": user.username,
                                "id": user.id,
                                "email": user.email,
                                "is_email_verified": user.is_email_verified,
                                "phone": str(user.phone),
                                "is_phone_verified": user.is_phone_verified,
                                "user_type": type,
                                "private_profile": user.private_profile,
                                "Token": token,
                                "username": user.username,
                                "id": user.id,
                                "email": user.email,
                                "phone": str(user.phone),
                                "token": token,
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "gender": user.gender,
                                "age": user.age,
                                "prefer_not_say": user.prefer_not_say,
                                "organization": user.organization,
                                "current_status": user.current_status,
                                "position": user.position,
                                "avatar": avatar(user),
                                "expertize": expertize_list,
                                "industry": industry_list,
                                "linkedin_profile": user.linkedin_profile,
                                "favourite_way_to_learn": user.favourite_way_to_learn,
                                "interested_topic": user.interested_topic,
                                "upscaling_reason": user.upscaling_reason,
                                "time_spend": user.time_spend
                            },
                            "success": True,
                            "message": "OTP match",
                        }
                        try:
                            print("QP of the api", request.query_params)
                            username = request.query_params['username']
                            email = request.query_params['email']
                            coupon = request.query_params['coupon']
                            user = User.objects.filter(username=username, email=email).first()
                            applyCouponCode(user, coupon)
                            print("Template was sent")
                        except Exception as e:
                            print("Exception error in Qp", e)
                        return Response(response, status=status.HTTP_200_OK)

                return Response({"otp": "Otp Verification failed",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class AddReferalCode(APIView):
    serializer_class = ReferalSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            id = request.data['user_id']
            associated_users = User.objects.filter(Q(id=id))
            print("associated_users", associated_users)

            if associated_users.exists():
                User.objects.filter(id=id).update(referral_code=request.data['referal_code'])
                return Response({"message": "Update", "success": True}, status=status.HTTP_200_OK)
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    # type = UserTypes.objects.get(type="Learner")
    queryset = User.objects.filter(is_active=True, is_superuser=False, is_staff=False)
    serializer_class = UserProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        # do your customization here
        instance = self.get_object()
        profile_data = get_user_profile_data(instance)
        response = {
            "message": "Select",
            "success": True,
            "data": profile_data
        }
        return Response(response, status=status.HTTP_200_OK)

    def list(self, request):
        response = {'message': 'function is not offered in this path.', "success": False}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request):
        response = {'message': 'Create function is not offered in this path.', "success": False}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class IndustryExpertiseList(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['user_id'], is_active=True, is_superuser=False, is_staff=False)
        except User.DoesNotExist:
            return Response({"message": "user doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        industrys = Industry.objects.filter(is_active=True)
        industry_list = [{"id": industry.id, "name": industry.name} for industry in industrys]
        expertises = Tags.objects.filter(is_active=True)
        expertise_list = [{"id": expertise.id, "name": expertise.name, "color": expertise.color} for expertise in expertises]
        response = {
            "message": "UserProfileData of Industries and Expertise",
            "success": True,
            "industry_list":industry_list,
            "expertise_list": expertise_list
        }
        return Response(response, status=status.HTTP_200_OK)


class ProfileAssestQuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = User.objects.filter(is_active=True, is_superuser=False, is_staff=False)
    # serializer_class = ProfileAssestQuestionSerializer
    http_method_names = ['get']

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance)
        type = self.request.query_params.get('type') or "Learner"
        print(type)
        profile_assessment = ProfileAssestQuestion.objects.filter(question_for=type, is_active=True, is_delete=False)
        user_assest = UserProfileAssest.objects.filter(user=instance, assest_question__in=profile_assessment)
        data = []
        if user_assest:
            for assessment in user_assest:
                data.append({
                    "question_id": assessment.assest_question.id,
                    "question": assessment.assest_question.question,
                    "journey": assessment.assest_question.journey,
                    "options": assessment.assest_question.options,
                    "response": assessment.response,
                    "description": assessment.description,
                    "question_type": assessment.assest_question.question_type,
                    "question_for": assessment.assest_question.question_for,
                    "is_active": assessment.assest_question.is_active,
                    "is_delete": assessment.assest_question.is_delete,
                    "is_multichoice": assessment.assest_question.is_multichoice,
                    "display_order": assessment.assest_question.display_order
                })
        else:
            for assessment in profile_assessment:
                data.append({
                    "question_id": assessment.id,
                    "question": assessment.question,
                    "journey": assessment.journey,
                    "options": assessment.options,
                    "response": "",
                    "description": "",
                    "question_type": assessment.question_type,
                    "question_for": assessment.question_for,
                    "is_active": assessment.is_active,
                    "is_delete": assessment.is_delete,
                    "is_multichoice": assessment.is_multichoice,
                    "display_order": assessment.display_order
                })

        response = {
            # this is the default result you are getting today
            'data': data,
            "user_id": instance.id,
            "message": "Assest Question",
            "success": True

        }
        return Response(response, status=status.HTTP_200_OK)


class UserProfileAssestApiView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserProfileAssestSerializer
    http_method_names = ['post']


class UserProfileAssestAnswerView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserProfileAssestSerializer

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['user_id'], is_active=True, is_superuser=False, is_staff=False)
        except User.DoesNotExist:
            return Response({"message": "user doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        type = self.request.query_params.get('type') or "Learner"
        assesst_answer = UserProfileAssest.objects.filter(user=user, assest_question__question_for=type)
        print("assesst_answer ", assesst_answer)
        data = []
        for ans in assesst_answer:
            data.append({
                "ques_id": ans.assest_question.id,
                "question": ans.assest_question.question,
                "ans_id": ans.id,
                "answer": ans.response,
                "description": ans.description,
                "user": ans.user.id,
                "question_for": ans.question_for,
                "created_at": ans.created_at,
                "updated_at": ans.updated_at,
            })
        response = {
            # this is the default result you are getting today
            # 'data': UserProfileAssestSerializer(assesst_answer, many=True).data,
            "data": data,
            "message": "Assest Question_answer",
            "success": True
        }
        return Response(response, status=status.HTTP_200_OK)


class EditUserProfileAssest(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = UserProfileAssestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(id=request.data['user'], is_active=True, is_superuser=False, is_staff=False)
            except User.DoesNotExist:
                return Response({"message": "user doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            type = self.request.query_params.get('type') or "Learner"
            assesst_response = UserProfileAssest.objects.filter(
                user=user, assest_question__question_for=type, assest_question__id=request.data['assest_question'])
            assesst_response.update(response=request.data['response'])
            response = {
                # this is the default result you are getting today
                'data': UserProfileAssestSerializer(assesst_response, many=True).data,
                "message": "Edit_Assest Question_answer",
                "success": True
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HomePageApiView(APIView):
    def get(self, request, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['pk'])
            if not self.request.query_params.get('company_id'):
                return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                company = Company.objects.get(id=self.request.query_params.get('company_id'))
            except Company.DoesNotExist:
                return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            categories = all_categories_list()
            recommand_journey = []
            all_journey = public_channel_list(user, company.id)
            print(all_journey)
            journey_list = []
            for journey in all_journey:
                journey = journey['channel']
                user_status = UserChannel.objects.filter(user=user, Channel=journey)
                if user_status.count() > 0:
                    user_status = user_status.first()
                    user_status_data = user_status.status
                else:
                    user_status_data = "Enroll"
                journey_list.append({
                    "id": journey.pk,
                    "title": journey.title,
                    "color": journey.color,
                    "category": journey.category.category if journey.category else "",
                    "journey_type": journey.channel_type,
                    "short_description": journey.short_description,
                    "is_assessment_required": journey.is_test_required,
                    "assessment_id": journey.test_series.pk if journey.test_series else "",
                    "survey_id": journey.survey.pk if journey.survey else "",
                    "is_community_required": journey.is_community_required,
                    "user_status": user_status_data,
                    "duration": "2 Week",
                    "tags": journey.tags.split(",")
                })
            response = {
                "message": "Get data",
                "success": True,
                "data": {
                    "categories": categories,
                    "recommand_journey": journey_list,
                    "all_journey": journey_list
                }
            }
            return Response(response, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)


class CategoryJourney(APIView):
    def post(self, request):
        serializer = CategoryJourneySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                try:
                    company = Company.objects.get(id=request.data['company_id'])
                except Company.DoesNotExist:
                    return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
                user = User.objects.get(id=request.data['user_id'])
                all_journey = public_channel_list(user, company.id)
                category = request.data['category']
                print(all_journey)
                journey_list = []
                for journey in all_journey:
                    journey = journey['channel']
                    try:
                        user_status = UserChannel.objects.get(user=user, Channel=journey)
                        user_status_data = user_status.status
                    except UserChannel.DoesNotExist:
                        user_status_data = "Enroll"
                    if journey.category != None:
                        if category == journey.category.category:
                            journey_list.append({
                                "id": journey.pk,
                                "title": journey.title,
                                "color": journey.color,
                                "category": journey.category.category if journey.category else "",
                                "journey_type": journey.channel_type,
                                "short_description": journey.short_description,
                                "is_assessment_required": journey.is_test_required,
                                "assessment_id": journey.test_series.pk if journey.test_series else "",
                                "survey_id": journey.survey.pk if journey.survey else "",
                                "is_community_required": journey.is_community_required,
                                "user_status": user_status_data,
                                "duration": "2 Week",
                                "tags": journey.tags.split(",")
                            })
                response = {
                    "message": "Get data",
                    "success": True,
                    "data": {
                        "all_journey": journey_list
                    }
                }
                return Response(response, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "serializer.errors", "success": False}, status=status.HTTP_400_BAD_REQUEST)


class JourneyDetails(APIView):
    def get(self, request, *args, **kwargs):
        try:
            if not self.request.query_params.get('company_id'):
                return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                company = Company.objects.get(id=self.request.query_params.get('company_id'))
            except Company.DoesNotExist:
                return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            journey = Channel.objects.get(pk=self.kwargs['journey'])
            print(journey)
            user = User.objects.get(id=self.kwargs['user_id'])
            all_journey = public_channel_list(user, company.id)
            print(all_journey)
            journey_list = []
            for all_journey in all_journey:
                all_journey = all_journey['channel']
                try:
                    user_status = UserChannel.objects.get(user=user, Channel=all_journey)
                    user_status_data = user_status.status
                except UserChannel.DoesNotExist:
                    user_status_data = "Enroll"
                journey_list.append({
                    "id": all_journey.pk,
                    "title": all_journey.title,
                    "color": all_journey.color,
                    "category": all_journey.category.category if all_journey.category else "",
                    "journey_type": all_journey.channel_type,
                    "short_description": all_journey.short_description,
                    "is_assessment_required": all_journey.is_test_required,
                    "assessment_id": all_journey.test_series.pk if all_journey.test_series else "",
                    "survey_id": all_journey.survey.pk if all_journey.survey else "",
                    "is_community_required": all_journey.is_community_required,
                    "user_status": user_status_data,
                    "duration": "2 Week",
                    "tags": journey.tags.split(",")
                })
            try:
                user_status = UserChannel.objects.get(user=user, Channel=journey)
                user_status_data = user_status.status

            except UserChannel.DoesNotExist:
                user_status_data = "Enroll"

            if journey.channel_type == "SkillDevelopment":
                skills = Channel.objects.filter(parent_id=journey)
                content = []
                for skills in skills:
                    content.append({
                        "skill_id": skills.pk,
                        "skill": skills.title,
                        "read_status": get_journey_content(skills, user)[1],
                        "pre_assessment": skills.test_series.pk if skills.test_series else "",
                        "is_pre_assessment_required": skills.is_test_required,
                        "data": get_journey_content(skills, user)[0]
                    })

            elif journey.channel_type == "MentoringJourney":
                content_list = []
                content_image = ""
                journey_group = ChannelGroup.objects.filter(channel=journey, is_delete=False).first()
                mentoring_journey = MentoringJourney.objects.filter(journey=journey, journey_group=journey_group, is_delete=False)
                for mentoring_journey in mentoring_journey:
                    type = mentoring_journey.meta_key
                    read_status = ""
                    if type == "quest":
                        content = Content.objects.get(pk=mentoring_journey.value)
                        content_image = content.image.url
                        try:
                            user_read_status = UserCourseStart.objects.get(
                                user=user, content=content, channel_group=mentoring_journey.journey_group, channel=journey.pk)
                            read_status = user_read_status.status
                        except UserCourseStart.DoesNotExist:
                            read_status = ""
                    elif type == "assessment":
                        test_series = TestSeries.objects.get(pk=mentoring_journey.value)
                        test_attempt = TestAttempt.objects.filter(
                            test=test_series, user=user, channel=mentoring_journey.journey)
                        if test_attempt.count() > 0:
                            read_status = "Complete"
                    elif type == "survey":
                        survey = Survey.objects.get(pk=mentoring_journey.value)
                        survey_attempt = SurveyAttempt.objects.filter(
                            survey=survey, user=user)
                        if survey_attempt.count() > 0:
                            read_status = "Complete"

                    elif type == "journals":
                        weekely_journals = WeeklyLearningJournals.objects.get(
                            pk=mentoring_journey.value, journey_id=journey.pk)
                        learnig_journals = LearningJournals.objects.filter(is_draft=False,
                            weekely_journal_id=weekely_journals.pk, journey_id=journey.pk, email=user.email)
                        if learnig_journals.count() > 0:
                            read_status = "Complete"
                    else:
                        content_image = ""

                    content_list.append({
                        "id": mentoring_journey.value,
                        "type": mentoring_journey.meta_key,
                        "level":  "",
                        "journey_group": journey_group.pk,
                        "display_order": mentoring_journey.display_order,
                        "title": mentoring_journey.name,
                        "image": content_image,
                        "id": mentoring_journey.value,
                        "journey_id": mentoring_journey.journey.pk,
                        "read_status": read_status
                    })
                content = content_list
            else:
                content = get_journey_content(journey, user)[0]
            community = {}
            if journey.is_community_required:
                space_journey = SpaceJourney.objects.filter(journey = journey).first()
                community= {
                    "space_id":space_journey.space.id,
                    "space_group_id": space_journey.space.space_group.id,
                    "space_name": space_journey.space.title,
                    "space_group_name": space_journey.space.space_group.title
                }
                

            journey = {
                "id": journey.pk,
                "title": journey.title,
                "color": journey.color,
                "category": journey.category.category if journey.category else "",
                "journey_type": journey.channel_type,
                "banner": journey.image.url if journey.image else "",
                "short_description": journey.short_description,
                "description": journey.description,
                "is_assessment_required": journey.is_test_required,
                "assessment_id": journey.test_series.pk if journey.test_series else "",
                "survey_id": journey.survey.pk if journey.survey else "",
                "is_community_required": journey.is_community_required,
                "community": community,
                "user_status": user_status_data,
                "duration": "2 Week",
                "tags": journey.tags.split(","),
                "author": {
                    "first_name": journey.created_by.first_name,
                    "last_name": journey.created_by.last_name,
                    "avatar": "http://ec2-3-19-29-240.us-east-2.compute.amazonaws.com:8000/static/dist/img/avatar.png",
                    "heading": journey.created_by.profile_heading,
                    "about_us": journey.created_by.about_us,
                },
                "journey_content": content,
                "what_you_will_learn": journey.what_we_learn.split(","),
                "recommand_journey": journey_list

            }
            response = {
                "message": "Get data",
                "success": True,
                "data": {
                    "journey": journey,
                }
            }
            return Response(response, status=status.HTTP_200_OK)

        except Channel.DoesNotExist:
            return Response({"message": "Journey not found", "success": False}, status=status.HTTP_404_NOT_FOUND)


class JourneyAssessment(APIView):
    def post(self, request):
        data = request.data
        serializer = AssessmentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            assessment_id = data['assessment_id']
            journey_type = data["journey_type"]
            if journey_type == "SkillDevelopment" or journey_type == "MentoringJourney":
                test_series = TestSeries.objects.get(pk=assessment_id)
                test_question = TestQuestion.objects.filter(survey=test_series)
                data = []
                for test_question in test_question:
                    test_options = TestOptions.objects.filter(question=test_question)
                    options_list = []
                    for test_options in test_options:
                        options_list.append(test_options.option)
                    data.append({
                        "id": test_question.id,
                        "title": test_question.title,
                        "type": test_question.type,
                        "options": options_list,
                        "is_required": test_question.is_required,
                        "display_order": test_question.display_order,
                        "image": ques_image(test_question)
                    })
            response = {
                "message": "Get data",
                "success": True,
                "data": {
                    "id": test_series.id,
                    "assessment": test_series.name,
                    "question": data
                }
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": "serializer.errors", "success": False}, status=status.HTTP_400_BAD_REQUEST)


class SubmitAssessment(APIView):
    def post(self, request):
        data = request.data
        print("data:", data)
        serializer = JourneyAssesmentResponseSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # try:
            type = request.data['type']
            skill_id = request.data.get('skill_id') or None
            quest_id = request.data.get('quest_id')
            assessment_id = request.data['assessment_id']
            journey = request.data["journey_id"]
            question = request.data['questions']
            try:
                user = User.objects.get(pk=request.data["user_id"])
                print(user)
            except User.DoesNotExist:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            try:
                test_series = TestSeries.objects.get(pk=assessment_id)
            except TestSeries.DoesNotExist:
                return Response({"message": "Enter Valid Assessment Id", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            try:
                channel = Channel.objects.get(pk=journey)
            except Channel.DoesNotExist:
                return Response({"message": "Enter Valid Journey Id", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            channel_group = ChannelGroup.objects.filter(channel=channel, is_delete=False)
            test_attempt = TestAttempt.objects.create(
                user=user, channel=channel, test=test_series, type=type, skill_id=skill_id, quest_id=quest_id)
            test_marks = 0
            total_marks = 0
            op_marks, check_marks = 0, 0
            if not isinstance(question, list):
                question = ast.literal_eval(question)
            for i in question:
                question_ins = TestQuestion.objects.get(pk=i["q_id"])
                test_marks += question_ins.marks
                print("test_marks ", test_marks)
                print("question_ins.type ", question_ins.type)
                print("question_ins.marks ", question_ins.marks)
                if question_ins.type == 'ShortAnswer':
                    UserTestAnswer.objects.create(user=user, question=question_ins, question_marks=question_ins.marks,
                                                  test_attempt=test_attempt, response=i["response"])

                elif question_ins.type == 'Checkbox':
                    print("ques_response", i["response"])
                    res = i["response"].split(",")
                    print("res", res)
                    temp = []
                    for j in res:
                        print(j)
                        option_marks = TestOptions.objects.get(question=question_ins, option=j)
                        print(option_marks)
                        check_marks += option_marks.marks
                        temp.append(option_marks.pk)
                    UserTestAnswer.objects.create(user=user, question=question_ins, question_marks=question_ins.marks,
                                                  test_attempt=test_attempt, response=temp, total_marks=check_marks)

                else:
                    option_marks = TestOptions.objects.get(question=question_ins, option=i["response"])
                    op_marks += option_marks.marks

                    UserTestAnswer.objects.create(user=user, question=question_ins, question_marks=question_ins.marks,
                                                  test_attempt=test_attempt, response=i["response"], total_marks=option_marks.marks)
                    total_marks = op_marks+check_marks
                    print("total_marks ", total_marks)

            if test_series.auto_check == False:
                total_marks = 0
                user_skill = None
            else:
                test_attempt_marks = math.ceil((total_marks/test_marks)*100)
                channel_group = ChannelGroup.objects.filter(
                    start_mark__lte=test_attempt_marks, end_marks__gte=test_attempt_marks)

                channel_group = channel_group.first()
                user_skill = channel_group.channel_for
                print("user_skill ", user_skill)
                test_attempt.is_check = True
                if user_skill:
                    UserChannelLevel.objects.create(test_attempt=test_attempt, user=user, type="Assessment",
                                                    skill_level=user_skill.label, channel=channel)
                # user_channel = UserChannel.objects.filter(status="Joined", user=user).first()
                # print("user_channel ", user_channel)
                # if user_channel is None:
                #     respo = "Joined"
                #     UserChannel.objects.create(user=user, Channel=channel, status=respo)

            test_attempt.total_marks = total_marks
            test_attempt.test_marks = test_marks
            test_attempt.user_skill = user_skill
            test_attempt.save()

            SubmitPreFinalAssessment(user=user, test_attempt=test_attempt.type, channel=channel.pk, userType=request.session['user_type'])

            response = {
                "success": True,
                "message": "Submit Successfully",
                "data": {
                    "attempt_id": test_attempt.pk
                }
            }
            return Response(response, status=status.HTTP_200_OK)
            # except Exception as e:
            #     print(e)
            return Response({"message": "Something Went Wrong", "success": False}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class JourneyDetailsAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            journey = Channel.objects.get(pk=self.kwargs['journey'])
            try:
                user = User.objects.get(id=self.kwargs['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
            all_journey = public_channel_list(user)
            # print(all_journey)
            journey_list = []
            for channel in all_journey:
                channel = channel['channel']
                try:
                    user_status = UserChannel.objects.get(user=user, Channel=channel)
                    user_status_data = user_status.status
                except UserChannel.DoesNotExist:
                    user_status_data = "Enroll"
                journey_list.append({
                    "id": channel.pk,
                    "title": channel.title,
                    "color": channel.color,
                    "category": channel.category.category if channel.category else "",
                    "journey_type": channel.channel_type,
                    "short_description": channel.short_description,
                    "is_assessment_required": channel.is_test_required,
                    "assessment_id": channel.test_series.pk if channel.test_series else "",
                    "survey_id": channel.survey.pk if channel.survey else "",
                    "is_community_required": channel.is_community_required,
                    "user_status": user_status_data,
                    "duration": "2 Week",
                    "tags": channel.tags.split(",")
                })
            try:
                user_status = UserChannel.objects.get(user=user, Channel=journey)
                user_status_data = user_status.status
            except UserChannel.DoesNotExist:
                user_status_data = "Enroll"

            if journey.channel_type == "SkillDevelopment":
                skills = Channel.objects.filter(parent_id=journey, is_active=True, is_delete=False)
                content = []
                # print("skills", skills)
                assessment_status = ""
                for skill in skills:
                    assessment_attempt = TestAttempt.objects.filter(
                        user=user, channel=skill.parent_id, skill_id=skill.id, test=skill.test_series)
                    # print(assessment_attempt)
                    if len(assessment_attempt) > 0:
                        assessment_status = "Complete"
                    content.append({
                        "skill_id": skill.pk,
                        "skill": skill.title,
                        "read_status": get_journey_content(skill, user)[1],
                        "pre_assessment": skill.test_series.pk if skill.is_test_required and skill.test_series else "",
                        "assessment_status": assessment_status,
                        "is_pre_assessment_required": skill.is_test_required,
                        "data": get_journey_content(skill, user)[0]
                    })
                    progress = get_journey_progress(skill, user)
            elif journey.channel_type == "MentoringJourney":
                content_list = []
                content_image = ""
                progress_list = []
                journey_group = ChannelGroup.objects.filter(channel=journey, is_delete=False).first()
                mentoring_journey = MentoringJourney.objects.filter(
                    journey=journey, journey_group=journey_group, is_delete=False).order_by('display_order')
                for mentoring_journey in mentoring_journey:
                    type = mentoring_journey.meta_key
                    read_status = ""
                    start_time = ""
                    if type == "quest":
                        content = Content.objects.get(pk=mentoring_journey.value)
                        content_image = content.image.url
                        try:
                            user_read_status = UserCourseStart.objects.get(
                                user=user, content=content, channel_group=mentoring_journey.journey_group, channel=journey.pk)
                            read_status = user_read_status.status
                            start_time = user_read_status.created_at
                        except UserCourseStart.DoesNotExist:
                            read_status = ""
                    elif type == "assessment":
                        test_series = TestSeries.objects.get(pk=mentoring_journey.value)
                        test_attempt = TestAttempt.objects.filter(
                            test=test_series, user=user, channel=mentoring_journey.journey)
                        if test_attempt.count() > 0:
                            read_status = "Complete"
                            start_time = test_attempt.first().created_at

                    elif type == "survey":
                        survey = Survey.objects.get(pk=mentoring_journey.value)
                        survey_attempt = SurveyAttempt.objects.filter(
                            survey=survey, user=user)
                        if survey_attempt.count() > 0:
                            read_status = "Complete"
                            start_time = survey_attempt.first().created_at

                    elif type == "journals":
                        weekely_journals = WeeklyLearningJournals.objects.get(
                            pk=mentoring_journey.value, journey_id=journey.pk)
                        learnig_journals = LearningJournals.objects.filter(is_draft=False,
                            weekely_journal_id=weekely_journals.pk, journey_id=journey.pk, email=user.email)
                        if learnig_journals.count() > 0:
                            read_status = "Complete"
                            start_time = learnig_journals.first().created_at

                    else:
                        content_image = ""

                    content_list.append({
                        "id": mentoring_journey.value,
                        "type": mentoring_journey.meta_key,
                        "level":  "",
                        "journey_group": journey_group.pk,
                        "display_order": mentoring_journey.display_order,
                        "title": mentoring_journey.name,
                        "image": content_image,
                        "id": mentoring_journey.value,
                        "journey_id": mentoring_journey.journey.pk,
                        "read_status": read_status
                    })
                    progress_list.append({
                        "content": mentoring_journey.name,
                        "status": read_status,
                        "type": mentoring_journey.meta_key,
                        "start_time": start_time,
                        "week_delayed": "",
                        "display_order": mentoring_journey.display_order,
                        "journey_group": journey_group.pk,
                        "quest_id": mentoring_journey.value
                    })
                content = content_list
                progress = progress_list
            else:
                content = get_journey_content(journey, user)[0]

                progress = get_journey_progress(journey, user)

            community = {}
            if journey.is_community_required:
                space_journey = SpaceJourney.objects.filter(journey=journey).first()
                community = {
                    "space_id": space_journey.space.id,
                    "space_group_id": space_journey.space.space_group.id,
                    "space_name": space_journey.space.title,
                    "space_group_name": space_journey.space.space_group.title
                }
            journey = {
                "id": journey.pk,
                "title": journey.title,
                "color": journey.color,
                "category": journey.category.category if journey.category else "",
                "journey_type": journey.channel_type,
                "banner": journey.image.url if journey.image else "",
                "short_description": journey.short_description,
                "description": journey.description,
                "is_assessment_required": journey.is_test_required,
                "assessment_id": journey.test_series.pk if journey.test_series else "",
                "survey_id": journey.survey.pk if journey.survey else "",
                "is_community_required": journey.is_community_required,
                "community": community,
                "user_status": user_status_data,
                "duration": "2 Week",
                "tags": journey.tags.split(","),
                "author": {
                    "first_name": journey.created_by.first_name,
                    "last_name": journey.created_by.last_name,
                    "avatar": "http://ec2-3-19-29-240.us-east-2.compute.amazonaws.com:8000/static/dist/img/avatar.png",
                    "heading": journey.created_by.profile_heading,
                    "about_us": journey.created_by.about_us,
                },

                "what_you_will_learn": journey.what_we_learn.split(","),

            }

            response = {
                "message": "Get data",
                "success": True,
                "data": {
                    "journey": journey,
                    "quest": [] if user_status_data == "Enroll" else content,
                    "progress": progress,
                }
            }
            return Response(response, status=status.HTTP_200_OK)
        except Channel.DoesNotExist:
            return Response({"message": "Journey not found", "success": False}, status=status.HTTP_404_NOT_FOUND)


@permission_classes((AllowAny,))
class QuestSummary(APIView):
    def post(self, request, *args, **kwargs):
        try:
            quest = Content.objects.get(pk=request.data['quest_id'])
            journey_group = ChannelGroup.objects.get(pk=request.data['journey_group'])

            user = User.objects.get(id=request.data['user_id'])
            channel_group_content = ChannelGroupContent.objects.filter(
                channel_group=journey_group, content=quest, is_delete=False).first()
            print(channel_group_content)
            if not channel_group_content:
                return Response({"message": "Content not available", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            content_data = ContentData.objects.filter(content=channel_group_content.content)
            course_start = UserCourseStart.objects.filter(
                user=user, content=channel_group_content.content, channel_group=journey_group, channel=journey_group.channel).first()
            print(course_start)
            InProgress = 0
            Complete = 0
            temp = 0
            channel_group_content_list = []
            if course_start is not None:
                print("course_start", course_start)
                read_status = course_start.status

                if read_status == "InProgress":
                    InProgress = InProgress+1
                elif read_status == "Complete":
                    Complete = Complete + 1
                else:
                    temp = temp + 1

            else:
                read_status = ""

            content_data_list = []
            channel_group_content_list = []
            for content_data in content_data:
                content_data_list.append({
                    "id": content_data.id,
                    "title": content_data.title,
                    "read_status": read_status,
                    "time": content_data.time
                })

            channel_group_content_list.append({
                "id": channel_group_content.content.pk,
                "level": journey_group.channel_for.label if journey_group.channel_for else "",
                "journey_group": journey_group.pk,
                "content": channel_group_content.content.title,
                "data": content_data_list,
                "read_status": read_status,
                "post_assessment": journey_group.post_assessment.pk if journey_group.post_assessment else "",
            })

            response = {
                "message": "Get data",
                "success": True,
                "data": {
                    "quest": channel_group_content_list,

                }
            }
            return Response(response, status=status.HTTP_200_OK)

        except Content.DoesNotExist:
            return Response({"message": "quest not found", "success": False}, status=status.HTTP_404_NOT_FOUND)


class UnlockJourney(APIView):
    def post(self, request):
        data = request.data
        serializer = UnlockJourneySerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(pk=data['user_id'])
            try:
                journey = Channel.objects.get(pk=serializer.validated_data['journey_id'])
            except:
                return Response({"message": "Invalid Journey", "success": False}, status=status.HTTP_404_NOT_FOUND)

            user_channel = UserChannel.objects.filter(user=user, Channel=journey).first()
            print("user_channel ", user_channel)
            if not user_channel:
                respo = "Joined"
                user_channel = UserChannel.objects.create(user=user, Channel=journey, status=respo)
                add_user_to_company(user, journey.company)
                context = {
                    "screen":"ProgramJourney",
                    "navigationPayload": { 
                        "courseId": str(journey.id)
                    }
                }
                send_push_notification(user, journey.title, f"You're enrolled in {journey.title}", context)
                NotificationAndPoints(user, "joined journey")
                if journey.whatsapp_notification_required and (user.phone and user.is_whatsapp_enable):
                    journey_enrolment(user, journey)
                else:
                    print("phone does not exist")
                if journey.is_community_required:
                    add_member_to_space(journey, user)
                # if user_channel:
                #     NotificationAndPoints(user, "joined journey")
                return Response({"message": "Unlock Journey", "success": True}, status=status.HTTP_200_OK)
            elif user_channel.is_removed:
                return Response({"message": "You're removed from this journey", "success": False}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Already Joined", "success": False}, status=status.HTTP_200_OK)

        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class AssessmentAnswer(APIView):
    def post(self, request):
        data = request.data
        serializer = AssessmentAttemptSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(pk=data['user_id'])
            test_attempt = TestAttempt.objects.filter(pk=data['attempt_id'], user=user)
            if test_attempt.count() > 0:
                test_attempt = test_attempt.first()
                responses = []
                detils_list = []
                for attempt in test_attempt.test_attempet_answer.all():
                    attempt_response = attempt.response
                    option_list = []
                    if attempt.question.type in ["DropDown", "Checkbox", "MultiChoice"]:
                        option_list = TestOptions.objects.filter(question = attempt.question)
                        option_list = [(option.option, option.correct_option) for option in option_list]
                    if attempt.question.type == "Checkbox":
                        ids = ast.literal_eval(attempt.response)
                        print(ids)
                        temp = TestOptions.objects.filter(pk__in=ids)
                        print("TEMP", temp)
                        # for t in temp:
                        #     responses.append((t.option, t.correct_option))
                        responses = [temp.option for temp in temp]
                        res1 = ''
                        for res in responses:
                            res1 = f"{res1}, {res}" if res1 != "" else f"{res1}{res}"
                        attempt_response = res1
                    detils_list.append({
                        "attemp_id": attempt.test_attempt.pk,
                        "question": attempt.question.title,
                        "answer": attempt_response,
                        "question_marks": attempt.question_marks,
                        "given_marks": attempt.total_marks,
                        "options": option_list,
                    })
                return Response({"message": "Get", "data": detils_list, "success": True}, status=status.HTTP_200_OK)
            return Response({"message": "User attempt not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class QuestContentLearn(APIView):
    def post(self, request):
        data = request.data

        serializer = QuestContentSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(pk=data['user_id'])
            quest_id = data['quest_id']
            content = Content.objects.get(pk=data['quest_id'])
            channel_group = ChannelGroup.objects.get(pk=data['journey_group'])
            channel = Channel.objects.get(pk=channel_group.channel.pk)

            parent_check = is_parent_channel(channel_group.channel.pk)

            learning_journals = LearningJournals.objects.filter(
                journey_id=parent_check['channel_id'], microskill_id=quest_id, email=user.email).first()
            print(learning_journals)
            if channel.channel_type == "SkillDevelopment":
                if channel_group.post_assessment.pk is None:
                    go_next = "None"
                else:
                    go_next = {
                        "type": "Assessment",
                        'post_assessment_id': channel_group.post_assessment.pk, 'channel': channel.pk, "quest_id": "", "journey_group": ""}
            else:

                display_content = ChannelGroupContent.objects.get(channel_group=channel_group, content=content, is_delete=False)
                order = display_content.display_order + 1
                try:
                    channel_content = ChannelGroupContent.objects.get(channel_group=channel_group, display_order=order, is_delete=False)

                    go_next = {
                        "type": "Quest",
                        'quest_id': channel_content.content.pk, 'journey_group': channel_group.pk, "post_assessment_id": "", "journey": ""
                    }
                except:
                    go_next = "None"

            if channel.channel_type == "SkillDevelopment":
                go_previous = None
            else:

                display_content = ChannelGroupContent.objects.get(channel_group=channel_group, content=content, is_delete=False)
                order = display_content.display_order - 1
            try:
                channel_content = ChannelGroupContent.objects.get(channel_group=channel_group, display_order=order, is_delete=False)

                go_previous = reverse_lazy('content:read_content', kwargs={
                    'pk': channel_content.content.pk, 'group': channel_group.pk})
            except:
                go_previous = None
            result = []
            content_data = ContentData.objects.filter(content=quest_id).order_by("display_order")
            data = Paginator(content_data, 1)

            page_number = request.GET.get('page')

            try:
                page_obj = data.get_page(page_number)  # returns the desired page object
            except PageNotAnInteger:
                # if page_number is not an integer then assign the first page
                page_obj = data.page(1)
            except EmptyPage:
                page_obj = data.page(data.num_pages)
            user_course = UserCourseStart.objects.filter(
                user=user, content=quest_id, channel=channel, channel_group=channel_group)

            if user_course.count() == 0:
                UserCourseStart.objects.create(user=user, content=content,
                                               channel=channel, channel_group=channel_group, status="InProgress")

            data = page_obj[0]
            if data.display_order == 0:
                previous_order = data.display_order
            else:
                previous_order = data.display_order - 1

            try:
                UserReadContentData.objects.create(channel=channel, content=content,
                                                   content_data=data, channel_group=channel_group,  user=user)

            except:
                pass

            if previous_order != 0:
                get_previous_content = ContentData.objects.get(content=content, display_order=previous_order)
                UserReadContentData.objects.filter(
                    user=user, channel=channel, content=content, channel_group=channel_group, content_data=get_previous_content).update(status="Complete")

            content_data_option = ContentDataOptions.objects.filter(content_data=data)
            response = []
            options = []
            if data.type == "Poll":
                for cd_option in content_data_option:

                    check_user = ContetnOptionSubmit.objects.filter(user=user, content_data=data)

                    options.append({
                        "id": cd_option.id,
                        "option": cd_option.option,
                    })
                    if check_user.count() > 0:
                        get_user_result = ContetnOptionSubmit.objects.filter(content_data=data)
                        total_answer = get_user_result.count()
                        count = get_user_result.filter(option=cd_option.option).count()

                        if count == 0:
                            avg_count = 0
                        else:
                            avg_count = (count/total_answer)*100

                        response.append({
                            "id": cd_option.id,
                            "option": cd_option.option,
                            "count": avg_count,
                            "my_response": True
                        })
            elif data.type == "Quiz":
                # get_user_result = ContetnOptionSubmit.objects.filter(content_data=data,  user=self.request.user)

                #     get_user_result = get_user_result.first()
                content_data_options = ContentDataOptions.objects.filter(content_data=data)
                for cd_option in content_data_options:
                    check_user = ContetnOptionSubmit.objects.filter(user=user, content_data=data)

                    options.append({
                        "id": cd_option.id,
                        "option": cd_option.option,
                    })
                    print("check_user.count()", check_user.count())
                    if check_user.count() > 0:
                        get_user_result = ContetnOptionSubmit.objects.filter(content_data=data,  user=user)
                        print(get_user_result)
                        get_user_result = get_user_result.first()
                        content_data_options = ContentDataOptions.objects.filter(
                            content_data=data, correct_answer=True).first()

                        response = {
                            "option":  content_data_options.option,
                            "my_answer": get_user_result.option,
                            "is_true": True if cd_option.option == get_user_result.option else False
                        }
            user_read_status = UserReadContentData.objects.filter(
                user=self.request.user, channel=channel, content=content, content_data=data, channel_group=channel_group)
            if user_read_status.count() > 0:
                read_status = user_read_status[0].status
            else:
                read_status = ""
            print(read_status)
            #  if data.type != "Link" else "YtVideo",
            result.append({
                "id": data.id,
                "content": data.content.title,
                "title": data.title,
                "type": data.type,
                "data": data.data,
                "file": data.file.url if data.file else "",
                "video": data.video.url if data.video else "",
                "url": data.url,
                "display_order": data.display_order,
                "content_data_option": options,
                "poll_response": response,
                "read_status": read_status

            })
            # channel = Channel.objects.filter(parent_id=None)
            print(page_obj)
            content_data = {
                "title": content.title,
                "image": content.image.url if content.image else "",
                "description": content.description
            }
            learning_journals_list = {
                "id": learning_journals.id if learning_journals else 0,
                "name": learning_journals.name if learning_journals else "",
                "learning_journal": learning_journals.learning_journal if learning_journals else "",
                "user_name": learning_journals.user_name if learning_journals else "",
                "created_at": learning_journals.created_at if learning_journals else ""
            }
            next_page = page_obj.has_next() and page_obj.next_page_number() or None,
            previous = page_obj.has_previous() and page_obj.previous_page_number() or None
            response = {"journey_id": parent_check['channel_id'], "data": result, "previous_page": previous, "next_page": next_page,
                        "quest": content_data, "learning_journals": learning_journals_list, "go_next": go_next}
            return Response({"message": "get data", "data": response, "success": True}, status=status.HTTP_200_OK)
            # "go_next": go_next, ,
            #             "go_previous": go_previous,  "content_data": content_data, "mode": "Learn", "parent_check": parent_check, "learning_journals": learning_journals
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)


class QuestContentRevise(APIView):
    def post(self, request):
        data = request.data
        serializer = QuestContentSerializer(data=request.data)
        if serializer.is_valid():
            quest_id = data['quest_id']
            user = User.objects.filter(id=request.data['user_id']).first()
            print(user)
            try:
                content = Content.objects.get(pk=data['quest_id'])
            except Content.DoesNotExist:
                return Response({"message": "Invalid Channel Content id"}, status=status.HTTP_404_NOT_FOUND)

            try:
                channel_group = ChannelGroup.objects.get(pk=data['journey_group'])
                print(channel_group)
            except ChannelGroup.DoesNotExist:
                return Response({"message": "Invalid Channel group id"}, status=status.HTTP_404_NOT_FOUND)

            channel = Channel.objects.get(pk=channel_group.channel.pk)
            print(channel)
            parent_check = is_parent_channel(channel_group.channel.pk)
            learning_journals = LearningJournals.objects.filter(
                journey_id=parent_check['channel_id'], microskill_id=quest_id, email=request.user.email).first()
            print(learning_journals)
            if channel.channel_type == "SkillDevelopment":
                go_next = "None"
            else:

                display_content = ChannelGroupContent.objects.get(channel_group=channel_group, content=content)
                order = display_content.display_order + 1
                try:
                    channel_content = ChannelGroupContent.objects.get(channel_group=channel_group, display_order=order)

                    go_next = {
                        "type": "Quest",
                        'pk': channel_content.content.pk,
                        'group': channel_group.pk,
                        "quest_id": "", "journey_group": ""
                    }
                except:
                    go_next = "None"

            if channel.channel_type == "SkillDevelopment":
                go_previous = None
            else:

                display_content = ChannelGroupContent.objects.get(channel_group=channel_group, content=content)
                order = display_content.display_order - 1
                try:
                    channel_content = ChannelGroupContent.objects.get(channel_group=channel_group, display_order=order)

                    go_previous = reverse_lazy('content:read_content', kwargs={
                        'pk': channel_content.content.pk, 'group': channel_group.pk})
                except:
                    go_previous = None

            result = []
            data = ContentData.objects.filter(content=quest_id).order_by("display_order")
            user_course = UserCourseStart.objects.filter(
                user=request.user, content=quest_id, channel_group=channel_group, channel=channel)
            for data in data:
                content_data_option = ContentDataOptions.objects.filter(content_data=data)
                response = []
                options = []
                if data.type == "Poll":
                    for cd_option in content_data_option:
                        check_user = ContetnOptionSubmit.objects.filter(user=request.user, content_data=data)
                        options.append({
                            "id": cd_option.id,
                            "option": cd_option.option,
                        })
                        print(request.user)
                        if check_user.count() > 0:
                            get_user_result = ContetnOptionSubmit.objects.filter(content_data=data)
                            total_answer = get_user_result.count()
                            count = get_user_result.filter(option=cd_option.option).count()

                            if count == 0:
                                avg_count = 0
                            else:
                                avg_count = (count/total_answer)*100

                            response.append({
                                "id": cd_option.id,
                                "option": cd_option.option,
                                "count": avg_count,
                                "my_response": True
                            })
                elif data.type == "Quiz":
                    get_user_result = ContetnOptionSubmit.objects.filter(content_data=data,  user=self.request.user)
                    if get_user_result.count() > 0:
                        get_user_result = get_user_result.first()
                        content_data_options = ContentDataOptions.objects.filter(
                            content_data=data, correct_answer=True)
                        for cd_option in content_data_options:

                            response.append({
                                "option":  cd_option.option,
                                "my_answer": get_user_result.option,
                                "is_true": True if cd_option.option == get_user_result.option else False
                            })
                user_read_status = UserReadContentData.objects.filter(
                    user=self.request.user, channel=channel, content=content, content_data=data, channel_group=channel_group)
                if user_read_status.count() > 0:
                    read_status = user_read_status[0].status
                else:
                    read_status = ""
                    # if data.type != "Link" else "YtVideo",
                result.append({
                    "id": data.id,
                    "content": data.content.title,
                    "title": data.title,
                    "type": data.type,
                    "data": data.data,
                    "file": data.file.url if data.file else "",
                    "video": data.video.url if data.video else "",
                    "url": data.url,
                    "display_order": data.display_order,
                    "content_data_option": options,
                    "poll_response": response,
                    "read_status": read_status


                })
            content_data = {
                "title": content.title,
                "image": content.image.url if content.image else "",
                "description": content.description
            }

            learning_journals_list = {
                "id": learning_journals.id if learning_journals else '',
                "name": learning_journals.name if learning_journals else "",
                "learning_journal": learning_journals.learning_journal if learning_journals else "",
                "user_name": learning_journals.user_name if learning_journals else "",
                "created_at": learning_journals.created_at if learning_journals else ""
            }

            # channel = Channel.objects.filter(parent_id=None)
            response = {"journey_id": parent_check['channel_id'], "data": result,
                        "quest": content_data, "learning_journals": learning_journals_list, "go_next": go_next}
            return Response({"message": "get data", "data": response, "success": True}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class UserJoinedChannel(APIView):
    def get(self, request, *args, **kwargs):
        data = {"user_id": str(self.kwargs['user_id'])}
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        print(data)
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            user = User.objects.get(id=self.kwargs['user_id'])
            user_channels = UserChannel.objects.filter(user=user, Channel__is_active=True, Channel__is_delete=False, Channel__closure_date__gt=datetime.now(), Channel__company=company)
            journey_list = []
            journey_id_list = []
            for user_channels in user_channels:
                journey_id = user_channels.Channel.pk
                if not journey_id in journey_id_list:
                    journey_id_list.append(journey_id)
                    journey = Channel.objects.get(pk=journey_id)

                    journey_list.append({
                        "id": journey.pk,
                        "title": journey.title,
                        "color": journey.color,
                        "category": journey.category.category if journey.category else "",
                        "journey_type": journey.channel_type,
                        "short_description": journey.short_description,
                        "is_assessment_required": journey.is_test_required,
                        "assessment_id": journey.test_series.pk if journey.test_series else "",
                        "survey_id": journey.survey.pk if journey.survey else "",
                        "is_community_required": journey.is_community_required,
                        "user_status": user_channels.status,
                        "duration": "2 Week",
                        "tags": journey.tags.split(",")
                    })
            response = {
                "message": "Get data",
                "success": True,
                "data": {
                    "all_journey": journey_list
                }
            }
            return Response(response, status=200)
        return Response({"message": serializer.errors,  "success": False}, status=400)


class JourneySearchAPI(APIView):
    def post(self, request, **kwargs):
        data = request.data
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            if not self.request.query_params.get('company_id'):
                return Response({"message": "company_id is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                company = Company.objects.get(id=self.request.query_params.get('company_id'))
            except Company.DoesNotExist:
                return Response({"message": "Company_id does not exist",  "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user = User.objects.get(id=request.data['user_id'])
                all_journey = public_channel_list_search(user, request.data['search'], company.id)
                journey_list = []
                for journey in all_journey:
                    try:
                        user_status = UserChannel.objects.get(user=user, Channel=journey)
                        user_status_data = user_status.status
                    except UserChannel.DoesNotExist:
                        user_status_data = "Enroll"
                    journey_list.append({
                        "id": journey.pk,
                        "title": journey.title,
                        "color": journey.color,
                        "category": journey.category.category if journey.category else "",
                        "journey_type": journey.channel_type,
                        "short_description": journey.short_description,
                        "is_assessment_required": journey.is_test_required,
                        "assessment_id": journey.test_series.pk if journey.test_series else "",
                        "survey_id": journey.survey.pk if journey.survey else "",
                        "is_community_required": journey.is_community_required,
                        "user_status": user_status_data,
                        "duration": "2 Week",
                        "tags": journey.tags.split(",")
                    })
                response = {
                    "message": "Get data",
                    "success": True,
                    "data": {
                        "all_journey": journey_list
                    }
                }
                return Response(response, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": serializer.errors,  "success": False}, status=400)


class ContentQuizAsnwer(APIView):
    def post(self, request, **kwargs):
        data = request.data
        serializer = ContentQuizAsnwerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            id = data['id']
            option = data['option']
            quest_id = data['quest_id']
            journey_id = data['journey_id']
            get_cd = ContentData.objects.get(id=id)
            user = User.objects.filter(id=data['user_id']).first()
            if get_cd.type == "Quiz":
                cd_option = ContentDataOptions.objects.filter(content_data=get_cd)
                ContetnOptionSubmit.objects.create(content_data=get_cd, option=option, user=user)
                ca = cd_option.filter(correct_answer=True)[0]
                cd_option = cd_option.filter(option=option)[0]
                response = {
                    "correct_answer": cd_option.correct_answer,
                    "answer": ca.option
                }
                return Response({"message": "get data", "data": response, "success": True}, status=status.HTTP_200_OK)

            elif get_cd.type == "Poll":
                if ContetnOptionSubmit.objects.filter(content_data=get_cd, option=option, user=user).count() > 0:
                    message = "Already submited"
                    cd_option = ContentDataOptions.objects.filter(content_data=get_cd)
                else:
                    message = "submit Poll"
                    ContetnOptionSubmit.objects.create(content_data=get_cd, option=option, user=user)
                    cd_option = ContentDataOptions.objects.filter(content_data=get_cd)
                response = []
                for cd_option in cd_option:
                    get_user_result = ContetnOptionSubmit.objects.filter(content_data=get_cd)
                    total_answer = get_user_result.count()
                    count = get_user_result.filter(option=cd_option.option).count()

                    if count == 0:
                        avg_count = 0
                    else:
                        avg_count = (count/total_answer)*100

                    response.append({
                        "id": cd_option.id,
                        "option": cd_option.option,
                        "count": avg_count
                    })
                return Response({"message": message, "data": response, "success": True}, status=status.HTTP_200_OK)
            return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class AvatarUpdate(APIView):
    def post(self, request, format=None):
        data = request.data
        serializer = AvatarUpdateSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            try:
                user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "Invalid UUID or User does not exist",  "success": False}, status=status.HTTP_404_NOT_FOUND)
            user = User.objects.filter(id=data['user_id']).first()
            user.avatar = request.data['avatar']
            user.save()
            return Response({"message": "Avatar uploaded successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Communities APIs


class JourneyPostCreate(APIView):
    def post(self, request):
        data = request.data
        serializer = AskQuestionSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = User.objects.get(id=request.data['user_id'])
            try:
                channel = Channel.objects.get(id=request.data['journey_id'])
            except Channel.DoesNotExist:
                return Response({"message": "Journey UUID is Invalid",  "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                microskill = Content.objects.get(id=request.data['quest_id'], Channel=channel)
            except Content.DoesNotExist:
                return Response({"message": "Content not found in this Journey",  "success": False}, status=status.HTTP_404_NOT_FOUND)
            title = request.data['title']
            body = request.data['description']
            type = request.data['type']
            create_post(user, channel, title, body, type, microskill.id)
            data = {
                "title": title,
                "description": body,
                "created_by": user.username,
            }
            return Response({"message": "Post Successfully Created", "Post_data": data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JourneyAllPost(APIView):
    def get(self, request, **kwargs):
        try:
            channel = Channel.objects.get(id=self.kwargs['journey_id'])
        except Channel.DoesNotExist:
            return Response({"message": "Invalid Journey UUID",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        result = []
        if channel.is_community_required:
            space_id = channel.journryspace.space_id
            community_id = channel.journryspace.community_id
            data = get_space_post(community_id, space_id)
            print(data)
            for data in data:
                post_data = {
                    "post_id": data['id'],
                    "slug": data['slug'],
                    "name": data['body']['name'],
                    "body": data['body']['body'],
                    "record_type": data['body']['record_type'],
                    "user_name": data['user_name'],
                }
                result.append(post_data)
        else:
            return Response({"message": "No post found for this journey in community post"}, status=status.HTTP_404_NOT_FOUND)

        context = {
            "post_data": result,
            "channel": channel.title,
            "Success": True,
            "type": "community"
        }
        return Response({"data": context}, status=status.HTTP_200_OK)


class PostComment(APIView):
    def post(self, request, **kwargs):
        data = request.data
        serializer = PostCommentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                channel = Channel.objects.get(id=request.data['journey_id'])
            except Channel.DoesNotExist:
                return Response({"message": "Journey does not exist",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(id=request.data['user_id'])
            post_id = request.data['post_id']
            try:
                post = CommunityPost.objects.get(post_id=post_id, journey=channel)
            except CommunityPost.DoesNotExist:
                return Response({"message": "Post does not exist on this journey",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
            body = request.data['answer']
            post_Comment(channel, post_id, body, user)
            data = {
                "post_name": post.name,
                "post_body": post.body,
                "comment": body,
                "commented_by": user.username,
            }
            return Response({"Success": True, "data": data}, status=status.HTTP_200_OK)


class DeletePost(APIView):
    def delete(self, request, **kwargs):
        user = User.objects.get(id=self.kwargs['user_id'])
        try:
            channel = Channel.objects.get(id=self.kwargs['journey_id'])
        except Channel.DoesNotExist:
            return Response({"message": "Journey does not exist",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        post_id = self.kwargs['post_id']
        try:
            post = CommunityPost.objects.get(post_id=post_id, journey=channel)
        except CommunityPost.DoesNotExist:
            return Response({"message": "Post does not exist on this journey",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        delete_post(channel, post_id)
        data = {
            "post_id": post_id,
            "post_delete": "Success",
            "deleted_by": user.username,
            "Success": True,
        }
        return Response({"response": data}, status=status.HTTP_200_OK)


class MarkasComplete(APIView):
    def post(self, request):
        serializer = QuestContentSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(pk=request.data['user_id'])
            content = Content.objects.get(pk=request.data['quest_id'])
            channel_group = ChannelGroup.objects.get(pk=request.data['journey_group'])
            channel = Channel.objects.get(pk=channel_group.channel.pk)
            user_course = UserCourseStart.objects.filter(
                user=user, content=content, channel_group=channel_group, channel=channel).update(status="Complete")
            UserReadContentData.objects.filter(
                user=user, content=content, channel_group=channel_group, channel=channel).update(status='Complete')
            CheckEndOfJourney(user, channel.pk, userType=request.session['user_type'])
            return Response({"message": "Mark As Complete", "success": True}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class ContacProgramTeamAPI(APIView):
    def post(self, request):
        serializer = ContacProgramTeamsSerializer(data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            if not self.request.query_params.get('company_id'):
                return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            try:
                company = Company.objects.get(id=self.request.query_params.get('company_id'))
            except Company.DoesNotExist:
                return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                user = User.objects.get(id=request.data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            subject = request.data['subject']
            issue = request.data['issue']
            company = user.company.all().first()
            obj = ContactProgramTeam.objects.create(user=user, subject=subject, issue=issue, company=company)
            image_file = request.FILES.getlist('image')
            try:
                print(subject)
                mail = EmailMessage(subject, issue, INFO_CONTACT_EMAIL, [
                                    "mentoring@hrfc.asia"], ["Info@growatpace.com"])
                for image in image_file:
                    name = image.name
                    content = image.read()
                    content_type = image.content_type
                    mail.attach(name, content, content_type)
                    ContactProgramTeamImages.objects.create(contact_program=obj, image=image)
                mail.send()
                print(("mailed"))

            except BadHeaderError:
                return HttpResponse('Invalid header found.')

            data = {
                "response": "Success",
                "success": True,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class ResendEmail(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "invalid User", "success": False}, status=status.HTTP_404_NOT_FOUND)
        sendVerificationMail(user, user.email)
        return Response({"message": "Verification email successfully sent", "success": True}, status=status.HTTP_200_OK)


class ShowUnreadMsgCount(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "invalid User", "success": False}, status=status.HTTP_404_NOT_FOUND)
        all_rooms = AllRooms.objects.filter(Q(user1=user) | Q(user2=user) | Q(members__in=[user]), user1__is_active=True, user2__is_active=True, user1__is_delete=False, user2__is_delete=False)
        count = 0
        for rooms in all_rooms:
            unread_msg = Chat.objects.filter(Q(to_user=user) & Q(from_user=rooms.user2) | Q(to_user=user) & Q(
                from_user=rooms.user1) | Q(room=rooms), ~Q(read_by__in=[user]))
            if unread_msg:
                count += 1
        count = None if count == 0 else count
        data = {
            "user_id": user.id,
            "message_count": count,
            "Success": True,
        }
        return Response(data, status=status.HTTP_200_OK)

class StartEngagementTime(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "invalid User", "success": False}, status=status.HTTP_404_NOT_FOUND)

        UserEngagement.objects.create(user=user, login_time=datetime.now())
        response = {
            "message": "User Logged In",
            "success": True
        }
        return Response(response, status=status.HTTP_200_OK)

class EndEngagementTime(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "invalid User", "success": False}, status=status.HTTP_404_NOT_FOUND)

        user_engagement = UserEngagement.objects.filter(user=user).first()
        if user_engagement:
            user_engagement.logout_time = datetime.now()
            user_engagement.save()
            response = {
                "message": "User Logged Out",
                "success": True
            }
            return Response(response, status=status.HTTP_200_OK)
        response = {
            "message": "Engagment data not available",
            "success": False
        }
        return Response(response, status=status.HTTP_404_NOT_FOUND)


class SocialLogin(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        print(request.data)
        type = data.get('user_type')
        host = self.request.query_params.get('host_name') or "Mobile"
        serializer = SocialLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            facebook_account_id = data.get('facebook_account_id') or None
            google_account_id = data.get('google_account_id') or None
            first_name = request.data['first_name']
            profile_image = data.get('avatar') or None
            last_name = request.data['last_name']
            
            signup = update_boolean(request.data['signup'])

            if not google_account_id and not facebook_account_id:
                return Response({"message": "facebook/google account id field cannnot be blank", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            if not request.data['email']:
                return Response({"message": "Email field cannnot be blank", "success": False}, status=status.HTTP_400_BAD_REQUEST)

            user = get_or_create_user(first_name, last_name, request.data['email'], request.data['social_login_type'], type, profile_image, google_account_id, facebook_account_id)
            if signup:
                if not data.get('coupon_code') and host == "Mobile":
                    return Response ({"message": "Coupon code required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                elif data.get('coupon_code') and host != "Forum":
                    coupon_code = data.get('coupon_code')
                if not validate_Coupon(coupon_code):
                    return Response({"message": "Invalid Coupon Code", "success": False}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    user.coupon_code = coupon_code
                    user.save()
                    applyCouponCode(user, coupon_code)
            if not isinstance(user, str):
                if data.get('device_id') and data.get('firebase_token'):
                    User_firebase_details(user, data.get('device_id'), data.get('firebase_token'))
                token, created = Token.objects.get_or_create(user=user)
                token = token.key
                industry_list = [industry.name for industry in user.industry.all()]
                expertize_list = [expertize.name for expertize in user.expertize.all()]
                type = ",".join(str(type.type) for type in user.userType.all())
                response = {
                    "data": {
                        "username": user.username,
                        "id": user.id,
                        "email": user.email,
                        "is_email_verified": user.is_email_verified,
                        "phone": str(user.phone),
                        "is_phone_verified": user.is_phone_verified,
                        "user_type": type,
                        "private_profile": user.private_profile,
                        "token": token,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "gender": user.gender,
                        "age": user.age,
                        "prefer_not_say": user.prefer_not_say,
                        "organization": user.organization,
                        "current_status": user.current_status,
                        "position": user.position,
                        "avatar": user.avatar.url,
                        "expertize": expertize_list,
                        "industry": industry_list,
                        "linkedin_profile": user.linkedin_profile,
                        "favourite_way_to_learn": user.favourite_way_to_learn,
                        "interested_topic": user.interested_topic,
                        "upscaling_reason": user.upscaling_reason,
                        "time_spend": user.time_spend,
                        "signup": signup
                    },
                    "success": True,
                    "message": "Login Successfull",
                }
                return Response(response, status=status.HTTP_200_OK)
            return Response({"message": user, "success": False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)

class ProgramTeamAnnouncementList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_channel = UserChannel.objects.filter(user=user, status="Joined")
        channel_list = [channel.Channel for channel in user_channel]
        announcements = ProgramTeamAnnouncement.objects.filter(journey__in=channel_list)
        announcement_list = []
        for announcement in announcements:
            announcement_list.append({
                "id": announcement.id,
                "company_id": announcement.company.pk if announcement.company else '' ,
                "company_name": announcement.company.name if announcement.company else '' ,
                "journey_id": announcement.journey.id,
                "journey_name": announcement.journey.title,
                "topic": announcement.topic,
                "summary": announcement.summary,
                "announce_date": announcement.announce_date,
                "created_by": f"{announcement.created_by.first_name} {announcement.created_by.last_name}"
            })
        response = {
            "message": "Annoucement Data",
            "success": True,
            "data": announcement_list
        }
        return Response(response, status=status.HTTP_200_OK)
    
class DataTranslate(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = TranslateDataSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            from_lang = data.get('from_lang') or "auto"
            to_lang = request.data['to_lang']
            if to_lang not in LANGUAGES.keys():
                return Response({"message": "Choose valid translate code", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            text = request.data['text']
            if not isinstance(text, list):
                return Response({"message": "text value should be in list form", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            data = translate_data(to_lang, text, from_lang)
            lang = LANGUAGES[to_lang]
            response = {
                "message": f"data translated to {lang} is successfully",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PublicAnnouncementList(APIView):
    def get(self, request, *args, **kwargs):
        # if not self.request.query_params.get('user_type'):
        #     return Response({"message": "user_type is required", "success": False}, status=status.HTTP_404_NOT_FOUND)            
        user_type = self.request.query_params.get('user_type')
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if not self.request.query_params.get('company_id'):
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=self.request.query_params.get('company_id'))
        except Company.DoesNotExist:
            return Response({"message": "company_id does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        journey = UserChannel.objects.filter(user=user, Channel__company=company, status="Joined", is_removed=False)
        # if user_type in ['Admin', 'ProgramManager']:
        #     journey = None
        response = {
            "message": "Public Annoucement Data",
            "success": True,
            "data": public_announcement_list(company, journey)
        }
        return Response(response, status=status.HTTP_200_OK)
    

class AssignSurveyList(APIView):
    def post(self, request):
        serializer = AssignSurveyListSerializer(data=request.data)
        if serializer.is_valid():
            user_type=request.data['user_type']
            try:
                user=User.objects.get(id=request.data['user_id'], userType__type=user_type)
            except User.DoesNotExist:
                return Response({"message": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
            journeys = company_journeys(user_type, user, request.data['company_id'])

            final_data = []
            if user_type == "Mentor":
                joined_channel = []
                pool_mentor = PoolMentor.objects.filter(mentor=user, pool__journey__closure_date__gt=datetime.now())
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
                user_channel = UserChannel.objects.filter(
                    user=user, Channel__channel_type="MentoringJourney", Channel__in=journeys)
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
            response = {
                "message": "assigned survey list",
                "success": True,
                "data": final_data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MobileLogs(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data=request.data
        serializer = MobileLogsSerializer(data=request.data)
        if serializer.is_valid():
            data = request.data['data']
            dir_path = f"{str(BASE_DIR)}/logs/mobile/{date.today()}"
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
            with open(f"{dir_path}/debug.log", 'a') as file:
                file.write(data)
            response = {
                "message": "data added to file",
                "success": True,
                "data": data
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetCompanyJourney(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data=request.data
        serializer = CompanyJourneySerializer(data=request.data)
        if serializer.is_valid():
            company_id = data['company_id']
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return Response({"message": "Company does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            journeys = Channel.objects.filter(company=company, is_delete=False, is_active=True)
            journey_list = []
            for journey in journeys:
                journey_list.append({
                    "id": journey.id,
                    "title": journey.title
                })
            response = {
                "message": "Get Company's journey",
                "success": True,
                "journey": journey_list
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserValidation(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data=request.data
        # print(request.data)
        serializer = ValidationSerializer(data=request.data)
        if serializer.is_valid():
            response = False
            journey_id = None
            if value := data.get('value'):
                response = User.objects.filter(Q(email=value)|Q(username=value)|Q(phone=value)).exists()
                print(response)
            if coupon_code := data.get('coupon_code'):
                response, journey_id = validate_Coupon_for_rasa(coupon_code)
            response = {
                "message": f"Validation {response}",
                "success": True,
                "response": response,
                "journey_id": journey_id
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GetTimeZone(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        print(request.data)
        try:
            timezone = request.data['timezone']
            request.session['timezone'] = timezone
            print("Session Timezone", request.session['timezone'])
            response = {"message":f"Timezone {request.session['timezone']}", "success":True}
            return Response(response, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Timezone key was not in the data"}, status.HTTP_400_BAD_REQUEST)
    
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
                    return Response(response, 200)
                return Response(data, 200)
            print('data3 ', response)
            return Response(response, 200)
        else:
            Response({"message":"missing parameter", "success":False}, 400)

class AssesmentQuestions(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        data = request.query_params
        serializer = AssesmentQuestionSerializer(data=data)
        if serializer.is_valid():
            # profile_assest = ProfileAssestQuestion.objects.filter(id=13)
            profile_assest = ProfileAssestQuestion.objects.filter(
                question_for=request.query_params['type'], is_active=True, is_delete=False, journey=request.query_params['journey_id'])
            data = []
            for profile in profile_assest:
                data.append({'id':profile.id, 'question': profile.question, 'type': profile.question_type, 'options':profile.options})
            return Response({"profile_assest": data}, status.HTTP_200_OK)
        else: return Response({"message":"missing params", "success": False}, status.HTTP_400_BAD_REQUEST)

class Check_lite_signup_user_data(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        data = request.data
        print(data)
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
                    "user_id": user.id,
                    "user_type": userr_type,
                    "email": user.email if user else "",
                    "username": user.username if user else "",
                    "mobile": str(user.phone) if user else "",
                    "first_name": user.first_name if user else "",
                    "last_name": user.last_name if user else "",
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
       
class SignupLitePost(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        print("DATA", request.data)
        email = request.data['email']
        username = request.data['username']
        name = request.data['name']
        mobile = request.data['phone']
        coupon_code = request.data['Coupon_code']
        user_type = request.data['userType']
        term_and_conditions = request.data['term_and_conditions']
        is_whatsapp_enable = request.data['is_whatsapp_enable']
        pdpa_statement = request.data['pdpa_statement']
        try:
            type = UserTypes.objects.get(type=user_type)
        except UserTypes.DoesNotExist:
            return Response({"message":"user_type not found", "success":False}, status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(username=username, email=email)
        modified_date = datetime.now()

        if not user:
            data = {"coupon_code": coupon_code}
            print(username)
            try:
                validate_email(email)
            except:
                context = {'message' : 'you have entered incorrect email address', 'success':False}
                return Response(context, status.HTTP_400_BAD_REQUEST)

            if not '+' in mobile:
                context = {'message': 'you have entered incorrect country code or phone number', "success":False}
                return Response(context, status.HTTP_400_BAD_REQUEST)
                
            if User.objects.filter(phone=mobile).exists():
                context = {'message': 'Phone Number is already exists', "success":False}
                return Response(context, status.HTTP_400_BAD_REQUEST)

            check_user = User.objects.filter(email=email).first()
            check_profile = Profile.objects.filter(user=check_user).first()
            print("line 340", check_user, check_profile)
            if check_user or check_profile:
                context = {'message': 'User already exists',  "success":False}
                return Response(context, status.HTTP_400_BAD_REQUEST)

            if not validate_Coupon(coupon_code):
                context = {'message': 'Invalid Coupon Code', "success":False}
                return Response(context, status.HTTP_400_BAD_REQUEST)
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
            if user.phone is None or user.phone == str(None):
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
        if request.data['userType'] not in user_types:
            user.userType.add(type.id)

        user.save()
        default_space_join_user(user)
        # if coupon_code:
            # applyCouponCode(user, coupon_code)

        # for question in request.data['question_list']:
        #     print(question['question'])
        #     profile_question = ProfileAssestQuestion.objects.get(pk=question['question_id'])
        #     user_profile_question = UserProfileAssest.objects.filter(
        #         assest_question=profile_question, question_for=user_types).first()
        #     if user_profile_question:
        #         UserProfileAssest.objects.create(user=user, question_for=request.data['userType'],
        #                                         assest_question=profile_question, response=question['response'])
        
        otp = str(random.randint(100000, 999999))
        print("OTP for lite signup",otp)
        try:
            profile = Profile.objects.get(user=user)
            profile.otp = otp
            profile.save()
        except Exception:
            Profile.objects.create(user=user, otp=otp)
        vonage_sms_otp_sender(user, otp)
        register_email(user, password)

        NotificationAndPoints(user, title="registration")

        return Response({"success":True, "message":"otp sent", "otp": otp}, 200)

class UpdateEmail(APIView):

    def post(self, request):
        serializer = UpdateEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = request.data['email']
            request.session['email'] = email
            user = User.objects.filter(id=request.data['id']).first()
            if User.objects.filter(email=request.data['email']).exists():
                response = {
                    "message": "Email already exist",
                    "success": False
                }
                return Response(response, status=status.HTTP_200_OK)
            elif user:
                otp = str(random.randint(100000, 999999))
                if user_profile := Profile.objects.filter(user=user).first():
                    user_profile.otp = otp
                    user_profile.save()
                else:
                    user_profile = Profile.objects.create(user=user, otp=otp)
                send_email_otp(email, otp)
                response = {
                    "message": "Please check your email for otp",
                    "success": True
                }
                return Response(response, status=status.HTTP_200_OK)
                
            response = {
                "message": "User Not Found",
                "success": False
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailOtp(APIView):

    def post(self, request):
        serializer = VerifyEmailOtpSerializer(data=request.data)
        if serializer.is_valid():
            otp = request.data['otp']
            user = User.objects.filter(id=request.data['id']).first()
            if user:
                user_profile = Profile.objects.filter(user=user).first()
                if user_profile.otp == otp:
                    UserEmailChangeRecord.objects.create(user=user, old_email=user.email, current_email=request.session['email'])
                    user.email = request.session['email']
                    user.save()
                    response = {
                        "message": "Email updated successfully.",
                        "success": True
                    }
                    return Response(response, status=status.HTTP_200_OK)

                response = {
                    "message": "OTP verification failed.",
                    "success": False
                }
                return Response(response, status=status.HTTP_200_OK)
                
            response = {
                "message": "User Not Found",
                "success": False
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RuntheCronjobs(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        users_risk_data_update()
        mentors_risk_data_update()
        pair_risk_data_update()
        return Response({'message':'success', 'success':True}, 200)
 
class MenteeActivityData(APIView):
    permission_classes = [AllowAny]
    def get(self,request):
        company = request.query_params['company']

        if not request.query_params.get('email'):
            return Response({"message": "email required in query_params", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email = request.query_params.get('email')
            manager_name = ProgramManager.objects.get(email__iexact=email).get_full_name()
        except:
            return Response({"message":"User is not program manager", "success": False}, status.HTTP_401_UNAUTHORIZED)
        
        users = User.objects.filter(userType__type="Learner")
        mentee_data = [] 
        headers = ['User', 'Email', 'Calls', 'Total Calls', 'Quest', 'Total Quest', 'Journals', 'Total Journals', 'All Post']
        
        for user in users:
            if NoActivityMenteeData.objects.filter(user=user, company=company).exists():
                data = NoActivityMenteeData.objects.filter(company=company, user=user).values_list()
                d = data[0]
                mentee_data.append([user.get_full_name(), user.email, d[6], d[7], d[8], d[9], d[10], d[11], d[12]])

        df = pd.DataFrame(mentee_data, columns=headers)
        df.to_csv(f"static/csv/mentee_activity_{email}.csv", index=False)

        send_activity_email("Mentee", email, manager_name, f"static/csv/mentee_activity_{email}.csv")
        timenow = int(time())
        with open(f'static/csv/mentee_activity_{email}.csv', 'rb') as f:
            csv_file = File(f, name=f"{email.split('@')[0]}_{timenow}.csv")
            SaveRasaManagerFiles.objects.create(csv_file=csv_file).save()

        file_link = SaveRasaManagerFiles.objects.get(csv_file__contains=f"{email.split('@')[0]}_{timenow}.csv").csv_file.url
        print("File link", file_link)

        os.remove(f"static/csv/mentee_activity_{email}.csv")
        print("File deleted")

        return Response({"message":"success", "success":True, "data":mentee_data, "headers":headers, "url":file_link}, 200)
      
class MentorActivityData(APIView):
    permission_classes = [AllowAny]
    def get(self,request):
        company = request.query_params['company']

        if not request.query_params.get('email'):
            return Response({"message": "email required in query_params", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        email = request.query_params.get('email')

        try:
            email = request.query_params.get('email')
            manager_name = ProgramManager.objects.get(email__iexact=email).get_full_name()
        except:
            return Response({"message":"User is not program manager", "success": False}, status.HTTP_401_UNAUTHORIZED)
        
        users = User.objects.filter(userType__type="Mentor")
        mentor_data = [] 
        headers = ['User', 'Email', 'Calls', 'Total Calls', 'Quest', 'Total Quest', 'Journals', 'Total Journals', 'All Post']
        
        for user in users:
            if NoActivityMentorData.objects.filter(user=user, company=company).exists():
                data = NoActivityMentorData.objects.filter(company=company, user=user).values_list()
                d = data[0]
                mentor_data.append([user.get_full_name(), user.email, d[6], d[7], d[8], d[9], d[10], d[11], d[12]])
        df = pd.DataFrame(mentor_data, columns=headers)
        df.to_csv(f"static/csv/mentor_activity_{email}.csv", index=False)

        send_activity_email("Mentor", email, manager_name, f"static/csv/mentor_activity_{email}.csv")

        timenow = int(time())
        with open(f'static/csv/mentor_activity_{email}.csv', 'rb') as f:
            csv_file = File(f, name=f"{email.split('@')[0]}_{timenow}.csv")
            SaveRasaManagerFiles.objects.create(csv_file=csv_file).save()

        file_link = SaveRasaManagerFiles.objects.get(csv_file__contains=f"{email.split('@')[0]}_{timenow}.csv").csv_file.url
        print("File link", file_link)

        os.remove(f"static/csv/mentor_activity_{email}.csv")
        print("File deleted")
        
        return Response({"message":"success", "success":True, "data":mentor_data, "headers":headers, "url":file_link}, 200)
          
class PairActivityData(APIView):
    permission_classes = [AllowAny]
    def get(self,request):
        company = request.query_params['company']

        if not request.query_params.get('email'):
            return Response({"message": "email required in query_params", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        email = request.query_params.get('email')

        try:
            email = request.query_params.get('email')
            manager_name = ProgramManager.objects.get(email__iexact=email).get_full_name()
        except:
            return Response({"message":"User is not program manager", "success": False}, status.HTTP_401_UNAUTHORIZED)

        fields = ["Company Name", "Journey Name", "Mentor Name", "Mentee Name"]
        if not company:
            return Response({"message": "company_id is required", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        pair_data = NoActivityPairData.objects.filter(company__id=company)
        pair_data_list = [ 
            {
            "Company Name": pair.company.name,
            "Journey Name": pair.pair.journey.title,
            "Mentor Name": pair.pair.mentor.get_full_name(),
            "Mentee Name": pair.pair.user.get_full_name(),
            }
            # {
            # "company_id": pair.company.pk,
            # "company_name": pair.company.name,
            # "journey_id": pair.pair.journey.pk,
            # "journey_name": pair.pair.journey.title,
            # "mentor_id": pair.mentor.id,
            # "mentor_name": pair.pair.mentor.get_full_name(),
            # "mentee_id": pair.pair.user.id,
            # "mentee_name": pair.pair.user.get_full_name(),
            # }
            for pair in pair_data]
        
        # Writing the data to a CSV file
        with open(f'static/csv/pair_activity_{email}.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            writer.writerows(pair_data_list)

        send_activity_email("Attendance", email, manager_name, f"static/csv/pair_activity_{email}.csv")
        
        timenow = int(time())
        with open(f'static/csv/pair_activity_{email}.csv', 'rb') as f:
            csv_file = File(f, name=f"{email.split('@')[0]}_{timenow}.csv")
            SaveRasaManagerFiles.objects.create(csv_file=csv_file).save()

        file_link = SaveRasaManagerFiles.objects.get(csv_file__contains=f"{email.split('@')[0]}_{timenow}.csv").csv_file.url
        print("File link", file_link)

        os.remove(f"static/csv/pair_activity_{email}.csv")
        print("File deleted")

        response = {
            "message": "Get Risk Pairs",
            "data": pair_data_list,
            "success": True,
            "url":file_link
        }
        return Response(response, 200)

class GenerateAttendance(APIView):
    permission_classes = [AllowAny]
    def get(self,request):
        journey = request.query_params['journey']

        if not request.query_params.get('email'):
            return Response({"message": "email required in query_params", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        email = request.query_params.get('email')

        try:
            email = request.query_params.get('email')
            manager_name = ProgramManager.objects.get(email__iexact=email).get_full_name()
        except:
            return Response({"message":"User is not program manager", "success": False}, status.HTTP_401_UNAUTHORIZED)

        mentor_channel = Channel.objects.get(pk=journey)
        
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

        mentor_channel = Channel.objects.get(pk=journey)
        data = generate_attendence_for_rasa(mentor_channel)


        # Writing the data to a CSV file
        with open(f'static/csv/attendance_{email}.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)

        send_activity_email("Attendance", email, manager_name, f"static/csv/attendance_{email}.csv")
                
        timenow = int(time())
        with open(f'static/csv/attendance_{email}.csv', 'rb') as f:
            csv_file = File(f, name=f"{email.split('@')[0]}_{timenow}.csv")
            SaveRasaManagerFiles.objects.create(csv_file=csv_file).save()


        file_link = SaveRasaManagerFiles.objects.get(csv_file__contains=f"{email.split('@')[0]}_{timenow}.csv").csv_file.url
        print("File link", file_link)

        os.remove(f"static/csv/attendance_{email}.csv")
        print("File deleted")

        return Response({'message':'success', 'success':True, 'data':data, "headers":fields, "url":file_link}, 200)

class ManagerCompanies(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        email = request.query_params['email']
        try:
            manager_name = ProgramManager.objects.get(email__iexact=email).get_full_name()
        except:
            return Response({"message":"User is not program manager", "success": False, "manager": False}, status.HTTP_401_UNAUTHORIZED)
        
        data = User.objects.filter(email__iexact=email).first()
        if not data == None:
            companies = data.company.all()
            all_companies = []
            all_company_ids = []
            for company in companies:
                all_companies.append(str(company))
                uuid = Company.objects.get(name__iexact=str(company)).id
                all_company_ids.append(uuid)
            return Response({"message":"success", "success": True, 'data':all_companies, "ids": all_company_ids}, 200)
        else:
            return Response({"message":"failure", "success": False, "info":"Email does not exist."}, 404)
        
class GetJourneyTitle(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        journey_id = request.query_params['journey_id']
        data = Channel.objects.get(id__iexact=journey_id)
        if data:
            print(data.title)
            return Response({"message":"success", "success": True, "title": data.title}, 200)
        else:
            return Response({"message":"failure", "success": False, "info":"Journey does not exist."}, 404)

class GetJourneyList(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        company_id = self.request.query_params.get('company') or None

        if company_id:
            journeys = Channel.objects.filter(company__id=company_id, closure_date__gt=datetime.now())

        journey_list = [{"id": journey.pk, "name": journey.title} for journey in journeys]
        response = {
            "message": "program manager journey list",
            "success": True,
            "data": journey_list
        }
        return Response(response, status=status.HTTP_200_OK)

def generate_apple_redirect_url(request):
    TEAM_ID = "M5XQ6M34PZ"
    KEY_ID = "G83684CZKZ"
    APP_ID = CLIENT_ID = "com.atpace.applesignintestapp"
    SERVICE_ID = "com.atpace.applesignintestservice"
    with open("static/cred/apple_private_key.p8", 'r') as f:
        PRIVATE_KEY = f.read()

    # Define your client ID and redirect URI
    client_id = CLIENT_ID
    redirect_uri = 'https://1da4-2405-201-301d-f0f1-a5f7-705d-95a6-9fa0.ngrok-free.app/apple-auth-callback'  # Replace with your actual redirect URI

    # Generate the JWT payload
    payload = {
        'iss': TEAM_ID,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        'aud': 'https://appleid.apple.com',
        'sub': client_id,  # Replace with your actual client bundle ID
    }

    # Generate the JWT using PyJWT library
    token = jwt.encode(payload, PRIVATE_KEY, algorithm='ES256')  # Replace with your actual private key

    # Build the redirect URL
    redirect_url = f'https://appleid.apple.com/auth/authorize?response_type=code%20id_token&client_id={client_id}&redirect_uri={redirect_uri}&state=your_state&scope=name%20email&response_mode=form_post'

    return HttpResponseRedirect(redirect_url)


class GetDyteAuthToken(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        data = request.query_params
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
            email = user.email
            user_id = self.kwargs['user_id']
        except User.DoesNotExist:
            return Response({"Message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        

        meet_id = data['meet_id']

        try: dyte_obj = DyteAuthToken.objects.get(email__iexact=email, meeting_id= meet_id)
        except DyteAuthToken.DoesNotExist: return Response({"message": f"Token does not exist for user {user.get_full_name()} - {user_id} for meet_id = {meet_id}"}, status=status.HTTP_404_NOT_FOUND)

        context = {
            "meet_id": meet_id,
            "user": user.get_full_name(),
            "email": user.email,
            "authToken": dyte_obj.authToken,
            "user_preset": dyte_obj.preset
        }

        return Response({"message": "success", "success":True, "info":context}, status=status.HTTP_200_OK)