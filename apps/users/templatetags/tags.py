import requests
from apps.community.models import LearningJournals, WeeklyjournalsTemplate
from apps.feedback.models import FeedbackTemplate
from apps.leaderboard.models import UserDrivenGoal
from apps.survey_questions.models import Survey
from django import template

from apps.users.models import User, UserProfileAssest, UserRoles, UserTypes, Company, Coupon, Learner
from apps.content.models import Channel, SkillConfig, UserChannel, Content, MentoringJourney, PublicProgramAnnouncement
from apps.test_series.models import TestSeries
import datetime
import re
from django.db.models import Q
import string
import random
from apps.chat_app.models import Room as AllRooms
from apps.mentor.models import Pool, PoolMentor, AssignMentorToUser
import pytz


try:
    from django.urls import reverse, NoReverseMatch
except ImportError:
    from django.core.urlresolvers import reverse, NoReverseMatch
    from django.core.urlresolvers import reverse, NoReverseMatch
register = template.Library()


@register.filter(name='has_userType')
def has_userType(user, userType):
    user_type = UserTypes.objects.get(type=userType)
    return True if user_type in user.userType.all() else False


def video_id(url):
    from urllib.parse import urlparse, parse_qs

    if url.startswith(('youtu', 'www')):
        url = 'http://' + url

    query = urlparse(url)

    if 'youtube' in query.hostname:
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return query.path.split('/')[2]
    elif 'youtu.be' in query.hostname:
        return query.path[1:]
    else:
        return False


@register.filter(name='check_url_type')
def check_url_type(url):
    type = "youtube"
    return type

@register.filter(name='convert_in_timezone')
def convert_in_timezone(utc_time, timezone):
    print("in filetrdsd", utc_time, timezone)

    # Set the timezone you want to convert to
    tz = pytz.timezone(timezone)

    # Convert UTC time to the local timezone
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(tz)
    print("local time", local_time.strftime("%d-%m-%y %H:%M:%S %p"))

    return local_time.strftime("%d-%m-%y %H:%M:%S %p")

def player_vimeo(value):
    if "vimeo" in value:
        id = value.split('/')[-1]
        print("id ", id)
        return id
    return False


@register.filter(name='youtube_embed_url')
# converts youtube URL into embed HTML
# value is url
def youtube_embed_url(value):
    url_string = video_id(value) if value else ""

    if url_string:
        embed_url = 'https://www.youtube.com/embed/%s' % (url_string)
        res = "<iframe class='content_card'  width=\"700\" height=\"350\" src=\"%s\" frameborder=\"0\" allowfullscreen></iframe>" % (
            embed_url)
        return res

    id = player_vimeo(value)
    return f'<iframe title="vimeo-player" src="https://player.vimeo.com/video/688209060?h={id}" width=\"700\" height=\"350\" frameborder="0" allowfullscreen></iframe>'


youtube_embed_url.is_safe = True


@register.filter(name='user_channel')
def user_channel(userId, company_id=None):
    user = User.objects.get(id=userId)
    if company_id:
        company = user.company.filter(pk=company_id)
    else:
        company = user.company.all()

    if company:
        journey = Channel.objects.filter(Q(is_global=True) | Q(company__in=company),
                                        parent_id=None, is_active=True, is_delete=False)
        channel = UserChannel.objects.filter(status="Joined", user=user, Channel__in=journey)
    else:
        channel = UserChannel.objects.filter(status="Joined", user=user)
    joined_channel = []
    for channel in channel:
        print(f"created_at : {channel.created_at}, name : {channel.Channel.title}")
        if channel.Channel.is_active == True and channel.Channel.is_delete == False:
            joined_channel.append(channel)
    return joined_channel


@register.filter(name='coupon_code')
def coupon_code(userId):
    user = User.objects.get(id=userId)
    print(type(user.coupon_code), "coupen_code")
    print(user.coupon_code, "coupen_code")
    CouponCode = user.coupon_code
    return CouponCode


@register.filter(name='mentor_channel')
def mentor_channel(mentor, company_id=None):
    print("company_id", company_id)
    if company_id:
        company = mentor.company.filter(pk=company_id)
    else:
        company = mentor.company.all()
    
    print("compmau", company)

    journey = Channel.objects.filter(Q(is_global=True) | Q(company__in=company),
                                      parent_id=None, is_active=True, is_delete=False)
    print("123", journey)
    joined_channel = []
    pool_mentor = PoolMentor.objects.filter(
        mentor=mentor, pool__journey__is_active=True, pool__journey__is_delete=False, pool__journey__in=journey)
    print(pool_mentor.count(), "54")
    if pool_mentor.count() > 0:
        for pools in pool_mentor:
            channel = pools.pool.journey
            if channel.is_active is True and channel.is_delete is False:
                if channel not in joined_channel:
                    joined_channel.append(channel)
    else:
        journeys = UserChannel.objects.filter(user=mentor, is_completed=False, status='Joined', is_removed=False, Channel__in=journey)
        print("journeys", journeys)
        for journey in journeys:
            joined_channel.append(journey.Channel)
    return joined_channel


@register.filter(name='all_mentoring_channel')
def all_mentoring_channel(user_type, company_id=None):
    channel = Channel.objects.filter(channel_type="MentoringJourney", parent_id=None, is_delete=False, is_active=True, closure_date__gt=datetime.datetime.now())
    if user_type != 'Admin' and company_id:
        channel = channel.filter(company__id__in=[company_id])
    return channel

@register.filter(name='all_mentoring_selfpaced_channel')
def all_mentoring_selfpaced_channel(user_type, company_id=None):
    channel = Channel.objects.filter(Q(channel_type="MentoringJourney") | Q(channel_type="SelfPaced"), parent_id=None, is_delete=False, is_active=True, closure_date__gt=datetime.datetime.now())
    if user_type != 'Admin' and company_id:
        channel = channel.filter(company__id__in=[company_id])
    return channel


@register.filter(name='all_channel')
def all_channel(user):
    channel = Channel.objects.filter(parent_id=None, is_delete=False, is_active=True)
    return channel


@register.filter(name='all_pools')
def all_pools(user):
    pools = Pool.objects.filter(is_active=True)
    return pools


@register.filter(name='all_skill_channel')
def all_skill_channel(user_type, company_id=None):
    print("user", user_type, company_id)
    if user_type != 'Admin' and company_id:
        channel = Channel.objects.filter(channel_type="SkillDevelopment", parent_id=None, is_delete=False, is_active=True, company__id__in=[company_id], closure_date__gt=datetime.datetime.now())
    else:
        channel = Channel.objects.filter(channel_type="SkillDevelopment", parent_id=None, is_delete=False, is_active=True, closure_date__gt=datetime.datetime.now())
    return channel


@register.filter(name='sub_channel')
def sub_channel(channel):
    channel = Channel.objects.filter(parent_id=channel, is_delete=False, is_active=True)
    return channel


@register.filter(name='journey_by_id')
def journey_by_id(journe_id):
    channel = Channel.objects.get(pk=journe_id)
    return channel


@register.filter(name='is_user_joind')
def is_user_joind(userId, channel):
    user = User.objects.get(id=userId)
    channel = UserChannel.objects.filter(user=user, Channel=channel)
    if channel.exists():
        return channel[0].status
    return "Enroll"


@register.filter(name='get_user_channel')
def get_user_channel(user):
    if user.is_superuser:
        return Channel.objects.filter(is_delete=False, is_active=True)
    return Channel.objects.filter(company__in=user.company.all(), is_delete=False, is_active=True)


@register.filter(name='get_user_channel_skill')
def get_user_channel_skill(user):
    return Channel.objects.filter(channel_type="SkillDevelopment", is_active=True, is_delete=False)


@register.filter(name='all_assessment')
def all_assessment(user):
    return TestSeries.objects.filter(is_delete=False, is_active=True)


@register.filter(name='all_survey')
def all_survey(user):
    survey = Survey.objects.filter(is_delete=False)
    # if user.session['user_type'] == "ProgramManager":
    #     user = user.user
    #     all_journey = Channel.objects.filter(parent_id=None, is_delete=False,
    #                                          is_active=True, company__in=user.company.all())
    #     all_surveys = MentoringJourney.objects.filter(journey__in=all_journey, meta_key="survey",
    #                                                   is_delete=False).values("value")
    #     survey_id_list = [i['value'] for i in all_surveys]
    #     survey = survey.filter(pk__in=survey_id_list)

    return survey


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    try:
        pattern = '^' + reverse(pattern_or_urlname)
    except NoReverseMatch:
        pattern = pattern_or_urlname
    path = context['request'].path
    if re.search(pattern, path):
        return 'active'
    return ''


@register.filter(name="channel_pending_request")
def channel_pending_request(user, userType):
    pending_request = UserChannel.objects.filter(status="Pending").count()

    return pending_request


@register.filter(name="joinned_request")
def joinned_request(user):
    join_channel = UserChannel.objects.filter(status="Joined")
    return join_channel


@register.filter(name="total_channel")
def total_channel(user):
    total_channel = Channel.objects.filter(is_delete=False, is_active=True).count()
    return total_channel


@register.filter(name="new_channel")
def new_channel(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    new_channel = Channel.objects.filter(is_active=True, is_delete=False, created_at__gte=last_date).count()
    return new_channel


@register.filter(name="total_course")
def total_course(user):
    total_course = Content.objects.filter(is_delete=False).count()
    return total_course


@register.filter(name="new_course")
def new_course(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    new_course = Content.objects.filter(is_delete=False, created_at__gte=last_date).count()
    return new_course


@register.filter(name="new_enrollment")
def new_enrollment(user):
    last_date = datetime.date.today() - datetime.timedelta(days=7)
    new_enrollment = UserChannel.objects.filter(status="Joined", created_at__gte=last_date).count()
    return new_enrollment


@register.filter(name="total_users")
def total_users(user):
    user_type = UserTypes.objects.get(type="Learner")
    total_users = User.objects.filter(userType=user_type).count()
    return total_users


@register.filter(name="get_all_user")
def get_all_user(user):
    user_type = UserTypes.objects.filter(type__in=["Learner", "Mentor", "ProgramManager"])
    total_users_list = User.objects.filter(userType__in=user_type)
    if user.session['user_type'] == "ProgramManager":
        user = user.user
        print(user.company.all())
        total_users_list = total_users_list.filter(company__in=user.company.all())
    return total_users_list


@register.filter(name="get_all_learner")
def get_all_learner(user):
    all_learner = Learner.objects.all()
    if user.session['user_type'] == "ProgramManager":
        all_learner = all_learner.filter(company__in=user.company.all())

    return all_learner


@register.filter(name="get_all_mentor")
def get_all_mentor(user):
    user_type = UserTypes.objects.get(type="Mentor")
    total_users = User.objects.filter(userType=user_type)
    return total_users


@register.filter(name="all_role")
def all_role(user):
    roles = UserRoles.objects.all()
    return roles


@register.filter(name="sub_channel_with_pathway")
def sub_channel_with_pathway(channel):
    sub_channel = Channel.objects.filter(parent_id=channel, is_delete=False, is_active=True)
    content = []

    for sub_channel in sub_channel:

        data = SkillConfig.objects.filter(channel=channel, sub_channel=sub_channel)
        if data.count() > 0:
            content.append({
                "title": sub_channel.title,
                "id": sub_channel.pk
            })

    return content


@register.filter(name="get_type")
def get_type(value):
    try:
        datetime_object = parser.isoparse(value)
        date = datetime_object.strftime('%m/%d/%Y')
    except:
        date = value
    return date


@register.simple_tag(takes_context=True)
def cookie(context, cookie_name):  # could feed in additional argument to use as default value
    request = context['request']
    result = request.COOKIES.get(cookie_name, '')  # I use blank as default value
    return result


@register.filter(name="check_value_is_none")
def check_value_is_none(data):
    if data is None:
        return "-"
    else:
        return data


@register.filter(name="user_profile_assessment")
def user_profile_assessment(user):
    user_profile_assest = UserProfileAssest.objects.filter(user=user)
    return len(user_profile_assest)


@register.filter(name="all_company")
def all_company(user):
    company = Company.objects.filter(is_delete=False)
    return company


@register.filter(name="all_coupon")
def all_coupon(user):
    coupon = Coupon.objects.filter(is_delete=False, is_active=True)
    return coupon


@register.filter(name='split')
def split(value, arg):
    return value.split(arg)


@register.simple_tag
def get_chat_room(user_one, user_two):
    my_chat_room = AllRooms.objects.filter(
        Q(user1=user_one) & Q(user2=user_two) | Q(user1=user_two) & Q(user2=user_one)).first()

    if my_chat_room is None:
        room_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        AllRooms.objects.create(user1=user_one, user2=user_two, name=room_name)
    else:
        room_name = my_chat_room.name
    return room_name


@register.filter(name='get_users')
def get_users(user):
    return User.objects.filter(is_active=True, is_delete=False)


@register.filter(name='get_mentor_mentees')
def get_mentor_mentees(mentor, company_id=None):
    company = mentor.company.all()
    if company_id:
        company = company.filter(pk=company_id)

    journey = Channel.objects.filter(Q(is_global=True) | Q(company__in=company), closure_date__gt=datetime.datetime.now(),
                                      parent_id=None, is_active=True, is_delete=False)
    return AssignMentorToUser.objects.filter(mentor=mentor, is_assign=True, is_revoked=False, journey__in=journey)


@register.filter(name='get_suggestion_goals')
def get_suggestion_goals(userId):
    user = User.objects.get(id=userId)
    return UserDrivenGoal.objects.filter(created_by__username="admin", is_active=True, goal_type="User Driven")[:20]


@register.filter(name='program_manager_members')
def program_manager_members(program_manager):
    managers = User.objects.filter(pk=program_manager.pk)
    for manager in managers:
        users = User.objects.filter(company__in=manager.company.all())
        # print("users", users)
    users_list = []
    for user in users:
        if (user not in users_list and user != program_manager):
            users_list.append(user)

    # print("user_list", users_list)

    return users_list


@register.filter(name='program_manager_journeys')
def program_manager_journeys(program_manager):
    company = program_manager.company.all()
    journey_list = Channel.objects.filter(company__in=company)
    return journey_list

@register.filter(name='get_mentee_journeys')
def get_mentee_journeys(user, company_id):
    channel = UserChannel.objects.filter(status="Joined", user=user, Channel__is_active=True, Channel__is_delete=False, Channel__company__id=company_id, Channel__closure_date__gt=datetime.datetime.now())
    return [channel.Channel for channel in channel]


@register.filter(name='get_journeys')
def get_journeys(user, type):
    print("get jo", user, type)
    if type == 'Learner':
        channel = UserChannel.objects.filter(status="Joined", user=user)
        joined_channel = []
        for channel in channel:
            if channel.Channel.is_active == True and channel.Channel.is_delete == False:
                joined_channel.append(channel.Channel)
        return joined_channel
    if type == 'Mentor':
        return mentor_channel(user)
    return "no data"

@register.filter(name='feedback_template')
def feedback_template(user):
    template_list = FeedbackTemplate.objects.all()
    return template_list

@register.filter(name='weekly_journal_template')
def weekly_journal_template(user):
    journal_list = WeeklyjournalsTemplate.objects.all()
    return journal_list

@register.filter(name="public_annouce_type")
def public_annouce_type(user):
    annouce_type = PublicProgramAnnouncement.annoucement_type
    type_list = [type[0] for type in annouce_type]
    print(type_list)
    return type_list



@register.filter(name="company_logo")
def company_logo(company_id):
    if company_id:
        company = Company.objects.get(pk=company_id)
        return company.logo
    else:
        return None

@register.filter(name="company_banner")
def company_banner(company):
    company = Company.objects.get(pk=company)
    # print("company logo", company.logo)
    return company.banner

