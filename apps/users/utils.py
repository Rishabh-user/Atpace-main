import jwt
from ravinsight.web_constant import JWT_SECRET_KEY
from arPaceAI.arPaceAI.atPaceAI import best_matches
from apps.program_manager_panel.models import SubcribedUser, MentorMenteeRatio, AssignTaskToUser
from apps.mentor.models import AssignMentorToUser, PoolMentor, Pool, DyteAuthToken,MenteeSummary,MentorSummary
from fuzzywuzzy import fuzz
from django.utils.timezone import localtime
import asyncio
import time
from django.db.models.query_utils import Q
from datetime import datetime
from http.client import HTTPResponse
import requests
import json
from apps.atpace_community.utils import add_member_to_space
# from apps.video_calling.views import API_KEY
from ravinsight.settings import API_KEY, DYTE_API_KEY,DYTE_BASE_URL, DYTE_ORG_ID, DYTE_APP_URL
from apps.content.models import Channel, MatchQuesConfig, MatchQuestion, UserChannel
from django.core.mail import send_mail, BadHeaderError, EmailMultiAlternatives, EmailMessage
from threading import Thread
from apps.users.models import Collabarate, Coupon, UserTypes, ProfileAssestQuestion, User, CouponApply, UserCompany, UserProfileAssest
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from apps.vonage_api.utils import journey_enrolment
from ravinsight.web_constant import SITE_NAME, DOMAIN, INFO_CONTACT_EMAIL, LOGIN_URL, PROTOCOL, DEFAULT_TIMEZONE, BASE_URL
import re, os, ast
import pytz
import random
import string
from datetime import datetime
from apps.utils.models import EmailStatusList
from apps.users.helper import add_user_to_company, user_company
from django.http import HttpResponse
from apps.chat_app.models import Chat, Room as AllRooms
from apps.users.templatetags.tags import get_chat_room
from threading import Thread
from apps.mentor.models import MeetingParticipants, AllMeetingDetails

def clean_text(w):
    w = re.sub(r'(\d+)(\.\d+)?', '', w)
    w = re.sub(r'(\s[a-zA-Z]\s)', '', w)
    w = re.sub(r'([^\x41-\x7A\x20]+)|([\r\n\"\'\t\s]+)', '', w)
    w = re.sub(r'\s+', '', w)
    w = re.sub(r'[^a-zA-Z0-9 \n\.]', '', w)
    return w.strip()+''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=5))


def validate_Coupon(coupon_code):
    response = False
    try:
        coupon = Coupon.objects.get(code__iexact=coupon_code, valid_from__lte=datetime.now(),
                           valid_to__gte=datetime.now(), is_active=True)
        if Channel.objects.filter(id=coupon.journey, closure_date__gt=datetime.now()).exists():
            response = True
        else:
            response = False
    except Coupon.DoesNotExist as e:
        print(e)
    return response

def validate_Coupon_for_rasa(coupon_code):
    response = False
    try:
        coupon = Coupon.objects.get(code__iexact=coupon_code, valid_from__lte=datetime.now(), valid_to__gte=datetime.now(), is_active=True)
        if Channel.objects.filter(id=coupon.journey, closure_date__gt=datetime.now()).exists():
            journey_id = Channel.objects.get(id=coupon.journey, closure_date__gt=datetime.now())
            journey_id = journey_id.id
            response = True
        else:
            response = False
            journey_id = None
    except Coupon.DoesNotExist as e:
        print("Coupon does not exist", e)
        journey_id = None
    return response, journey_id


def applyCouponCode(user, coupon_code):
    try:
        coupon = Coupon.objects.get(code__iexact=coupon_code, valid_from__lte=datetime.now(),
                                    valid_to__gte=datetime.now(), is_active=True)
        print("coupon.id", coupon.id)
    except Coupon.DoesNotExist:
        return False
    if coupon:
        user = User.objects.get(pk=user.pk)
        if coupon.journey:
            journey = Channel.objects.get(pk=coupon.journey)
            UserCompany.objects.create(user=user, company=journey.company)
            user.company.add(journey.company)

            AlloteChannel(coupon.journey, user.pk)
        user.coupon_code = coupon.code
        user.save()

        CouponApply.objects.create(code=coupon, user=user, applied=True)

    return True


def AlloteChannel(channel_id, user_id):

    channel = Channel.objects.get(pk=channel_id)
    user = User.objects.get(pk=user_id)

    if channel.is_community_required:
        add_member_to_space(channel, user)
        # space_id = channel.journryspace.space_id
        # community_id = channel.journryspace.community_id
        # group_id = channel.journryspace.space_group_id
        # InviteMember(user, space_id, community_id, group_id)

    response = False
    try:
        UserChannel.objects.get(Channel=channel, user=user, status="Joined")
    except UserChannel.DoesNotExist:
        UserChannel.objects.create(Channel=channel, user=user, status="Joined")
        add_user_to_company(user, channel.company)
        response = True
        if channel.whatsapp_notification_required and (user.phone and user.is_whatsapp_enable):
            journey_enrolment(user, channel)
    return response


def register_email(user, password=None):
    if password is None:
        password = "Please login with your existing password"
    subject = "Welcome to Growatpace"
    email_template_name = "email/register_mail.txt"

    c = {
        "email": user.email,
        'domain': DOMAIN,
        'site_name': SITE_NAME,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),

        "user": user,
        'token': default_token_generator.make_token(user),
        'protocol': PROTOCOL,
        'password': password
    }
    email = render_to_string(email_template_name, c)
    try:
        mail = send_mail(subject, email, INFO_CONTACT_EMAIL, [user.email], fail_silently=False)
        print(mail)
        sent_mail_status(subject, email_template_name, email, mail, "Register")
    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True

def send_email_otp(email, otp):
    subject = "Welcome to Growatpace"
    email_template_name = "email/change_email.txt"

    c = {
        "otp": otp
    }
    template_email = render_to_string(email_template_name, c)
    try:
        mail = send_mail(subject, template_email, INFO_CONTACT_EMAIL, [email], fail_silently=False)
        print(mail)
        sent_mail_status(subject, email_template_name, email, mail, "OTP")
    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True

def send_missing_existing_users(user_name, email, missign_email, existing_email):
    subject = "Issues in Uploading mentor data"
    email_template_name = "email/missing_existing_email.txt"

    c = {
        "user_name": user_name,
        "missign_email": missign_email if missign_email else None,
        "existing_email": existing_email if existing_email else None
    }
    template_email = render_to_string(email_template_name, c)
    try:
        mail = send_mail(subject, template_email, INFO_CONTACT_EMAIL, [email], fail_silently=False)
        print(mail)
        sent_mail_status(subject, template_email, email, mail, "CSV Upload")
    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True


def sendVerificationMail(user, email):
    subject = "Welcome to Growatpace"
    email_template_name = "email/verify_email.txt"
    token = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=32))
    user.token = token
    user.save()
    c = {
        "email": user.email,
        "domain": DOMAIN,
        # 'domain': DOMAIN,
        'site_name': SITE_NAME,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        'token': user.token,
        'protocol': PROTOCOL,
        # 'protocol': 'https',
    }
    email = render_to_string(email_template_name, c)
    try:
        mail = send_mail(subject, email, INFO_CONTACT_EMAIL, [user.email], fail_silently=False)
        print(mail)
        sent_mail_status(subject, email_template_name, email, mail, "Email Verification")
    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True


def send_call_booking_mail(user, mentor, email, mentor_name, mentee_name, call_url, date_time, title, offset):
    subject = "Mentoring Session scheduled"
    email_template_name = "email/send_email_for_booking.txt"
    print("in Mentor book ")
    c = {
        "email": user.email,
        'domain': DOMAIN,
        'site_name': SITE_NAME,
        "mentor_name": mentor_name,
        "mentee_name": mentee_name,
        "call_url": call_url,
        "datetime": date_time,
        "login_url": LOGIN_URL,
        "title": title,
        "time_zone": offset,

    }
    email = render_to_string(email_template_name, c)
    # try:
    #     mail = send_mail(subject, email, INFO_CONTACT_EMAIL, [user.email, mentor.email], fail_silently=False)
    # except BadHeaderError:
    #     return HTTPResponse('Invalid header found.')
    try:
        mail = EmailMultiAlternatives(subject, email, INFO_CONTACT_EMAIL, [user.email, mentor.email])
        mail.send(fail_silently=False)
        print("mailed")

    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True


def send_cancel_booking_mail(user, mentor, email, mentor_name, mentee_name, date_time, title, offset):
    subject = "Mentoring Session Cancelled"
    email_template_name = "email/send_email_for_booking_cancelled.txt"
    c = {
        "email": user.email,
        'domain': DOMAIN,
        'site_name': SITE_NAME,
        "mentor_name": mentor_name,
        "mentee_name": mentee_name,
        "datetime": date_time,
        "login_url": LOGIN_URL,
        "title": title,
        "time_zone": offset,

    }
    email = render_to_string(email_template_name, c)
    try:
        mail = send_mail(subject, email, INFO_CONTACT_EMAIL, [user.email, mentor.email], fail_silently=False)

    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True


def send_update_booking_mail(participants, mentor, mentor_name, mentee_name, call_url, date_time, title, offset):
    subject = "Mentoring Session Rescheduled"
    email_template_name = "email/send_email_for_booking_update.txt"
    print("in Mentor book ")
    send_mail_emails = [mentor.email]
    send_mail_emails.extend(participant.email for participant in participants.all())

    c = {
        'domain': DOMAIN,
        'site_name': SITE_NAME,
        "mentor_name": mentor_name,
        "mentee_name": mentee_name,
        "call_url": call_url,
        "datetime": date_time,
        "login_url": LOGIN_URL,
        "title": title,
        "time_zone": offset,
    }
    email = render_to_string(email_template_name, c)

    try:
        mail = send_mail(subject, email, INFO_CONTACT_EMAIL, send_mail_emails, fail_silently=False)

    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True


def send_otp_mail(user, otp):
    subject = "Welcome to Growatpace"
    email_template_name = "email/send_otp_email.txt"

    c = {
        "email": user.email,
        "name": user.first_name,
        "otp": otp
    }
    email = render_to_string(email_template_name, c)
    try:
        mail = send_mail(subject, email, INFO_CONTACT_EMAIL, [user.email], fail_silently=False)
        print(mail)
        sent_mail_status(subject, email_template_name, email, mail, "OTP")
    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True


def sent_mail_status(subject, body, email, status, type):
    response = False
    try:
        EmailStatusList.objects.create(subject=subject, body=body, email=email, status=status, type=type)
        response = True
    except:
        response = False
    print(response)
    return response


def get_the_participants(journey):
    mentee_obj = UserChannel.objects.filter(Channel__id=journey)
    mentor_obj = AssignMentorToUser.objects.filter(journey__id=journey)

    mentees = [{"user_name":mentee.user.get_full_name(), "email":mentee.user.email} for mentee in mentee_obj]
    mentors = [{"user_name":mentor.user.get_full_name(), "email":mentor.user.email} for mentor in mentor_obj]
    # mentees = [{"user_name":mentee.user.get_full_name(), "email":mentee.user.email, "user_id":str(mentee.user.id)} for mentee in mentee_obj]
    # mentors = [{"user_name":mentor.user.get_full_name(), "email":mentor.user.email, "user_id":str(mentor.user.id)} for mentor in mentor_obj]

    return mentees, mentors


def add_participant_api(meeting_id, user_name, email, preset, call_type):
    url = f"{DYTE_BASE_URL}/meetings/{meeting_id}/participants"
    payload = json.dumps({
                "name": user_name,
                "custom_participant_id": email,
                "preset_name": preset
            })
    response = requests.request("POST", url, data=payload, auth=(DYTE_ORG_ID, DYTE_API_KEY), headers={"Content-Type":
                                                                                                               "application/json"})
    data = response.json()


    try:
        DyteAuthToken.objects.get(user_name=user_name, email=email, preset=preset, 
                                  meeting_id=meeting_id, call_type=call_type)
    except:
        DyteAuthToken.objects.create(user_name=user_name, email=email, authToken=data['data']['token'],
                                    preset=preset, preset_id=data['data']['preset_id'],
                                    meeting_id=meeting_id, participant_id=data['data']['id'], call_type=call_type)
        

def add_meet_participant(journey, meeting_id, call_type, program_manager=None, speaker=None, participants=None):     
    print("SPEAKER COMINg", speaker)   
    if journey:
        mentees, mentors = get_the_participants(journey)

        journey_users = mentees + mentors

        if speaker:
            try:
                speaker_of_call = User.objects.get(id=speaker)
            except:
                speaker_of_call = speaker
                
        for juser in journey_users:
            if speaker_of_call.email == juser['email']: 
                journey_users.remove(juser)
                break

        for journey_user in journey_users:
            if call_type == "livestream":
                add_participant_api(meeting_id, journey_user['user_name'], journey_user['email'], "group_call_participant", call_type)
                print(f"added {journey_user['email']} as livestream viewer")
            else:
                add_participant_api(meeting_id, journey_user['user_name'], journey_user['email'], "group_call_participant", call_type)
                print(f"added {journey_user['email']} as group call participant")

    if speaker:
        try:
            speaker_of_call = User.objects.get(id=speaker)
        except:
            speaker_of_call = speaker
        
        if call_type == "livestream":
            add_participant_api(meeting_id, speaker_of_call.get_full_name(), speaker_of_call.email, "group_call_host", call_type)
            print(f"ADDDED {speaker_of_call.email} as LIVE CALL host")
        else:
            add_participant_api(meeting_id, speaker_of_call.get_full_name(), speaker_of_call.email, "group_call_host", call_type)
            print(f"ADDDED {speaker_of_call.email} as GROUP CALL host")

        # adding all menting

    if program_manager:
        print("Program manager", program_manager.get_full_name(), program_manager.email)
        if call_type == "livestream":
            add_participant_api(meeting_id, program_manager.get_full_name(), program_manager.email, "group_call_participant", call_type)
            print("added as livestream viewer") 
        else:
            add_participant_api(meeting_id, program_manager.get_full_name(), program_manager.email, "group_call_participant", call_type)
            print("Program manager added in the call")

    if participants:
        for participant in participants:
            parti = User.objects.get(id=participant)
            if call_type == "livestream":
                add_participant_api(meeting_id, parti.get_full_name(), parti.email, "group_call_participant", call_type)
                print(f"ADDDED {parti.email} as LIVE CALL host")
            else:
                add_participant_api(meeting_id, parti.get_full_name(), parti.email, "group_call_participant", call_type)
                print(f"ADDDED {parti.email} as GROUP CALL participant ")

# dyte integration for livestream and groupcalls
def lives_streaming_room(name, call_type, journey=None, program_manager=None, speaker=None, participants=None):
    print("NAME", name)
    
    payload = json.dumps({
        "title": str(name),
        "preferred_region":"ap-southeast-1",
        "record_on_start": True,
	    "live_stream_on_start": False
    })

    # create meeting
    url = f"{DYTE_BASE_URL}/meetings"
    response = requests.request("POST", url, data=payload, auth=(DYTE_ORG_ID, DYTE_API_KEY), headers={"Content-Type": "application/json"})
    if response.status_code == 400 or response.status_code == 422:
        data = {"message": "Bad request or Unprocessable Entity", "success": False}
        return data, 400
    
    # generate the meet url after creating meeting
    elif response.status_code == 200 or response.status_code == 201:
        meet_id = response.json()['data']['id']
        meet_url = f"{BASE_URL}/config/dyte/{meet_id}"
        t = Thread(target=add_meet_participant, args=[journey, meet_id, call_type, program_manager, speaker, participants], daemon=True).start()
        return response.json(), meet_id
    else:
        data = {"message": f"Unknown error, response - {response.status_code} : {response.text}  ", "success": False}
        return data, 400
    

def edit_dyte_call(meet_id, call_type,journey=None, program_manager=None, speaker=None, participants=None):
    try:
        t = Thread(target=add_meet_participant, args=[journey, meet_id, call_type, program_manager, speaker, participants], daemon=True).start()
        print("Edited the call")
        return True, True
    except Exception as e:
        print("Error {e} while editing dyte call")
        return False, str(e)


# adding mentor and mentee to dyte meeting
def add_participant_for_mentor_mentee_call(user, meeting_id, host=False):
    url = f"{DYTE_BASE_URL}/meetings/{meeting_id}/participants"

    if host: preset = "group_call_host"
    else: preset = "group_call_participant"
    payload = json.dumps({
        "name": user.get_full_name(),
        "custom_participant_id": user.email,
        "preset_name": preset
    })
    response = requests.request("POST", url, data=payload, auth=(DYTE_ORG_ID, DYTE_API_KEY), headers={"Content-Type":
                                                                                                        "application/json"})
    data = response.json()
    print("DATA", data)
    DyteAuthToken.objects.create(user_name=user.get_full_name(), email=user.email, authToken=data['data']['token'],
                                    preset=preset, preset_id=data['data']['preset_id'], 
                                    meeting_id=meeting_id, participant_id=data['data']['id'], call_type="mentor-mentee")
    print("participant details saved")


def delete_meet_link(name):
    url = f"https://api.daily.co/v1/rooms/{name}"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.request("DELETE", url, headers=headers)
    res = response.json()
    print("response", response.status_code)
    if response.status_code == 404:
        return {"message": res['info']}
    return res


def meeting(name): 
    print("NAME", name)
    try:
        all_meet_details = AllMeetingDetails.objects.filter(title=name)
        print(len(all_meet_details))
    except Exception as e: print("EXCEPTION", e)

    obj = MeetingParticipants.objects.filter(session__in=all_meet_details)
    print("OBJECT", obj)
    user_names = [o.user_name for o in obj]
    return user_names


def get_title(obj):
    title = obj.url_title
    if not title:
        title = obj.custom_url.split('/')[-1]
        title = title.split("?")[0]
        return title
    return title


def meeting_logs(mtgSessionId):
    url = f"https://api.daily.co/v1/logs?mtgSessionId={mtgSessionId}&limit=200"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.request("GET", url, headers=headers)
    # print(response.text)
    return response.json()


def unixTimstamp(ts):
    date_time = datetime.fromtimestamp(ts)
    date_time = date_time.astimezone()
    return date_time.strftime('%Y-%m-%d %H:%M:%S')


def minutes(sec):
    s = time.gmtime(sec)
    return time.strftime("%H:%M:%S", s)


def asynmail(user, email):
    co1 = sendVerificationMail(user, email)
    loop = asyncio.get_event_loop(co1)
    if not loop.is_running() and not isinstance(loop, asyncio.ProactorEventLoop):
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    loop.close()


def update_signup_lite(user, type, user_type, journey_id):
    # print(f"user = {user}\ntype = {type}\nuser_type = {user_type}\njourney_id = {journey_id}")
    user_channel = UserChannel.objects.filter(user=user, Channel_id=journey_id)
    print("user_channel", user_channel)
    if not user_channel:
        return {"success": True, "message": f"You already have account with username: {user.username} and email: {user.email} and you can enroll for this journey"}
    else:
        if "Mentor" and "Learner" in type:
            return {"success": False, "message": "You're already enrolled in this journey."}
        elif user_type == "Mentor" and type == user_type:
            return {"success": False, "message": "You're already enrolled as Mentor in this journey. If you want to enrolled as Learner then click on Ok and changed the type"}
        elif user_type == "Learner" and type == user_type:
            return {"success": False, "message": "You're already enrolled as Learner in this journey. If you want to enrolled as Mentor then click on Ok and changed the type"}

def local_time(obj):
    return localtime(obj)

def convert_to_local_time(obj, offset):
    if offset:
        # Set the timezone you want to convert to
        tz = pytz.timezone(offset)

        # Get the current time in UTC
        utc_time = obj

        # Convert UTC time to the local timezone
        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(tz)
    else:
        local_time = obj
    
    return local_time

def strf_format(obj):
    return obj.strftime("%d-%m-%y %H:%M:%S %p")

def convert_to_utc(obj, offset):
    if not offset:
        offset = DEFAULT_TIMEZONE
    
    local = pytz.timezone(offset)
    naive = datetime.strptime(str(obj), "%Y-%m-%d %H:%M:%S")

    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)

    return utc_dt

def aware_time(date_time):
    utc = pytz.UTC
    return utc.localize(date_time)

def listing_mentor(values):
    count = 0
    data = []
    values = sorted(values, reverse=True)
    for value in values:
        count += 1
        if count < 3:
            data.append({
                "name": value[1],
                "match_percentage": f"{value[0]}% match",
                "id": str(value[2]),
                "question_id": value[3],
                "already_checked": ""
            })
        else:
            break
    return data

def menter_mentee_capacity(company, user):
    subscription_user = SubcribedUser.objects.filter(user=user, company=company,
                                                     is_subscribed=True, is_active=True, is_delete=False, is_cancel=False).last()
    if not subscription_user:
        return False
    mentor_mentee_ratio = MentorMenteeRatio.objects.filter(
        user_subscription=subscription_user, is_active=True, is_delete=False).first()
    if not mentor_mentee_ratio:
        mentor_mentee_ratio = MentorMenteeRatio.objects.filter(
            subscription=subscription_user.subscription, is_active=True, is_delete=False).first()
    return mentor_mentee_ratio

def matching_mentor_1(journey, pool, company):
    user_list = []
    pool_mentor = PoolMentor.objects.filter(pool=pool, mentor__is_active=True, mentor__is_delete=False)

    mentors = [mentor.mentor for mentor in pool_mentor]
    mentee_list = MenteeSummary.objects.filter(journey=journey).values("mentee__id", "mentee__first_name", "summary", "mentee__email")
    mentor_list = MentorSummary.objects.filter(journey=journey, mentor__in=mentors).values("mentor__id", "mentor__first_name", "summary", "mentor__email")
    manual_mentor_list = [{"name": mentor.first_name, "id": str(mentor.id)} for mentor in mentors]
    print("MANUAL MENTOR LIST ****", manual_mentor_list)
    
    for mentee in mentee_list:
        response = best_matches(mentees=[mentee], mentors=mentor_list, num_top_mentors=3)
        match_response = [ast.literal_eval(value) for value in response]
        
        poll_mentor_list = []
        for mentor in match_response:
            assign_check = AssignMentorToUser.objects.filter(journey=journey, mentor_id=mentor['ID'], 
                                                    user__id=mentee['mentee__id'], is_assign=True, is_revoked=False).first()
            poll_mentor_list.append({
                "name": mentor['Name'],
                "id": str(mentor['ID']),
                "match_percentage": mentor['Score'],
                "already_checked": str(assign_check.mentor.id) if assign_check else "",
                "assign_date": strf_format(local_time(assign_check.created_at)) if assign_check else ""
            })
    
        user_list.append({
            "user": mentee['mentee__id'],
            "email": mentee['mentee__email'],
            "name": mentee['mentee__first_name'],
            "company_id": str(company.id),
            "company_name": company.name,
            "journey_id": str(journey.id),
            "journey_name": journey.title,
            "poll_mentor_list": poll_mentor_list,
            "manual_assign_list": manual_mentor_list
        })
    return user_list

def matching_mentor(journey, pool, company, log_user):
    user_list = []

    user_channel = UserChannel.objects.filter(Channel=journey, user__userType__type="Learner", user__is_active=True, user__is_delete=False)
    pool_mentor = PoolMentor.objects.filter(pool=pool, mentor__is_active=True, mentor__is_delete=False)

    mentor_id_list = [mentor.mentor.pk for mentor in pool_mentor]
    mentor_list = [{"mentor": mentor.mentor.username, "name": f"{mentor.mentor.first_name} {mentor.mentor.last_name}", "id": str(
        mentor.mentor.pk)} for mentor in pool_mentor]

    journey_user_list = [[{"user": channel.user.username, "name": f"{channel.user.first_name} {channel.user.last_name}",
                           "id": str(channel.user.pk)}] for channel in user_channel]

    match_config = MatchQuesConfig.objects.filter(journey=journey, company=company).first()
    match_question = MatchQuestion.objects.filter(ques_config=match_config)

    for channel in user_channel:
        pool_list_1 = []
        pool_list_2 = []
        pool_list_3 = []
        user = channel.user
        print(f"user_: {user}")

        assign_check = AssignMentorToUser.objects.filter(journey=journey, mentor_id__in=mentor_id_list,
                                                         user=user, is_assign=True, is_revoked=False).first()
        if assign_check:
            pool_list_1.append({
                "name": f"{assign_check.mentor.first_name} {assign_check.mentor.last_name}",
                "id": str(assign_check.mentor.id),
                "already_checked": str(assign_check.mentor.id) if assign_check else "",
                "assign_date": strf_format(local_time(assign_check.created_at))
            })
            pool_list_2.append({
                "name": f"{assign_check.mentor.first_name} {assign_check.mentor.last_name}",
                "id": str(assign_check.mentor.id),
                "already_checked": str(assign_check.mentor.id) if assign_check else "",
                "assign_date": strf_format(local_time(assign_check.created_at))
            })
            pool_list_3.append({
                "name": f"{assign_check.mentor.first_name} {assign_check.mentor.last_name}",
                "id": str(assign_check.mentor.id),
                "already_checked": str(assign_check.mentor.id) if assign_check else "",
                "assign_date": strf_format(local_time(assign_check.created_at))
            })

        for question in match_question:

            # matching question one answer
            if question.question_type == "self":
                values = []
                profile_question_1 = ProfileAssestQuestion.objects.filter(
                    question=question.learner_ques.question, question_for="Learner", is_active=True, is_delete=False).values("id", "question").first()
                profile_assests_1 = UserProfileAssest.objects.filter(
                    user=user, assest_question__question=profile_question_1['question'], assest_question__question_for="Learner").values("id", "response").first()
                if profile_assests_1:
                    if question.is_dependent and (profile_assests_1['response'] == question.dependent_option):
                        profile_question_1_1 = ProfileAssestQuestion.objects.filter(
                            question=question.dependent_learner.question, question_for="Learner", is_active=True, is_delete=False).values("id", "question").first()
                        profile_assests_1_1 = UserProfileAssest.objects.filter(
                            user=user, assest_question__question=profile_question_1_1['question'], assest_question__question_for="Learner").values("id", "response").first()
                        if profile_assests_1_1:
                            for mentor1 in mentor_list:
                                value = fuzz.token_set_ratio(profile_assests_1_1['response'], mentor1["name"])
                                values.append([value, mentor1["name"], mentor1["id"], profile_assests_1_1['id']])
                            print("1 ", values)
                            if values:
                                pool_list_1.extend(listing_mentor(values))

            # matching question two answer
            elif question.question_type == "goal":
                values = []
                mentee_profile_question_2 = ProfileAssestQuestion.objects.filter(
                    question=question.learner_ques.question, question_for="Learner").values("id", "question").first()
                mentee_profile_assests_2 = UserProfileAssest.objects.filter(
                    user=user, assest_question__question=mentee_profile_question_2['question'], assest_question__question_for="Learner").values("id", "response").first()
                if mentee_profile_assests_2:
                    if question.is_dependent and (mentee_profile_assests_2['response'] == question.dependent_option):
                        dependent_mentee_profile_question_2 = ProfileAssestQuestion.objects.filter(
                            question=question.dependent_learner.question, question_for="Learner").values("id", "question").first()
                        dependent_mentee_profile_assests_2 = UserProfileAssest.objects.filter(
                            user=user, assest_question__question=dependent_mentee_profile_question_2['question'], assest_question__question_for="Learner").values("id", "response").first()
                        if dependent_mentee_profile_assests_2:
                            for mentor2 in mentor_list:
                                mentor_profile_question_2 = ProfileAssestQuestion.objects.filter(
                                    question=question.mentor_ques.question, question_for="Mentor").values("id", "question").first()
                                mentor_profile_assests_2 = UserProfileAssest.objects.filter(
                                    user_id=mentor2["id"], assest_question__question=mentor_profile_question_2['question'], assest_question__question_for="Mentor").values("id", "response").first()
                                if mentor_profile_assests_2:
                                    if question.is_dependent and (mentor_profile_assests_2['response'] == question.dependent_option):
                                        dependent_mentor_profile_question_2 = ProfileAssestQuestion.objects.filter(
                                            question=question.dependent_mentor.question, question_for="Mentor").values("id", "question").first()
                                        dependent_mentor_profile_assests_2 = UserProfileAssest.objects.filter(
                                            user_id=mentor2["id"], assest_question__question=dependent_mentor_profile_question_2['question'], assest_question__question_for="Mentor").values("id", "response").first()
                                        if dependent_mentor_profile_assests_2:
                                            value = fuzz.token_set_ratio(
                                                dependent_mentee_profile_assests_2["response"], dependent_mentor_profile_assests_2["response"])
                                            values.append(
                                                [value, mentor2["name"], mentor2["id"], dependent_mentee_profile_assests_2['id'], dependent_mentor_profile_assests_2['id']])
                                    else:
                                        value = fuzz.token_set_ratio(
                                            dependent_mentee_profile_assests_2["response"], mentor_profile_assests_2["response"])
                                        values.append(
                                            [value, mentor2["name"], mentor2["id"], dependent_mentee_profile_assests_2["id"], mentor_profile_assests_2['id']])
                            print("2 ", values)
                            if values:
                                pool_list_2.extend(listing_mentor(values))
                    else:
                        for mentor2 in mentor_list:
                            mentor_profile_question_2 = ProfileAssestQuestion.objects.filter(
                                question=question.mentor_ques.question, question_for="Mentor").values("id", "question").first()
                            mentor_profile_assests_2 = UserProfileAssest.objects.filter(
                                user_id=mentor2["id"], assest_question__question=mentor_profile_question_2['question'], assest_question__question_for="Mentor").values("id", "response").first()
                            if mentor_profile_assests_2:
                                if question.is_dependent and (mentor_profile_assests_2['response'] == question.dependent_option):
                                    dependent_mentor_profile_question_2 = ProfileAssestQuestion.objects.filter(
                                        question=question.dependent_mentor.question, question_for="Mentor").values("id", "question").first()
                                    dependent_mentor_profile_assests_2 = UserProfileAssest.objects.filter(
                                        user_id=mentor2["id"], assest_question__question=dependent_mentor_profile_question_2['question'], assest_question__question_for="Mentor").values("id", "response").first()
                                    if dependent_mentor_profile_assests_2:
                                        value = fuzz.token_set_ratio(
                                            mentee_profile_assests_2["response"], dependent_mentor_profile_assests_2["response"])
                                        values.append(
                                            [value, mentor2["name"], mentor2["id"], mentee_profile_assests_2["id"], dependent_mentor_profile_assests_2['id']])
                                else:
                                    value = fuzz.token_set_ratio(
                                        mentee_profile_assests_2["response"], mentor_profile_assests_2["response"])
                                    values.append([value, mentor2["name"], mentor2["id"],
                                                   mentee_profile_assests_2["id"], mentor_profile_assests_2['id']])
                        print("2 ", values)
                        if values:
                            pool_list_2.extend(listing_mentor(values))

            # #matching question three answer
            elif question.question_type == "industry":
                values = []
                mentee_profile_question_3 = ProfileAssestQuestion.objects.filter(
                    question=question.learner_ques.question, question_for="Learner").values("id", "question").first()
                mentee_profile_assests_3 = UserProfileAssest.objects.filter(
                    user=user, assest_question__question=mentee_profile_question_3['question'], assest_question__question_for="Learner").values("id", "response").first()
                if mentee_profile_assests_3:
                    if question.is_dependent and (mentee_profile_assests_3['response'] == question.dependent_option):
                        dependent_mentee_profile_question_3 = ProfileAssestQuestion.objects.filter(
                            question=question.dependent_learner.question, question_for="Learner").values("id", "question").first()
                        dependent_mentee_profile_assests_3 = UserProfileAssest.objects.filter(
                            user=user, assest_question__question=dependent_mentee_profile_question_3['question'], assest_question__question_for="Learner").values("id", "response").first()
                        if dependent_mentee_profile_assests_3:

                            for mentor3 in mentor_list:
                                mentor_profile_question_3 = ProfileAssestQuestion.objects.filter(
                                    question=question.mentor_ques.question, question_for="Mentor").values("id", "question").first()
                                mentor_profile_assests_3 = UserProfileAssest.objects.filter(
                                    user_id=mentor3["id"], assest_question__question=mentor_profile_question_3['question'], assest_question__question_for="Mentor").values("id", "response").first()
                                if mentor_profile_assests_3:
                                    if question.is_dependent and (mentor_profile_assests_3['response'] == question.dependent_option):
                                        dependent_mentor_profile_question_3 = ProfileAssestQuestion.objects.filter(
                                            question=question.dependent_mentor.question, question_for="Mentor").values("id", "question").first()
                                        dependent_mentor_profile_assests_3 = UserProfileAssest.objects.filter(
                                            user_id=mentor3["id"], assest_question__question=dependent_mentor_profile_question_3['question'], assest_question__question_for="Mentor").values("id", "response").first()
                                        if dependent_mentor_profile_assests_3:
                                            value = fuzz.token_set_ratio(
                                                dependent_mentee_profile_assests_3["response"], dependent_mentor_profile_assests_3["response"])
                                            values.append(
                                                [value, mentor3["name"], mentor3["id"], dependent_mentee_profile_assests_3['id'], dependent_mentor_profile_assests_3['id']])
                                    else:
                                        value = fuzz.token_set_ratio(
                                            dependent_mentee_profile_assests_3["response"], mentor_profile_assests_3["response"])
                                        values.append(
                                            [value, mentor3["name"], mentor3["id"], dependent_mentee_profile_assests_3["id"], mentor_profile_assests_3['id']])

                            print("3 ", values)
                            if values:
                                pool_list_3.extend(listing_mentor(values))
                    else:
                        for mentor3 in mentor_list:
                            mentor_profile_question_3 = ProfileAssestQuestion.objects.filter(
                                question=question.mentor_ques.question, question_for="Mentor").values("id", "question").first()
                            mentor_profile_assests_3 = UserProfileAssest.objects.filter(
                                user_id=mentor3["id"], assest_question__question=mentor_profile_question_3['question'], assest_question__question_for="Mentor").values("id", "response").first()
                            if mentor_profile_assests_3:
                                if question.is_dependent and (mentor_profile_assests_3['response'] == question.dependent_option):
                                    dependent_mentor_profile_question_3 = ProfileAssestQuestion.objects.filter(
                                        question=question.dependent_mentor.question, question_for="Mentor").values("id", "question").first()
                                    dependent_mentor_profile_assests_3 = UserProfileAssest.objects.filter(
                                        user_id=mentor3["id"], assest_question__question=dependent_mentor_profile_question_3['question'], assest_question__question_for="Mentor").values("id", "response").first()
                                    if dependent_mentor_profile_assests_3:
                                        value = fuzz.token_set_ratio(
                                            mentee_profile_assests_3["response"], dependent_mentor_profile_assests_3["response"])
                                        values.append(
                                            [value, mentor3["name"], mentor3["id"], mentee_profile_assests_3["id"], dependent_mentor_profile_assests_3['id']])
                                else:
                                    value = fuzz.token_set_ratio(
                                        mentee_profile_assests_3["response"], mentor_profile_assests_3["response"])
                                    values.append([value, mentor3["name"], mentor3["id"],
                                                   mentee_profile_assests_3["id"], mentor_profile_assests_3['id']])
                        print("3 ", values)
                        if values:
                            pool_list_3.extend(listing_mentor(values))
        user_list.append({
            "user": str(user.pk),
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}",
            "company_id": str(company.id),
            "company_name": company.name,
            "journey_id": str(journey.id),
            "journey_name": journey.title,
            "poll_mentor_1": pool_list_1,
            "poll_mentor_2": pool_list_2,
            "poll_mentor_3": pool_list_3,
            "manual_assign_list": mentor_list
        })

    return user_list

def program_announcement_email(topic, content, email_list, announce_by, attachment_info=None):
    subject = "Program Update Announcement"
    email_template_name = "email/program_update_announcement.txt"
    c = {
        'domain': DOMAIN,
        'site_name': SITE_NAME,
        'protocol': PROTOCOL,
        "topic": topic,
        "content": content,
        "announce_by": f"{announce_by.first_name} {announce_by.last_name}",
        "url": f"{PROTOCOL}://{DOMAIN}"
    }
    email = render_to_string(email_template_name, c)
    EmailThread(subject, email, email_list, attachment_info=attachment_info).start()
    # EmailThread(subject, email, email_list).start()
    return True

def jwt_encoding(user):
    return jwt.encode({"email": user.email, "user_id":str(user.id)}, JWT_SECRET_KEY, algorithm="HS256")

def jwt_decoding(token):
    data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    return data.get("user_id")

def marketplace_user_email(user):
    subject = "MarketPlace Mentor Profile Assessment"
    email_template_name = "email/mentor_profile_assessment.txt"
    jwt_token = jwt_encoding(user)
    c = {
        'domain': DOMAIN,
        'site_name': SITE_NAME,
        'protocol': PROTOCOL,
        "mentor_name": user.get_full_name(),
        "email": user.email,
        "password": "Please use your existing password, If you have not udated your password then check your previous email for Login credentials",
        "url": f"{PROTOCOL}://{DOMAIN}/user/profile-assessment/{user.id}/?token={jwt_token}"
    }
    email = render_to_string(email_template_name, c)
    EmailThread(subject, email, [user.email]).start()
    return True

class EmailThread(Thread):
    def __init__(self, subject, email, email_list, attachment_info = None):
        self.subject = subject
        self.recipient_list = email_list
        self.html_content = email
        self.attachment_info = attachment_info
        Thread.__init__(self)

    def run(self):
        for email in self.recipient_list:
            try:
                if not self.attachment_info==None:
                    mail = EmailMessage(self.subject, self.html_content, INFO_CONTACT_EMAIL, [email])
                    try:
                        name = self.attachment_info[0]
                        content = self.attachment_info[1]
                        content_type = self.attachment_info[2]
                        mail.attach(filename=name, mimetype=content_type, content=content)
                    except Exception as e:
                        print("Error while attching the file", e)
                    mail.send()
                    print('sent the email to', email)
                else:
                    EmailMessage(self.subject, self.html_content, INFO_CONTACT_EMAIL, [email]).send()
            except BadHeaderError:
                return HTTPResponse('Invalid header found.')
        return True

def registration_list(user, filter_user=None, filter_assessment=None, filter_journey=None, company_id=None, offset=None):
    company = user_company(user, company_id)
    pool_list = []
    pools = Pool.objects.filter(company__in=company, journey__closure_date__gt=datetime.now(), is_active=True)

    mentor_list = PoolMentor.objects.filter(pool__in=pools).values('mentor')
    user_type = UserTypes.objects.filter(type__in=['Learner', 'Mentor'])
    user_list = User.objects.filter(company__in=company, userType__in=user_type,
                                    is_delete=False, is_active=True, is_archive=False).distinct()

    if filter_user:
        user_list = user_list.filter(Q(first_name__contains=filter_user) | Q(last_name__contains=filter_user))

    users = user_list

    if filter_assessment:
        users = []
        if filter_assessment == "complete":
            for user in user_list:
                if user.user_profile_assest.all().count() != 0:
                    users.append(user)

        else:
            for user in user_list:
                if user.user_profile_assest.all().count() == 0:
                    users.append(user)

    check_mentor = []
    for mentor_list in mentor_list:
        check_mentor.append(mentor_list['mentor'])

    registration_list = []
    for user in users:
        type_id_list = []
        for type in user.userType.all():
            type_id_list.append({"type": str(type.type), "user_id": user.id})

        for journey in user.user_content.filter(Channel__closure_date__gt=datetime.now(), Channel__company__in=company, Channel__is_active=True, Channel__is_delete=False):
            if filter_journey:
                if filter_journey == journey.Channel.title:
                    registration_list.append({
                        "user_id": user.id,
                        "fullname": f"{user.first_name} {user.last_name}",
                        "username": user.username,
                        "email": user.email,
                        "phone": str(user.phone),
                        "profile_assest": "complete" if user.user_profile_assest.all().count() != 0 else "pending",
                        "type": type_id_list,
                        "is_active": user.is_active,
                        "date_joined": user.date_joined,
                        "date_modified": convert_to_local_time(user.date_modified, offset),
                        "is_lite_signup": user.is_lite_signup,
                        "is_archive": user.is_archive,
                        "journey_id": journey.Channel.id,
                        "journey_name": journey.Channel.title,
                        "journey_type": journey.Channel.channel_type,
                        "in_check_mentor": True if user.id in check_mentor else False
                    })

            else:
                registration_list.append({
                    "user_id": user.id,
                    "fullname": f"{user.first_name} {user.last_name}",
                    "username": user.username,
                    "email": user.email,
                    "phone": str(user.phone),
                    "profile_assest": "complete" if user.user_profile_assest.all().count() != 0 else "pending",
                    "type": type_id_list,
                    "is_active": user.is_active,
                    "date_joined": strf_format(local_time(user.date_joined)),
                    "date_modified": strf_format(local_time(user.date_modified)),
                    "is_lite_signup": user.is_lite_signup,
                    "is_archive": user.is_archive,
                    "journey_id": journey.Channel.id,
                    "journey_name": journey.Channel.title,
                    "in_check_mentor": True if user.id in check_mentor else False
                })

    context = {
        "message": "User Registration List",
        "registration_list": registration_list,
        "pool": pool_list,
        "check_mentor": check_mentor,
        "success": True
    }
    return context

def company_logo(obj):
    if obj.logo:
        logo = str(obj.logo.url)
        logo = logo.split('?')
        return logo[0]
    else:
        return ''

def send_user_certificate_mail(user, certificate, journey, company, program_team, designation, offset=None):
    subject = "Certificate"
    email_template_name = "email/send_email_for_user_certificate.txt"

    c = {
        'domain': DOMAIN,
        'site_name': SITE_NAME,
        "login_url": LOGIN_URL,
        "user_name": user.get_full_name(),
        "journey": journey,
        "company": company,
        "program_team": program_team, 
        "designation": designation,
        "time_zone": offset,
    }
    email = render_to_string(email_template_name, c)

    try:
        mail = EmailMessage(subject, email, INFO_CONTACT_EMAIL, [user.email])
        name = certificate.name
        content = certificate.read()
        mail.attach(name, content)
        mail.send()
    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True

def send_activity_email(activity, email, name, file_name):

    subject = f"{activity} Report"
    email_template_name = "email/send_activity_report.txt"
    c = {"name": name}
    email_string = render_to_string(email_template_name, c)

    try:
        mail = EmailMessage(subject, email_string, INFO_CONTACT_EMAIL, [email])
        # mail = EmailMessage(subject, email_string, INFO_CONTACT_EMAIL, ["sarvesh@growatpace.com"])
        with open(file_name, 'rb') as file:
            mail.attach('Report.csv', file.read(), 'text/csv')
        mail.send()
    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True

def getJourneyUsers(journey):
    pool_mentor = PoolMentor.objects.filter(pool__journey=journey, pool__journey__closure_date__gt=datetime.now(), is_active=True)
    mentors_list = [mentor.mentor for mentor in pool_mentor]
    user_channel = UserChannel.objects.filter(Channel=journey, is_removed=False, Channel__closure_date__gt=datetime.now(), status="Joined")
    learners_list = [user.user for user in user_channel]
    print
    mentors_list.extend(learners_list)

    return mentors_list

def removeUserSlotFun(slot_id, slot_type, user):
    if slot_type == 'LiveStreaming' or 'GroupStreaming':
        try:
            collabarate = Collabarate.objects.get(id=slot_id)
        except Collabarate.DoesNotExist:
            data = {"Message": 'Slot does not exist', "Success": False}
            return data
        collabarate.participants.remove(user)
        data = {
            "Message": 'Slot Removed Successfully',
            "Success": True
        }
        return data
    data = {
        "Message": 'Slot can not be deleted',
        "Success": False
    }
    return data

def send_reminder(task):
    assign_task_users = AssignTaskToUser.objects.filter(task=task, is_assigned=True, is_revoked=False, is_active=True, is_delete=False)

    for assign_task in assign_task_users:

        subject = "Task Reminder"
        email_template_name = "email/task_reminder.txt"

        c = {
            'domain': DOMAIN,
            'site_name': SITE_NAME,
            "user": assign_task.assigned_to.first_name + " " + assign_task.assigned_to.last_name,
            "task_name": task.title,
            "start_time": task.start_time,
            "due_time": task.due_time,
            "description": task.description
        }
        email_string = render_to_string(email_template_name, c)
        try:
            send_mail(subject, email_string, 'info@growatpace.com', [assign_task.assigned_to.email], fail_silently=False)
        except BadHeaderError:
            return HttpResponse('Invalid header found.') 

        message = f"""
            Hello,\n
            Reminder for the task {task.title}\n\n
            By: {assign_task.assigned_by.first_name} {assign_task.assigned_by.last_name}\n
            Regards,\n
            Program Team
        """

        room = get_chat_room(assign_task.assigned_by, assign_task.assigned_to)
        room = AllRooms.objects.get(name=room)
        chat = Chat.objects.create(from_user=assign_task.assigned_by, to_user=assign_task.assigned_to, message=message, room=room)

    return True

def send_certificate_email_by_manager(email, user_name, journey, file_name):
    subject = f"🎉 Congratulations on Completing the Program! 🎉"
    email_template_name = "email/certificate.txt"
    c = {"user_name": user_name, "journey": journey}
    email_string = render_to_string(email_template_name, c)

    try:
        mail = EmailMessage(subject, email_string, INFO_CONTACT_EMAIL, [email])
        # mail = EmailMessage(subject, email_string, INFO_CONTACT_EMAIL, ["sarvesh@growatpace.com"])
        with open(f'static/{file_name}.png' , 'rb') as file:
            mail.attach('Certificate.png', file.read(), 'image/png')
        mail.send()
        try: os.remove(f'static/{file_name}.png')
        except: print("File not deleted")
    except BadHeaderError:
        return HTTPResponse('Invalid header found.')
    return True

#users active on prod for client request
def active_users():
    email_list = """abhi@growatpace.com
hazrilharith@gmail.com
andhykas@gmail.com
angeline.soh@hotmail.com
heyang99@hotmail.com
anthonytan@ear.com.sg
a88109277@gmail.com
lutbatb@gmail.com
catleegc@hotmail.com
chiafj7@gmail.com
dawong1991@gmail.com
oyundulguun@gmail.com
ernest.tan.office@gmail.com
eva.musyrifah@sunlife.com
farida.budhiyati@sunlife.com
gerleflamme@gmail.com
haydar.maks@sunlife.com
hiroaki.morii.5900@idemitsu.com
inga.nuh@sunlife.com
irdinasyaurah02@gmail.com
isabellhlim@gmail.com
jacksontan@thejacksontan.com
jessica.adrianto@sunlife.com
jocelynyeojx@gmail.com
jolenedhrmp@gmail.com
simanungkalitkaiser@gmail.com
khandmaa.d@monos.mn
Leeann.tiong.0590@idemitsu.com
tfliew@hotmail.com
18051238803@163.com
malathi.ck@gmail.com
jenamalay@gmail.com
m.agarwal2905@gmail.com
kh.mandalmaa@gmail.com
marz14790@gmail.com
mayling.lim18@gmail.com
mendbayar@global-tm.mn
metna.hakim@sunlife.com
mindy_tang@yellowribbon.gov.sg
munkhtuulg@yahoo.com
narantsatsral.hr@gmail.com
bichngapharm@gmail.com
oliver.kneittinger@outlook.com
ponlokt18@gmail.com
ravi@growatpace.com
reiskoh@gmail.com
reny.bernadetta@sunlife.com
resga.muchren@sunlife.com
SAKINAH004@e.ntu.edu.sg
siewching.soh.0050@idemitsu.com
stevekhy@gmail.com
maoxiaoya0624@hotmail.com
ravi@ravinsight.com
uranjargal@monos.mn
wafiq.dawood@gmail.com
werner.pattiradjawane@sunlife.com
wulan.ranny@gmail.com
lawrence.p.young@gmail.com"""
    email_list = email_list.split('\n')
    activated_users_list = []
    for email in email_list:
        if User.objects.filter(email__iexact=email, is_active=False).exists():
            activated_users_list.append(email)
            User.objects.filter(email__iexact=email).update(is_active=True)
    return email_list

def invoke_endpoint(client, data):
    ENDPOINT_NAME = "huggingface-summarization12-4-svl"
    response = client.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Accept="application/json",
        Body=json.dumps({"inputs": data}),
    )
    result = json.loads(response["Body"].read().decode()) if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200 else None
    return result

def process_data(profile:dict, profession:str, client):
    if profession.lower() == 'mentee' or profession.lower() == 'mentor':
        if profile.get('Expertize'): profile["responses"].append(f"I have Expertize in {profile['Expertize']}.")

        if profile.get('Interested Topic'): profile["responses"].append(f"I have Interest in {profile['Interested Topic']}.")

        if profile.get('Industry'): profile["responses"].append(f"The industry in which I work in is {profile['Industry']}.")

        if profile.get('Organization'): profile["responses"].append(f"I work in an organisation named {profile['Organization']}.")

        if profile.get('Position'): profile["responses"].append(f"My position at work is {profile['Position']}.")

        if profile.get('Profile Heading'): profile["responses"].append(f"Profile Heading: {profile['Profile Heading']}.")

        if profile.get('Upscaling Reason'): profile["responses"].append(f"I am upscaling myself because {profile['Upscaling Reason']}.")

        if profile.get('Favourite Way to Learn'): profile["responses"].append(f"My favorite way to learn is {profile['Favourite Way to Learn']}.")

        if profile.get('About Us'): profile["responses"].append(f"About me: {profile['About Us']}.")

        # if profile.get('responses'):
        #     for response in profile.get('responses'): profile["responses"].append(f"About me: {profile['About Us']}.")

        detail = '.'.join(profile.get('responses'))
        summary = invoke_endpoint(client, detail)
        if summary[0].get('summary_text'):
            return summary[0]['summary_text']
    return None
