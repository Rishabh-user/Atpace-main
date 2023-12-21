import vonage
from ravinsight.web_constant import VONAGE_KEY, VONAGE_SECRET
from ravinsight.settings.base import BASE_DIR, DYTE_ORG_ID,DYTE_BASE_URL, DYTE_API_KEY
from ravinsight.web_constant import BASE_URL
from datetime import date
import re, requests
import random
import string
import requests
from apps.users.models import Collabarate, Company
import phonenumbers
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from apps.vonage_api.utils import whatsapp_otp_login
from .serializers import CategorySerializers
from .models import JourneyCategory, UrlShortner
from apps.content.models import MentoringJourney, ContentData, UserReadContentData
from apps.mentor.models import AssignMentorToUser, mentorCalendar, DyteAuthToken
from apps.community.models import LearningJournals, LearningJournalsComments
from apps.users.models import User
from apps.users.utils import get_title, meeting, send_otp_mail, sendVerificationMail
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.views import View
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
import math, queue, json
from threading import Thread
import pandas as pd
from ast import literal_eval
import json
from django.http import HttpResponse
from apps.mentor.models import *

que = queue.Queue()

def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def clean_text(w):
    w = re.sub(r'(\d+)(\.\d+)?', '', w)
    w = re.sub(r'(\s[a-zA-Z]\s)', '', w)
    w = re.sub(r'([^\x41-\x7A\x20]+)|([\r\n\"\'\t\s]+)', '', w)
    w = re.sub(r'\s+', '', w)
    w = re.sub(r'[^a-zA-Z0-9 \n\.]', '', w)
    return w.strip()+random.choice(string.ascii_uppercase + string.digits)


def generateRandomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))


# def sendVerificationMail(user, receiver_email):
#     subject = 'Account Verification'
#     from_email = 'mEinstein <no_replay@meinstein.ai>'
#     to = receiver_email
#     url = 'https://meinstein.ai/user/verify/'+receiver_email+'/'
#     html_message = rend
#     er_to_string(
#         'emailui.html', {'user': user.first_name, 'url': url})
#     plain_message = strip_tags(html_message)
#     mail.send_mail(subject, plain_message, from_email,
#                    [to], html_message=html_message)
#     return True


def reset_passwordMail(user, otp):
    subject = 'Account Verification'
    from_email = 'Growatpace <info@growatpace.com>'
    to = user.email
    subject = "Password Reset Requested"
    email_template_name = "email/password_reset_otp.txt"
    c = {
        "otp": otp
    }
    email = render_to_string(email_template_name, c)
    mail.send_mail(subject, strip_tags(email), from_email, [to])
    return True


def all_categories_list():
    category = JourneyCategory.objects.all()
    serializer = CategorySerializers(category, many=True)
    return serializer.data


def send_otp(user, otp):
    mobile = str(user.phone)
    # print(str(mobile))
    number = phonenumbers.parse(mobile, None).national_number
    country_code = phonenumbers.parse(mobile, None).country_code

    url = "https://api.authkey.io/request?authkey=a5d290db7118dbc5&mobile=" + \
        str(number)+"&country_code="+str(country_code)+"&sid=2828&var="+otp
    res = requests.get(url)
    if not user.is_email_verified:
        sendVerificationMail(user, user.email)
    send_otp_mail(user, otp)
    whatsapp_otp_login(user, otp)
    print("Mobile otp ",res.json())
    return True

def vonage_sms_otp(user, otp, phone=None):
    client = vonage.Client(key=VONAGE_KEY, secret=VONAGE_SECRET)
    sms = vonage.Sms(client)
    if phone:
        to_number = str(phone)
    else:
        to_number = str(user.phone)
    responseData = sms.send_message({
            "from": "Vonage APIs",
            "to": to_number,
            "text": f"Welcome To AtPace\n\nUse this verification code velow to finish logging\n\nYour login code is: {otp}",
        })

    if responseData["messages"][0]["status"] == "0":
        print("Message sent successfully.")
    else:
        print(f"Message failed with error: {responseData['messages'][0]['error-text']}")
    # if not user.is_email_verified:
    #     sendVerificationMail(user, user.email)
    # send_otp_mail(user, otp)
    # whatsapp_otp_login(user, otp)

    return True

def vonage_sms_otp_sender(user, otp, phone=None): # working as of 15 june, replaced the send_otp and vonage_send_otp function
    if user.phone:
        url = "https://rest.nexmo.com/sms/json"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        print("Calling Nexmo")

        if phone: to_number = str(phone)
        else: to_number = str(user.phone)

        if to_number == None:
            send_otp_mail(user, otp)
            return

        if not "+" in to_number: to_number = "+" + to_number 
        print("TO NUMBER", to_number)

        from_title = "ATPACE"
        country_code = phonenumbers.parse(to_number,None).country_code
        if str(country_code) == "65": from_title = "@PacePgme"

        print("CountryCode", country_code)

        data = {
            "to": to_number,
            "from": from_title,
            "text": f"Welcome to ATPACE\n\nUse this verification code below to finish logging\n\nYour login code is: {otp}",
            "api_key": VONAGE_KEY, 
            "api_secret": VONAGE_SECRET 
        }

        r = requests.post(url, headers=headers, params=data)
        if not user.is_email_verified:
            sendVerificationMail(user, user.email)
        send_otp_mail(user, otp)
        whatsapp_otp_login(user, otp)
    if not user.is_email_verified:
        sendVerificationMail(user, user.email)
    send_otp_mail(user, otp)
    return True

def check_journal_is_fill(journey, user, journals_list, week):
    response = 0
    journal_id = False
    journal = "Week {0} Journal".format(week)
    try:
        weekely_journal_id = journals_list[journal]
        journal_id = True
    except:
        pass
    if journal_id:
        learning_journal = LearningJournals.objects.filter(
            journey_id=journey.pk, weekely_journal_id=weekely_journal_id, email=user.email)
        if learning_journal.count() > 0:
            response = 100

    return response


def mentor_check_journal_is_fill(journey, user, mentor, journals_list, week):
    response = 0
    journal_id = False
    journal = "Week {0} Journal".format(week)
    try:
        weekely_journal_id = journals_list[journal] # journals_list is a dict
        journal_id = True
    except: pass

    if journal_id:
        learning_journal = LearningJournals.objects.filter(
            journey_id=journey.pk, weekely_journal_id=weekely_journal_id, email=user.email)
        print(learning_journal)
        if learning_journal.count() > 0:
            learning_journal = learning_journal.first()
            journal_comment = LearningJournalsComments.objects.filter(
                learning_journal=learning_journal, user_email=mentor.email, user_id=mentor.pk)
            print("learning_journal", journal_comment)
            if journal_comment.count() > 0:
                response = 100

    return response


def check_user_content_read_status(user, content):
    complete = 0
    content_data_list = ContentData.objects.filter(content=content)
    for content_data in content_data_list:
        try:
            read_content = UserReadContentData.objects.get(user=user,  content_data=content_data)
            status = read_content.status
        except:
            status = "Start"

        # print(status)
        if status == "Complete":
            complete = complete + 1

    if not content_data_list.count() == 0: complete_status = (complete/content_data_list.count())*100
    else: complete_status = complete * 100.0
    return complete_status


def one_to_one_call(meet):
    title = get_title(meet)
    data = meeting(title)
    if not data:
        return 0
    return 100


# def journey_meeting_attendi(user, meet):
#     attend = 0
#     title = get_title(meet)
#     print(title, "TITLE")
#     data = meeting(title)['data']
#     if not data:
#         return attend
#     for data in data[0]['participants']:
#         if user.email == data['user_name']:
#             attend = 100
#     return attend


def journey_meeting_attendi(user, meet):
    attend = 0
    title = get_title(meet)
    print(title, "TITLE")
    data = meeting(title)
    if not data:
        return attend
    if user.email in data:
        attend = 100
    return attend


def generate_attendence_for_rasa(journey):

    mentoring_journey = MentoringJourney.objects.filter(journey=journey, meta_key="journals", is_delete=False)
    j = 1
    journals_list = {mentoring_journey.name: mentoring_journey.value for mentoring_journey in mentoring_journey}

    assign_journey = AssignMentorToUser.objects.filter(journey=journey, is_assign=True)
    data = []
    count = 1

    collabarate = Collabarate.objects.filter(journey=journey.pk, is_cancel=False, start_time__lte=date.today())
    live_session = collabarate.filter(type="LiveStreaming")
    group_session = collabarate.filter(type="GroupStreaming")

    learn = MentoringJourney.objects.filter(journey=journey, meta_key="quest", is_delete=False)
    for i in assign_journey:
        learner_meet = 0
        mentor_meet = 0
        learner_attend_calls = 0
        mentor_attend_calls = 0
        learner_attend_sessions = 0
        mentor_attend_sessions = 0
        overall_learn = 0
        overall_mentee_journal = 0
        overall_mentor_journal = 0
        overall_calls = 0
        overall_livestream = 0
        temp_1 = {
            "Group": count,
            "Role": "Mentor",
            "Name": i.mentor.first_name,
            "Overall": "",
            "Learn": "",
            "Journal": "",
            "Calls": "",
            "Live Session": "",
            "Group Session": "",
            "One To One": "",
        }

        temp_2 = {
            "Group": count,
            "Role": "Mentee",
            "Name": i.user.first_name,
            "Overall": "",
            "Learn": "",
            "Journal": "",
            "Calls": "",
            "Live Session": "",
            "Group Session": "",
            "One To One": "",
        }

        temp_3 = {
            "Group": "",
            "Role": "",
            "Name": "",
            "Overall": "",
            "Learn": "",
            "Journal": "",
            "Calls": "",
            "Live Session": "",
            "Group Session": "",
            "One To One": "",
        }

        for j in range(1, 16):
            temp_learning_journal = math.ceil(mentor_check_journal_is_fill(journey,
                                                                           i.user, i.mentor, journals_list, j))
            temp_mentor_journal = math.ceil(check_journal_is_fill(journey, i.user, journals_list, j))
            overall_mentee_journal = temp_learning_journal + overall_mentee_journal
            overall_mentor_journal = temp_mentor_journal + overall_mentor_journal
            temp_1.update({"Journal " + str(j):  temp_learning_journal, })
            temp_2.update({"Journal " + str(j):  temp_mentor_journal, })
            temp_3.update({"Journal " + str(j):  "", })

        for k in range(len(learn)):
            print(learn[k], "11")

            temp_overall_learn = math.ceil(check_user_content_read_status(i.user, learn[k].value))
            overall_learn = temp_overall_learn + overall_learn
            print(overall_learn, "212")
            temp_1.update({"Learn " + str(k+1):  temp_overall_learn, })
            temp_2.update({"Learn " + str(k+1):  "", })
            temp_3.update({"Learn " + str(k+1):  "", })
        temp_1['Journal'] = math.ceil(overall_mentee_journal/15)
        temp_2['Journal'] = math.ceil(overall_mentor_journal/15)
        temp_1['Learn'] = math.ceil(overall_learn/len(learn))

        for meet in range(len(live_session)):
            learner_attend = journey_meeting_attendi(i.user, live_session[meet])
            learner_attend_sessions += learner_attend
            temp_1.update({"Live Session " + str(meet+1):  learner_attend, })
            mentor_attend = journey_meeting_attendi(i.mentor, live_session[meet])
            mentor_attend_sessions += mentor_attend
            temp_2.update({"Live Session " + str(meet+1):  mentor_attend, })
        temp_1['Live Session'] = math.ceil(learner_attend_sessions/live_session.count()
                                           if mentor_attend_sessions > 0 else 0)
        temp_2['Live Session'] = math.ceil(mentor_attend_sessions/live_session.count()
                                           if mentor_attend_sessions > 0 else 0)

        for meet in range(len(group_session)):
            learner_attend = journey_meeting_attendi(i.user, group_session[meet])
            learner_attend_calls += learner_attend
            temp_1.update({"Group Session " + str(meet+1):  learner_attend, })
            mentor_attend = journey_meeting_attendi(i.mentor, group_session[meet])
            mentor_attend_calls += mentor_attend
            temp_2.update({"Group Session " + str(meet+1):  mentor_attend, })
        temp_1['Group Session'] = math.ceil(learner_attend_calls/group_session.count()
                                            if learner_attend_calls > 0 else 0)
        temp_2['Group Session'] = math.ceil(mentor_attend_calls/group_session.count()
                                            if mentor_attend_calls > 0 else 0)

        booked_slots = mentorCalendar.objects.filter(
            mentor=i.mentor, slot_status="Booked", participants=i.user, start_time__gte=date.today(), status="Upcoming")
        print("booked_slots ", booked_slots, i.mentor, i.user)
        for slot in range(len(booked_slots)):
            learner_attend = one_to_one_call(booked_slots[slot])
            learner_meet += learner_attend
            temp_1.update({"One To One " + str(slot+1):  learner_attend, })
            mentor_attend = journey_meeting_attendi(i.mentor, group_session[meet])
            mentor_meet += mentor_attend
            temp_2.update({"One To One " + str(slot+1):  mentor_attend, })

        temp_1['One To One'] = math.ceil(learner_meet/booked_slots.count() if learner_meet > 0 else 0)
        temp_2['One To One'] = math.ceil(mentor_meet/booked_slots.count() if mentor_meet > 0 else 0)
        temp_1['Calls'] = 0
        temp_1['Overall'] = math.ceil((temp_1['Journal'] + temp_1['Learn'] +
                                      temp_1['Calls'] + temp_1['Live Session'])/4)
        data.append(temp_1)
        data.append(temp_2)
        data.append(temp_3)

    return data

def url_shortner(long_url, domain):
    # def url_shortner(long_url):
    if url := UrlShortner.objects.filter(long_url=long_url).first():
        return f"{domain}/re/{url.short_url}"

    s = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    short_url = ("".join(random.sample(s, 6)))
    UrlShortner.objects.create(long_url=long_url, short_url=short_url)

    return f"{domain}/re/{short_url}"
    # return short_url

def get_words():
    filename = f"{BASE_DIR}/static/wordlist.txt"
    f = open(filename)
    wordlist = f.readlines()
    return [w.strip() for w in wordlist if w]

def get_check_words(data):
    data = data.split(" ")
    return [re.sub(r"[^a-zA-Z0-9]+", ' ', k) for k in data]

def check_inappropriate_words(data):
    words = set(get_words())
    check_words = set(get_check_words(data))
    return words.intersection(check_words)

def update_journals(i, journey, journals_dict, que):
    print("JOURNALS STARTED")
    mentee_dict, mentor_dict, no_role_dict = {}, {}, {}
    overall_mentee_journal = 0
    overall_mentor_journal = 0 
    for j in range(1, 16):
        temp_learning_journal = math.ceil(mentor_check_journal_is_fill(journey,i.user, i.mentor, journals_dict, j))
        temp_mentor_journal = math.ceil(check_journal_is_fill(journey, i.user, journals_dict, j))
        overall_mentee_journal = temp_learning_journal + overall_mentee_journal
        overall_mentor_journal = temp_mentor_journal + overall_mentor_journal
        mentor_dict.update({"Journal " + str(j):  temp_learning_journal, })
        mentee_dict.update({"Journal " + str(j):  temp_mentor_journal, })
        no_role_dict.update({"Journal " + str(j):  "", })
    mentee_dict['Journal'] = math.ceil(overall_mentee_journal/15)
    mentor_dict['Journal'] = math.ceil(overall_mentor_journal/15)
    print("JOURNALS ENDED")
    que.put([mentee_dict, mentor_dict, no_role_dict])

def update_learnings(i, learn, que):
    print("LEARINGS STARTED")
    mentee_dict, mentor_dict, no_role_dict = {}, {}, {}
    overall_learn = 0

    for k in range(len(learn)):
        print(learn[k], "11")
        temp_overall_learn = math.ceil(check_user_content_read_status(i.user, learn[k].value))
        overall_learn = temp_overall_learn + overall_learn
        print(overall_learn, "212")
        mentee_dict.update({"Learn " + str(k+1):  temp_overall_learn, })
        mentor_dict.update({"Learn " + str(k+1):  "", })
        no_role_dict.update({"Learn " + str(k+1):  "", })
    mentee_dict['Learn'] = math.ceil(overall_learn/len(learn))
    print("LEARNINGS ENDED")
    que.put([mentee_dict, mentor_dict])

def update_live_sessions(i, live_session, que):
    print("LIVE STARTED")
    mentee_dict, mentor_dict = {}, {}
    learner_attend_sessions = 0
    mentor_attend_sessions = 0
    for meet in range(len(live_session)):
        learner_attend = journey_meeting_attendi(i.user, live_session[meet])
        learner_attend_sessions += learner_attend
        mentee_dict.update({"Live Session " + str(meet+1):  learner_attend, })
        mentor_attend = journey_meeting_attendi(i.mentor, live_session[meet])
        mentor_attend_sessions += mentor_attend
        mentor_dict.update({"Live Session " + str(meet+1):  mentor_attend, })
    live_session_count = live_session.count()
    mentee_dict['Live Session'] = math.ceil(learner_attend_sessions/live_session_count
                                           if mentor_attend_sessions > 0 else 0)
    mentor_dict['Live Session'] = math.ceil(mentor_attend_sessions/live_session_count
                                           if mentor_attend_sessions > 0 else 0)     
    print("LIVE ENDED")
    que.put([mentee_dict, mentor_dict])   

def update_group_sessions(i, group_session, que):
    print("GROUP STARTED")
    mentee_dict, mentor_dict = {}, {}
    learner_attend_calls = 0
    mentor_attend_calls = 0
    for meet in range(len(group_session)):
        learner_attend = journey_meeting_attendi(i.user, group_session[meet])
        learner_attend_calls += learner_attend
        mentee_dict.update({"Group Session " + str(meet+1):  learner_attend, })
        mentor_attend = journey_meeting_attendi(i.mentor, group_session[meet])
        mentor_attend_calls += mentor_attend
        mentor_dict.update({"Group Session " + str(meet+1):  mentor_attend, })
    group_session_count = group_session.count()
    mentee_dict['Group Session'] = math.ceil(learner_attend_calls/ group_session_count
                                if learner_attend_calls > 0 else 0)
    mentor_dict['Group Session'] = math.ceil(mentor_attend_calls/ group_session_count
                                if mentor_attend_calls > 0 else 0)
    print("GROUP ENDED")
    que.put([mentee_dict, mentor_dict])        

def update_booked_slots(i, booked_slots, group_session, que):
    print("BOOKED STARTED")
    mentee_dict, mentor_dict = {}, {}
    learner_meet = 0
    mentor_meet = 0
    for slot in range(len(booked_slots)):
        learner_attend = one_to_one_call(booked_slots[slot])
        learner_meet += learner_attend
        mentee_dict.update({"One To One " + str(slot+1):  learner_attend, })
        mentor_attend = journey_meeting_attendi(i.mentor, group_session[slot])
        mentor_meet += mentor_attend
        mentor_dict.update({"One To One " + str(slot+1):  mentor_attend, })
    mentee_dict['One To One'] = math.ceil(learner_meet/booked_slots.count() if learner_meet > 0 else 0)
    mentor_dict['One To One'] = math.ceil(mentor_meet/booked_slots.count() if mentor_meet > 0 else 0)
    mentee_dict['Calls'] = 0
    print("BOOKED ENDED")
    que.put([mentee_dict, mentor_dict])
    
# def generate_attendence(user, journey):
#     mentoring_journey = MentoringJourney.objects.filter(journey=journey, is_delete=False)
#     journals = mentoring_journey.filter(meta_key="journals")
#     learn = mentoring_journey.filter(meta_key="quest")

#     journals_dict = {journal.name: journal.value for journal in journals}

#     assign_journey = AssignMentorToUser.objects.filter(journey=journey, is_assign=True)
#     data = []
#     count = 1

#     collabarate = Collabarate.objects.filter(journey=journey.pk, is_cancel=False, start_time__lte=date.today())
#     live_session = collabarate.filter(type="LiveStreaming")
#     group_session = collabarate.filter(type="GroupStreaming")
    
#     journal_thread_list, learn_thread_list , live_thread_list, group_thread_list, booked_thread_list = [],[],[],[],[]
#     journal_thread_res, learn_thread_res , live_thread_res, group_thread_res, booked_thread_res = [],[],[],[],[]

#     for i in assign_journey:
#         learner_attend_sessions = 0
#         mentor_attend_sessions = 0
#         booked_slots = mentorCalendar.objects.filter(mentor=i.mentor, slot_status="Booked", participants=i.user, start_time__gte=date.today(), status="Upcoming")
        
#         mentee_dict = {"Group": count,"Role": "Mentor","Name": i.mentor.first_name}
#         mentor_dict = {"Group": count,"Role": "Mentee","Name": i.user.first_name}
#         no_role_dict = {"Group": "","Role": "","Name": ""}

#         journal_thread_list.append(Thread(target=update_journals, args=[i, journey, journals_dict, que]))
#         learn_thread_list.append(Thread(target=update_learnings, args=[i, learn, que]))
#         # live_thread_list.append(Thread(target=update_live_sessions, args=[i, live_session, que]))
#         group_thread_list.append(Thread(target=update_group_sessions, args=[i, group_session, que]))       
#         booked_thread_list.append(Thread(target=update_booked_slots, args=[i, booked_slots, group_session, que]))

#         print("LIVE SESSION START")
#         for meet in range(len(live_session)):
#             learner_attend = journey_meeting_attendi(i.user, live_session[meet])
#             learner_attend_sessions += learner_attend
#             mentee_dict.update({"Live Session " + str(meet+1):  learner_attend, })
#             mentor_attend = journey_meeting_attendi(i.mentor, live_session[meet])
#             mentor_attend_sessions += mentor_attend
#             mentor_dict.update({"Live Session " + str(meet+1):  mentor_attend, })

#         mentee_dict['Live Session'] = math.ceil(learner_attend_sessions/live_session.count()
#                                            if mentor_attend_sessions > 0 else 0)
#         mentor_dict['Live Session'] = math.ceil(mentor_attend_sessions/live_session.count()
#                                            if mentor_attend_sessions > 0 else 0)
#         print("LIVE SESSION END")


#     for t in range(len(journal_thread_list)):
#         journal_thread_list[t].start()
#         learn_thread_list[t].start()
#         # live_thread_list[t].start()
#         group_thread_list[t].start()
#         booked_thread_list[t].start()

#     for s in range(len(journal_thread_list)):
#         learn_thread_list[s].join()
#         learn_thread_res.append(que.get())

#         # live_thread_list[s].join()
#         # live_thread_res.append(que.get())

#         group_thread_list[s].join()
#         group_thread_res.append(que.get())

#         booked_thread_list[s].join()
#         booked_thread_res.append(que.get())

#         journal_thread_list[s].join()
#         journal_thread_res.append(que.get())
    
    
#     journal_mentee_dict = journal_thread_res[-1][0]
#     journal_mentor_dict = journal_thread_res[-1][1]
#     journal_norole_dict = journal_thread_res[-1][2]

#     learn_mentee_dict = learn_thread_res[-1][0]
#     learn_mentor_dict = learn_thread_res[-1][1]

#     # live_mentee_dict = live_thread_res[-1][0]
#     # live_mentor_dict = live_thread_res[-1][1]

#     group_mentee_dict = group_thread_res[-1][0]
#     group_mentor_dict = group_thread_res[-1][1]
    
#     booked_mentee_dict = booked_thread_res[-1][0]
#     booked_mentor_dict = booked_thread_res[-1][1]

#     mentee_dict.update(journal_mentee_dict)
#     mentee_dict.update(learn_mentee_dict)
#     # mentee_dict.update(live_mentee_dict)
#     mentee_dict.update(group_mentee_dict)
#     mentee_dict.update(booked_mentee_dict)

#     mentor_dict.update(journal_mentor_dict)
#     mentor_dict.update(learn_mentor_dict)
#     # mentor_dict.update(live_mentor_dict)
#     mentor_dict.update(group_mentor_dict)
#     mentor_dict.update(booked_mentor_dict)

#     no_role_dict.update(journal_norole_dict)

#     mentee_dict['Overall'] = math.ceil((mentee_dict['Journal'] + mentee_dict['Learn'] + mentee_dict['Calls'] + mentee_dict['Live Session'])/4)
    
#     print(mentee_dict)
#     print(mentor_dict)
#     print(no_role_dict)
    
#     data.append(mentee_dict)
#     data.append(mentor_dict)
#     data.append(no_role_dict)

#     return data

def generate_attendence(user, journey):
    mentoring_journey = MentoringJourney.objects.filter(journey=journey, is_delete=False)
    journals = mentoring_journey.filter(meta_key="journals")
    learn = mentoring_journey.filter(meta_key="quest")
    j = 1

    journals_list = {journal.name: journal.value for journal in journals}

    assign_journey = AssignMentorToUser.objects.filter(journey=journey, is_assign=True)
    data = []
    count = 1

    collabarate = Collabarate.objects.filter(journey=journey.pk, is_cancel=False, start_time__lte=date.today())
    live_session = collabarate.filter(type="LiveStreaming")
    group_session = collabarate.filter(type="GroupStreaming")

    for i in assign_journey:
        learner_meet = 0
        mentor_meet = 0
        learner_attend_calls = 0
        mentor_attend_calls = 0
        learner_attend_sessions = 0
        mentor_attend_sessions = 0
        overall_learn = 0
        overall_mentee_journal = 0
        overall_mentor_journal = 0
        overall_calls = 0
        overall_livestream = 0
        temp_1 = {
            "Group": count,
            "Role": "Mentor",
            "Name": i.mentor.first_name,
            "Overall": "",
            "Learn": "",
            "Journal": "",
            "Calls": "",
            "Live Session": "",
            "Group Session": "",
            "One To One": ""
        }

        temp_2 = {
            "Group": count,
            "Role": "Mentee",
            "Name": i.user.first_name,
            "Overall": "",
            "Learn": "",
            "Journal": "",
            "Calls": "",
            "Live Session": "",
            "Group Session": "",
            "One To One": "",
        }

        temp_3 = {
            "Group": "",
            "Role": "",
            "Name": "",
            "Overall": "",
            "Learn": "",
            "Journal": "",
            "Calls": "",
            "Live Session": "",
            "Group Session": "",
            "One To One": "",
        }

        for j in range(1, 16):
            temp_learning_journal = math.ceil(mentor_check_journal_is_fill(journey,
                                                                           i.user, i.mentor, journals_list, j))
            temp_mentor_journal = math.ceil(check_journal_is_fill(journey, i.user, journals_list, j))
            overall_mentee_journal = temp_learning_journal + overall_mentee_journal
            overall_mentor_journal = temp_mentor_journal + overall_mentor_journal
            temp_1.update({"Journal " + str(j):  temp_learning_journal, })
            temp_2.update({"Journal " + str(j):  temp_mentor_journal, })
            temp_3.update({"Journal " + str(j):  "", })

        for k in range(len(learn)):
            print(learn[k], "11")

            temp_overall_learn = math.ceil(check_user_content_read_status(i.user, learn[k].value))
            overall_learn = temp_overall_learn + overall_learn
            print(overall_learn, "212")
            temp_1.update({"Learn " + str(k+1):  temp_overall_learn, })
            temp_2.update({"Learn " + str(k+1):  "", })
            temp_3.update({"Learn " + str(k+1):  "", })

        temp_1['Journal'] = math.ceil(overall_mentee_journal/15)
        temp_2['Journal'] = math.ceil(overall_mentor_journal/15)
        temp_1['Learn'] = math.ceil(overall_learn/len(learn))

        for meet in range(len(live_session)):
            learner_attend = journey_meeting_attendi(i.user, live_session[meet])
            learner_attend_sessions += learner_attend
            temp_1.update({"Live Session " + str(meet+1):  learner_attend, })
            mentor_attend = journey_meeting_attendi(i.mentor, live_session[meet])
            mentor_attend_sessions += mentor_attend
            
            temp_2.update({"Live Session " + str(meet+1):  mentor_attend, })
        temp_1['Live Session'] = math.ceil(learner_attend_sessions/live_session.count()
                                           if mentor_attend_sessions > 0 else 0)
        temp_2['Live Session'] = math.ceil(mentor_attend_sessions/live_session.count()
                                           if mentor_attend_sessions > 0 else 0)

        for meet in range(len(group_session)):
            learner_attend = journey_meeting_attendi(i.user, group_session[meet])
            learner_attend_calls += learner_attend
            temp_1.update({"Group Session " + str(meet+1):  learner_attend, })
            mentor_attend = journey_meeting_attendi(i.mentor, group_session[meet])
            mentor_attend_calls += mentor_attend

            temp_2.update({"Group Session " + str(meet+1):  mentor_attend, })
        temp_1['Group Session'] = math.ceil(learner_attend_calls/group_session.count()
                                            if learner_attend_calls > 0 else 0)
        temp_2['Group Session'] = math.ceil(mentor_attend_calls/group_session.count()
                                            if mentor_attend_calls > 0 else 0)

        booked_slots = mentorCalendar.objects.filter(
            mentor=i.mentor, slot_status="Booked", participants=i.user, start_time__gte=date.today(), status="Upcoming")
        print("booked_slots ", booked_slots, i.mentor, i.user)
        for slot in range(len(booked_slots)):
            learner_attend = one_to_one_call(booked_slots[slot])
            learner_meet += learner_attend
            temp_1.update({"One To One " + str(slot+1):  learner_attend, })
            mentor_attend = journey_meeting_attendi(i.mentor, group_session[meet])
            mentor_meet += mentor_attend
            temp_2.update({"One To One " + str(slot+1):  mentor_attend, })

        temp_1['One To One'] = math.ceil(learner_meet/booked_slots.count() if learner_meet > 0 else 0)
        temp_2['One To One'] = math.ceil(mentor_meet/booked_slots.count() if mentor_meet > 0 else 0)
        temp_1['Calls'] = 0
        temp_1['Overall'] = math.ceil((temp_1['Journal'] + temp_1['Learn'] +
                                      temp_1['Calls'] + temp_1['Live Session'])/4)
        data.append(temp_1)
        data.append(temp_2)
        data.append(temp_3)

    return data


def populate(request):
    df = pd.read_csv(open('info.csv', 'r'))
    rooms = df['room']
    info = df['info']

    for i in range(len(rooms)):

        res = json.loads(info[i])
        res = res['data']
        try:
            try: 
                collab_obj = Collabarate.objects.get(url_title=rooms[i])
                mentor_cal_obj = None
            except: 
                collab_obj = None
                mentor_cal_obj = mentorCalendar.objects.get(url_title=rooms[i])
        except: pass

        if collab_obj:
            try:
                if not res == []:
                    for r in res:
                        start_time = r['start_time']
                        duration = r['duration']
                        ongoing = r['ongoing']
                        max_participants = len(r['participants'])
                        AllMeetingDetails.objects.create(collaborate_meeting=collab_obj, title=collab_obj.title, start_time=start_time, duration=duration, ongoing=ongoing, max_participants=max_participants)
                        print("created")
            except: pass
        if mentor_cal_obj:
            try:
                if not res == []:
                    for r in res:
                        start_time = r['start_time']
                        duration = r['duration']
                        ongoing = r['ongoing']
                        max_participants = len(r['participants'])
                        AllMeetingDetails.objects.create(mentor_meeting=mentor_cal_obj, title=collab_obj.title, start_time=start_time, duration=duration, ongoing=ongoing, max_participants=max_participants)
                        print("created")
            except: pass

    # for i in range(len(rooms)):
    #     res = json.loads(info[i])
    #     res = res['data']
    #     if not res == []:
    #         for r in res:
    #             duration = r['duration']
    #             for p in r['participants']:
    #                 user_name = p['user_name']
    #                 join_time = p['join_time']
    #                 try:
    #                     meet_obj = AllMeetingDetails.objects.get(title=rooms[i])
    #                     MeetingParticipants.objects.create(join_time=int(join_time), duration=int(duration), user_name=user_name, session=meet_obj)
    #                 except: pass
    return HttpResponse('populated')


class RedirectToDyte(View):
    permission_classes = (AllowAny,)
    def get(self, request, **kwargs):
        if str(request.user) != "AnonymousUser" or ("user" in request.session.keys()):
            meet_id = self.kwargs['meet_id']
            try: email = request.user.email
            except: email = request.session['email']
            print("EMAIL", email)
            
            try:
                print("MEET ID", meet_id)
                token_obj = DyteAuthToken.objects.filter(email__iexact=email, meeting_id=meet_id).first()
                try:bg_image = Collabarate.objects.get(url_title=meet_id).custom_background.url
                except: bg_image = None
                print("**BG IMAGE**", bg_image)
            except Exception as e:
                print("**ERROR IN GETTING DYTE AUTH TOKEN**", e)
                return render(request, '401.html', {'message':'Entry Restricted - You are not a part of this meet.'})
            
            authToken = token_obj.authToken
            participant_id = token_obj.participant_id
            user_name = token_obj.user_name

            url = f"{DYTE_BASE_URL}/meetings/{meet_id}/participants/{participant_id}/token"
            r = requests.post(url, auth=(DYTE_ORG_ID, DYTE_API_KEY))
            if r.status_code == 200:
                authToken = r.json()['data']['token']
                token_obj.authToken = authToken
                token_obj.save()
            else: return render(request, '401.html', {'message':'Entry Restricted - You are not a part of this meet.'})
            
            feedback_url = f'{BASE_URL}/feedback/feedback-form-post/{meet_id}'
            local_url = f'http://127.0.0.1:8000/feedback/feedback-form-post/{meet_id}'

            context = {"authToken": authToken, "meet_id":meet_id, 
                       "participant_id": participant_id, "user_name": user_name, "feedback_url":feedback_url, "bg_image":bg_image}
            response = render(request, "feedback/dyte.html", context)
            return response
        else:
            meet_id = self.kwargs['meet_id']
            return render(request, '401.html', {'message':'Entry Restricted - You are not a part of this meet.'})
        
class RedirectToGuestUser(View):
    permission_classes = (AllowAny,)
    def get(self, request, **kwargs):
        meet_id = self.kwargs['meet_id']
        print("MEETID", meet_id)
        return render(request, 'auth/guest_user.html', context={"meet_id":meet_id})
            
def get_guest_user(request):
    if request.method == "POST":
        print("REQUEST POST", request.POST)
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        meet_id = request.POST.get('meet_id')

        phone_obj = User.objects.filter(phone=mobile).exists()
        email_obj = User.objects.filter(email=email).exists()
        if phone_obj:
            context={"message":"User exist with the given phone number. Login to conitnue with phone.", "class":" alert-danger error alert-dismissible"}
            return render(request, "auth/guest_user.html", context)
        if email_obj:
            context={"message":"User exist with the given email. Login to conitnue with email.", "class":" alert-danger error alert-dismissible"}
            return render(request, "auth/guest_user.html", context)

        obj = User.objects.create(email=email, first_name=fname, last_name=lname, phone=mobile, is_guest=True, username=email)


        name = obj.get_full_name()

        payload = json.dumps({
                "name": name,
                "custom_participant_id":email,
                "preset_name": "group_call_participant"
            })
        url = f"{DYTE_BASE_URL}/meetings/{meet_id}/participants"
        response = requests.request("POST", url, data=payload, auth=(DYTE_ORG_ID, DYTE_API_KEY), headers={"Content-Type":
                                                                                                               "application/json"})
        # print("RESPONSE CODE", response.status_code)
        if not response.status_code == 201:
            context={"message":"There was some issue with the meet. Please contact admin to join meet.", "class":" alert-danger error alert-dismissible"}
            return render(request, "auth/guest_user.html", context)
        data = response.json()
        # print("DATA", data)
        DyteAuthToken.objects.create(user_name=name, email=email, authToken=data['data']['token'],
                                        preset="group_call_participant", preset_id=data['data']['preset_id'], 
                                        meeting_id=meet_id, participant_id=data['data']['id'])
        # print("participant details saved")

        request.session['user'] = name
        request.session['email'] = email

        return redirect(f'/config/dyte/{meet_id}')
