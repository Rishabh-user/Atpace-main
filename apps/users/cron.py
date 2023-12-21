from datetime import datetime, timedelta, date, timezone
from time import time
from apps.content.models import MentoringJourney, UserChannel, UserCourseStart
from apps.leaderboard.views import send_push_notification
from apps.mentor.models import AssignMentorToUser, mentorCalendar
from apps.mentor.utils import check_user_slots
from apps.content.utils import learn_journal, weekly_quest_learn, user_calls, user_posts, mentor_calls, mentor_journal, mentor_quest
from apps.program_manager_panel.models import MessageScheduler, TaskRemainder, ProgramManagerTask
from apps.vonage_api.utils import lets_start_work_checkjourney, lets_start_work_journal, book_a_call_one_mentor, reminder_to_journnal_scheduler, program_team_weekly_scheduler
from apps.api.utils import meeting_notification
from apps.leaderboard.models import UserStreakCount, UserStreak, UserDrivenGoal
from .models import Learner, User, Collabarate, Mentor
from apps.kpi.Models.Learner import NoActivityMenteeData, NoActivityMentorData, NoActivityPairData
from apps.users.helper import journey_users, company_users, journal_percentage, microskill_percentage, no_acivity_pairs, company_journey
from apps.users.utils import send_reminder
from apps.atpace_community.models import Event
from apps.users.models import ProfileAssestQuestion, UserProfileAssest
from django.db.models.query_utils import Q
from apps.chat_app.models import Chat
from apps.push_notification.models import MeetRSVPData

def every_ten_days():
    all_users = User.objects.filter(is_active=True, is_delete=False, is_archive=False)

    #remind inactive users
    last_40_days = datetime.now() - timedelta(days=40)
    last_10_days = datetime.now() - timedelta(days=10)

    noti_user = all_users.filter(Q(last_login__lte=last_40_days) & Q(last_login__gte=last_10_days))
    for user in noti_user:
        description = f"""Hi {user.first_name} {user.last_name}!

        It's been awhile since we saw you on Mentor Circle! Come check out the latest content added on to the app!

        Check out content and engage with your fellow communities!"""

        context = {
            "screen": "Login",
        }
        send_push_notification(user, 'No login for last few days ', description, context)
    
    noti_user = all_users.filter(last_login__gte=last_40_days)
    for user in noti_user:

        if (user.is_active == True):
            user.is_active = False
            user.save()

    #remind set goals and signup jouney if user has not done yet
    learners  = all_users.filter(userType__in='Learner')
    for learner in learners:
        if not UserDrivenGoal.objects.filter(created_by=learner, is_active=True, is_deleted=False).exists():
            description = f"""Hi {learner.first_name} {learner.last_name}!
            Looks like you haven't set your goals yet for your learning journey. Come set your goals and let's find you the courses to unlock the new you!"""

            context = {
                "screen": "Goals",
            }
            send_push_notification(learner, 'Goal Setting Reminder', description, context)


        if not UserChannel.objects.filter(user=learner, status='Joined', is_alloted=True, is_removed=False).exists():
            description = f"""Hi {learner.first_name} {learner.last_name}!
It looks    like you haven't signed up for any courses yet, let's get you on your way to a new you by signing up for some courses!"""

            context = {
                "screen": "Program",
            }
            send_push_notification(learner, 'Journey Signup Reminder', description, context)
    
    # Reminder to keep making progress on course work

    remind_make_progress()

    return True

def to_lerner_message_scheduler():
    users = User.objects.filter(userType__type="Learner")
    last_7_date = datetime.today() - timedelta(days=7)
    for user in users:
        companys = user.company.all()
        for company in companys:
            journey_list, no_content, all_content = weekly_quest_learn(user, last_7_date, company)
            learnig_journals_list, all_journal = learn_journal(user, last_7_date, company)
            if len(learnig_journals_list)>0:
                journal = learnig_journals_list[0]
                lets_start_work_journal(user)

            if len(journey_list)>0:
                journey = journey_list[0]
                lets_start_work_checkjourney(user)
                    
def to_lerner_slot_scheduler():
    users = User.objects.filter(userType__type="Learner")
    for user in users:
        check_calls = check_user_slots(user)
        if len(check_calls)>0:
            calls = check_calls[0]
            book_a_call_one_mentor(user, calls['mentor_name'], calls['slot_time'])

def message_scheduler():
    today = date.today()
    msg_scheduler = MessageScheduler.objects.filter(time=datetime.now().strftime("%H:%M"), day=today.strftime(
        "%A"), start_date__lte=today, end_date__gte=today,  is_active=True, is_delete=False)
    for scheduler in msg_scheduler:
        receivers = ""
        if scheduler.journey:
            receivers = journey_users(scheduler.journey, scheduler.receiver)
        else:
            receivers = company_users(scheduler.company, scheduler.receiver)
        if scheduler.scheduler_type == "Program_Team_Weekly":
            journeys = []
            if not scheduler.journey:
                journeys = company_journey(scheduler.company)
            else:
                journeys.append(scheduler.journey)

        for receiver in receivers:
            if scheduler.receiver_platform == 'WhatsApp' and (receiver.phone and receiver.is_whatsapp_enable):
                if scheduler.scheduler_type == "Reminder_to_Journal":
                    reminder_to_journnal_scheduler(receiver, scheduler.journal.id)
                if scheduler.scheduler_type == "Program_Team_Weekly":
                    for journey in journeys:
                        microskill_perc = microskill_percentage(journey)
                        journal_perc = journal_percentage(journey)
                        no_acivity = no_acivity_pairs(journey)
                        if journey.whatsapp_notification_required:
                            program_team_weekly_scheduler(receiver, date.today().strftime("%d %b, %Y"), journey.title,
                                                      microskill_perc, journal_perc, no_acivity)

    return True

def users_risk_data_update():
    users = User.objects.filter(userType__type="Learner")
    last_14_date = datetime.now() - timedelta(days=14)
    for user in users:
        companys = user.company.all()
        for company in companys:
            no_journal, all_journal = learn_journal(user, last_14_date, company)
            journey_list, no_quest, all_quest = weekly_quest_learn(user, last_14_date, company)
            complete, no_call, total_calls = user_calls(user, last_14_date, company)
            all_post = user_posts(user, last_14_date, company)
            if not NoActivityMenteeData.objects.filter(user=user, company=company).exists():
                NoActivityMenteeData.objects.create(user=user, company=company, user_name=user.get_full_name(), 
                                                no_calls=no_call, total_calls=total_calls,
                                                no_quest=no_quest, total_quest=all_quest,
                                                no_journals=len(no_journal), total_journals=all_journal, all_post=all_post)
            else:
                NoActivityMenteeData.objects.filter(user=user, company=company).update(no_calls=no_call, total_calls=total_calls,
                                                no_quest=no_quest, total_quest=all_quest, no_journals=len(no_journal),
                                                total_journals=all_journal, all_post=all_post)
    return True

def mentors_risk_data_update():
    users = User.objects.filter(userType__type="Mentor")
    last_14_date = datetime.now() - timedelta(days=14)
    for user in users:
        companys = user.company.all()
        for company in companys:
            no_journal, all_journal = mentor_journal(user, company, last_14_date)
            journey_list, no_quest, all_quest = mentor_quest(user, company, last_14_date)
            complete, no_call, total_calls = mentor_calls(user, company, last_14_date)
            all_post = user_posts(user, last_14_date, company)
            if not NoActivityMentorData.objects.filter(user=user, company=company).exists():
                NoActivityMentorData.objects.create(user=user, company=company, user_name=user.get_full_name(), 
                                                no_calls=no_call, total_calls=total_calls,
                                                no_quest=no_quest, total_quest=all_quest,
                                                no_journals=len(no_journal), total_journals=all_journal, all_post=all_post)
            else:
                NoActivityMentorData.objects.filter(user=user, company=company).update(no_calls=no_call, total_calls=total_calls,
                                            no_quest=no_quest, total_quest=all_quest, no_journals=len(no_journal),
                                            total_journals=all_journal, all_post=all_post)
    return True

def pair_risk_data_update():
    last_14_date = datetime.now() - timedelta(days=14)
    assign_users= AssignMentorToUser.objects.all()
    for assign in assign_users:
        mentee = NoActivityMenteeData.objects.filter(user=assign.user, company=assign.journey.company, no_calls__gte=0, no_quest__gte=0, no_journals__gte=0, all_post__lte=1, updated_at__gte=last_14_date).first()
        mentor = NoActivityMentorData.objects.filter(user=assign.mentor, company=assign.journey.company, no_calls__gte=0, no_quest__gte=0, no_journals__gte=0, all_post__lte=1, updated_at__gte=last_14_date).first()        
        if mentee:
            if not NoActivityPairData.objects.filter(company=assign.journey.company, pair=assign).exists():
                NoActivityPairData.objects.create(company=assign.journey.company, pair=assign, learner=mentee, mentor=mentor)
            else:
                NoActivityPairData.objects.filter(company=assign.journey.company, pair=assign).update(mentor=mentor, learner=mentee)
        elif mentor:
            if not NoActivityPairData.objects.filter(company=assign.journey.company, pair=assign).exists():
                NoActivityPairData.objects.create(company=assign.journey.company, pair=assign, mentor=mentor, learner=mentee)
            else:
                NoActivityPairData.objects.filter(company=assign.journey.company, pair=assign).update(mentor=mentor, learner=mentee)
    return True

def risk_data_update():
    users_risk_data_update()
    mentors_risk_data_update()
    pair_risk_data_update()
    return True


def task_reminder():
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    all_task = ProgramManagerTask.objects.filter(is_active=True, is_delete=False, set_remainder=True, due_time__gt=current_time)

    for task in all_task:
        task_reminder = TaskRemainder.objects.get(task=task)
        reminder_time = (task.due_time - timedelta(minutes=task_reminder.remainder_before)).strftime('%Y-%m-%d %H:%M')
        
        if reminder_time == current_time:
            send_reminder(task)

    return True

def rsvp_reminder():
    upcoming_6_hours = datetime.now() + timedelta(hours=6)
    upcoming_24_hours = datetime.now() + timedelta(hours=24)
    collabarate = Collabarate.objects.filter(Q(start_time=upcoming_6_hours) | Q(start_time=upcoming_24_hours), is_active=True, is_cancel=False)
    for col in collabarate:
        if not MeetRSVPData.objects.filter(user=col.speaker, meet_id=col.id).exists():
            if col.type == "LiveStreaming":
                call_type = "Livestram" 
            else:
                call_type = "Group Call"

            description = f"""Hi {col.speaker.first_name} {col.speaker.last_name}!
            You haven't RSVP yet for {call_type}:
            {collabarate.title} {collabarate.start_time}
            Can you make it to the {call_type}?"""

            context = {
                "screen": "Collabarate",
            }
            send_push_notification(col.speaker, 'Reminder for RSVP', description, context)

        for par in col.participants.all():
            if not MeetRSVPData.objects.filter(user=par, meet_id=col.id).exists():
                description = f"""Hi {par.first_name} {par.last_name}!
                You haven't RSVP yet for {call_type}:
                {collabarate.title} {collabarate.start_time}
                Can you make it to the {call_type}?"""

                context = {
                    "screen": "Collabarate",
                }
                send_push_notification(par, 'Reminder for RSVP', description, context)

    event = Event.objects.filter(Q(start_time=upcoming_6_hours) | Q(start_time=upcoming_24_hours), location='URL (Zoom, YouTube Live)', post_id__is_active=True, post_id__is_delete=False)
    if not MeetRSVPData.objects.filter(user=event.host, meet_id=event.id).exists():

        description = f"""Hi {event.host.first_name} {event.host.last_name}!
        You haven't RSVP yet for Event:
        {event.post.title} {event.start_time}
        Can you make it to the Event?"""

        context = {
            "screen": "Community",
        }
        send_push_notification(event.host, 'Reminder for RSVP', description, context)

    for par in event.participants.all():
        if not MeetRSVPData.objects.filter(user=par, meet_id=event.id).exists():
            description = f"""Hi {par.first_name} {par.last_name}!
            You haven't RSVP yet for Event:
            {event.post.title} {event.start_time}
            Can you make it to the Event?"""

            context = {
                "screen": "Community",
            }
            send_push_notification(par, 'Reminder for RSVP', description, context)

    return True

def message_scheduler_and_task_reminder_and_rsvp_reminder():
    task_reminder()
    message_scheduler()
    rsvp_reminder
    return True

def journey_new_content():
    last_7_date = datetime.now() - timedelta(days=7)
    new_content = MentoringJourney.objects.filter(is_checked=True, is_delete=False, journey__is_active=True, journey__is_delete=False, created_at__gt=last_7_date)
    journey_list = []
    for content in new_content:
        if content.journey not in journey_list:
            journey_list.append(content.journey)
    
    for journey in journey_list:
        users = UserChannel.objects.filter(Channel=journey, status='Joined', is_alloted=True, is_removed=False)
        for user in users:
            description = f"""Hi {user.first_name} {user.last_name}!
            There is new content in {journey.title} this week! Spend some time viewing what's happening this week."""

            context = {
                "screen": "Journey",
            }
            send_push_notification(user, 'Journey new content', description, context)

    return True

def collabarate_notification():
    now_dt = datetime.fromisoformat(str(datetime.now()))
    now_unix_timestamp = now_dt.replace(tzinfo=timezone.utc).timestamp()

    collabarates = Collabarate.objects.all()

    for collab in collabarates:
        start_dt = datetime.fromisoformat(str(collab.start_time))
        start_dt_unix = start_dt.replace(tzinfo=timezone.utc).timestamp()
        print("Time difference", int(start_dt_unix) - int(now_unix_timestamp))
        if (int(start_dt_unix) - int(now_unix_timestamp)) < 300 and (int(start_dt_unix) - int(now_unix_timestamp)) > 0:
            if collab.type == "LiveStreaming":
                host = collab.speaker
                meeting_notification(host, collab.title, f"Hello {host.get_full_name()}, {collab.title} livestream is starting at {collab.start_time}.")
                participants = collab.participants.all()
                for parti in participants:
                    meeting_notification(parti, collab.title ,f"Hello {parti.get_full_name()}, {collab.title} livestream is starting at {collab.start_time}.")   
            else: 
                host = collab.speaker
                meeting_notification(host, collab.title, f"Hello {host.get_full_name()}, {collab.title} group call is starting at {collab.start_time}.")
                participants = collab.participants.all()
                for parti in participants:
                    meeting_notification(parti, collab.title ,f"Hello {parti.get_full_name()}, {collab.title} group call is starting at {collab.start_time}.")
    return True

def event_notification():
    now_dt = datetime.fromisoformat(str(datetime.now()))
    now_unix_timestamp = now_dt.replace(tzinfo=timezone.utc).timestamp()

    events = Event.objects.filter(location='URL (Zoom, YouTube Live)', post_id__is_active=True, post_id__is_delete=False)

    for event in events:
        start_dt = datetime.fromisoformat(str(event.start_time))
        start_dt_unix = start_dt.replace(tzinfo=timezone.utc).timestamp()
        print("Time difference", int(start_dt_unix) - int(now_unix_timestamp))

        if (int(start_dt_unix) - int(now_unix_timestamp)) < 300 and (int(start_dt_unix) - int(now_unix_timestamp)) > 0:
            host = event.host
            meeting_notification(host, event.post_id, f"Hello {host.get_full_name()}, {event.post_id} event is starting at {event.start_time}.")
            participants = event.attendees.all()
            for parti in participants:
                meeting_notification(parti, event.post_id ,f"Hello {parti.get_full_name()}, {event.post_id} event is starting at {event.start_time}.")   
    return True
def collabarate_event_notification():
    collabarate_notification()
    event_notification()
    return True

def collabrate_rsvp():
    now_dt = datetime.fromisoformat(str(datetime.now()))
    now_unix_timestamp = now_dt.replace(tzinfo=timezone.utc).timestamp()

    collabarates = Collabarate.objects.all()

    for collab in collabarates:
        start_dt = datetime.fromisoformat(str(collab.start_time))
        start_dt_unix = start_dt.replace(tzinfo=timezone.utc).timestamp()
        print("Time difference", int(start_dt_unix) - int(now_unix_timestamp))
        if int(start_dt_unix) > int(now_unix_timestamp):
            if collab.type == "LiveStreaming":
                participants = collab.participants.all()
                for parti in participants:
                    meeting_notification(parti, collab.title ,f"HHello {parti.get_full_name()}, You haven't RSVP for {collab.title} livestream starting at {collab.start_time}. Can you make it ?")   
            else:
                participants = collab.participants.all()
                for parti in participants:
                    meeting_notification(parti, collab.title ,f"Hello {parti.get_full_name()}, You haven't RSVP for {collab.title} livestream starting at {collab.start_time}. Can you make it ?")           
    return True

def event_rsvp():
    now_dt = datetime.fromisoformat(str(datetime.now()))
    now_unix_timestamp = now_dt.replace(tzinfo=timezone.utc).timestamp()

    events = Event.objects.all()

    for event in events:
        start_dt = datetime.fromisoformat(str(event.start_time))
        start_dt_unix = start_dt.replace(tzinfo=timezone.utc).timestamp()
        print("Time difference", int(start_dt_unix) - int(now_unix_timestamp))

        if int(start_dt_unix) > int(now_unix_timestamp):
            participants = event.attendees.all()
            for parti in participants:
                meeting_notification(parti, event.post_id ,f"Hello {parti.get_full_name()}, you haven't RSVP for {event.post_id} event starting at {event.start_time}. Can you make it?")
    return True

def event_collabrate_rsvp():
    collabrate_rsvp()
    event_rsvp()
    return True

def incomplete_profile_assessment():
    profile_questions = ProfileAssestQuestion.objects.filter(is_active=True, is_delete=False)
    users = User.objects.filter(is_archive=False, is_active=True, is_delete=False)

    #For Learners
    learner_profile_questions = profile_questions.filter(question_for='Learner').count()
    learners = users.filter(userType__type='Learner')
    for learner in learners:
        user_profile_assest = UserProfileAssest.objects.filter(user=learner, question_for='Learner').count()
        if learner_profile_questions > user_profile_assest:
            description = f"""Hi {learner.first_name} {learner.last_name}!
            You still have some incomplete items in your profile assessment."""

            context = {
                "screen": "Profile Assessment",
            }
            send_push_notification(mentor, 'Incomplete profil assessment', description, context)


    #For Mentors
    mentor_profile_questions = profile_questions.filter(question_for='Mentor').count()
    mentors = users.filter(userType__type='Mentor')
    for mentor in mentors:
        user_profile_assest = UserProfileAssest.objects.filter(user=mentor, question_for='Mentor').count()
        if mentor_profile_questions > user_profile_assest:
            description = f"""Hi {mentor.first_name} {mentor.last_name}!
            You still have some incomplete items in your profile assessment. """

            context = {
                "screen": "Profile Assessment",
            }
            send_push_notification(mentor, 'Incomplete profil assessment', description, context)

    return True

def journey_new_content():
    last_10_minute = datetime.now() - timedelta(minutes=10)
    mentor_call = mentorCalendar.objects.filter(Q(start_time__gt=last_10_minute) | Q(start_time__lt=datetime.now()), is_cancel=False, slot_status='Booked')

    for call in mentor_call:
        mentee = call.participants.first()
        description = f"""Hi {call.mentor.first_name} {call.mentor.last_name}!
        Your call with {mentee.first_name} {mentee.last_name} is about to start!"""

        context = {
            "screen": "Mentor Call",
        }
        send_push_notification(call.mentor, 'Mentor Call Reminder', description, context)

        description = f"""Hi {mentee.first_name} {mentee.last_name}!
        Your call with {call.mentor.first_name} {call.mentor.last_name} is about to start!"""

        context = {
            "screen": "Mentor Call",
        }
        send_push_notification(mentee, 'Mentor Call Reminder', description, context)

    return True



def seven_day_inacticity_notification():
    for i in range(7,35,3):
        date = datetime.now() + timedelta(-i)
        users = User.objects.filter(last_login__lte=date)
        context = {
            "screen": "Login"
        }
        for user in users:
            description = f"Hey {user.get_full_name()}, We miss you! It's been a while since you invested in yourself! Come spend some time to unlock a new you!"
            send_push_notification(user, "Reminder for inactivity", description, context)
            
def twenty_days_inacticity_notification():
    date = datetime.now() + timedelta(-20)
    users = User.objects.filter(last_login__lte=date)
    context = {
        "screen": "Login"
    }
    for user in users:
        description = f"""Hi {user.get_full_name()},
        We've missed you at AtPace Academy! There's a world of knowledge waiting for you to explore. We've recently added exciting new courses on various subjects to keep your learning journey going strong.

        📚 Discover new skills and expand your horizons
        🎓 Dive into our comprehensive course library
        🏆 Earn achievements and track your progress

        Don't let your learning journey come to a halt! Open app now and continue your pursuit of knowledge.

        Happy learning!
        The AtPace Team"""
        send_push_notification(user, "Reminder for inactivity", description, context)

def user_streak_notification():
    users = User.objects.all()
    for user in users:
        try: streak_count = UserStreakCount.objects.filter(user=user).first().streak_count
        except: streak_count = None

        title = "Streak Reminder"
        description = f"You're doing a great job with you {streak_count} day streak! Don't forget to log in to keep your streak up!"
        five_day_desc = f"Wow 5 day streak is Amazing! Don't forget to log in to keep your streak up!"
        none_desc = f"You have not joined the streak game yet! Don't forget to log in to keep your streak up!"
        context = {"screen":"Login"}

        if (not streak_count == None) and streak_count > 5: send_push_notification(user, title, five_day_desc, context)
        elif (not streak_count == None) and streak_count < 5: send_push_notification(user, title, description, context)
        else: send_push_notification(user, title, none_desc, context)


def meeting_reminder():
    upcoming_10_minute = datetime.now() + timedelta(minutes=10)
    collabarates = Collabarate.objects.filter(Q(start_time__lt=upcoming_10_minute) | Q(start_time__gt=datetime.now()), is_active=True, is_cancel=False)
    events = Event.objects.filter(Q(start_time__lt=upcoming_10_minute) | Q(start_time__gt=datetime.now()), post_id__is_active=True, post_id__is_delete=False)
    mentor_call = mentorCalendar.objects.filter(Q(start_time__lt=upcoming_10_minute) | Q(start_time__gt=datetime.now()), is_cancel=False, slot_status='Booked')
    for collabarate in collabarates:
        description = f"""Hi {collabarate.speaker.first_name} {collabarate.speaker.last_name}!
        {collabarate.title} is starting at {collabarate.start_time}!"""

        context = {
            "screen": "Collabarate",
        }
        send_push_notification(collabarate.speaker, 'Collabarate Reminder', description, context)

        for parti in collabarate.participants.all():
            description = f"""Hi {parti.first_name} {parti.last_name}!
            {collabarate.title} is starting at {collabarate.start_time}!"""

            context = {
                "screen": "Collabarate",
            }
            send_push_notification(parti, 'Collabarate Reminder', description, context)


    for event in events:
            description = f"""Hi {event.host.first_name} {event.host.last_name}!
            {event.post.title} is starting at {event.start_time}!"""

            context = {
                "screen": "Event",
            }
            send_push_notification(event.host, 'Event Reminder', description, context)

            for parti in event.attendees.all():
                description = f"""Hi {parti.first_name} {parti.last_name}!
                {event.title} is starting at {event.start_time}!"""

                context = {
                    "screen": "Event",
                }
                send_push_notification(parti, 'Event Reminder', description, context)

    for call in mentor_call:
            description = f"""Hi {call.mentor.first_name} {call.mentor.last_name}!
            {call.title} is starting at {call.start_time}!"""

            context = {
                "screen": "Mentor Call",
            }
            send_push_notification(call.mentor, 'Mentor Call Reminder', description, context)

            for parti in call.participants.all():
                description = f"""Hi {parti.first_name} {parti.last_name}!
                {call.title} is starting at {call.start_time}!"""

                context = {
                    "screen": "Mentor Call",
                }
                send_push_notification(parti, 'Mentor Call Reminder', description, context)

    return True


def unread_chat_and_open_slot():
    last_10_days = datetime.now() - timedelta(days=10)
    last_4_days = datetime.now() - timedelta(days=4)
    #Send notification to user has unread messages
    all_user = User.objects.filter(is_active=True, is_delete=False, is_archive=False)
    for user in all_user:
        if Chat.objects.filter(to_user=user, is_read=False, timestamp__lt=last_10_days).exists():
            description = f"""Hi {user.first_name} {user.last_name}!
            You have some unread messages still. Come check them out by tapping on the notification"""

            context = {
                "screen": "Chat",
            }
            send_push_notification(user, 'Messages waiting for review', description, context)

    #Send notification if mentor hann't opened slot this week
    all_mentor = Mentor.objects.filter(is_active=True, is_delete=False, is_archive=False)
    for mentor in all_mentor:
        if not mentorCalendar.objects.filter(Q(start_time__gte=last_4_days) & Q(start_time__lte=datetime.now()), mentor=mentor, is_cancel=False).exists():
            description = f"""Hi {mentor.first_name} {mentor.last_name}!

            You haven't opened time slots this week on your calendar!

            Go open time slots for your Mentee now!"""

            context = {
                "screen": "Calendar",
            }
            send_push_notification(mentor, 'Reminder to open calendar slots', description, context)

    return True

def monday_jobs():
    learners = Learner.objects.filter(is_active=True, is_delete=False, is_archive=False)
    for learner in learners:
        description = f"""Hi {learner.first_name} {learner.last_name}!
        It's a new week and another week of growing to do! Let's check out what's needs to be done this week!"""

        context = {
            "screen": "Login",
        }
        send_push_notification(learner, 'Reminder to start on week work and tasks', description, context)

        description = f"""It's a brand new day and a brand new opporunity to learn something new! Don't forget to make time for your growth!"""

        context = {
            "screen": "Login",
        }
        send_push_notification(learner, 'Reminder to keep making progress on course work', description, context)
        

        to_lerner_slot_scheduler()


    return True


def remind_make_progress():
    last_10_days = datetime.now() - timedelta(days=7)
    learners = Learner.objects.filter(is_active=True, is_delete=False, is_archive=False)
    for learner in learners:
        journeys = UserChannel.objects.filter(user=learner, status='Joined', is_alloted=True, is_removed=False)
        for journey in journeys:
            if not UserCourseStart.objects.filter(user=learner, channel=journey, created_at__gte=last_10_days).exists():
                description = f"""It's been a while since you made progress on {journey.title}, let's get back on track!"""

                context = {
                    "screen": "Journey",
                }
                send_push_notification(learner, 'Reminder to keep making progress on course work', description, context)

    return True


def every_friday():
    unread_chat_and_open_slot()
    to_lerner_message_scheduler()

