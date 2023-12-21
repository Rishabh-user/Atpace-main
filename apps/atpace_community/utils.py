import html2text
from django.db.models.query_utils import Q
from django import template
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.http import BadHeaderError, HttpResponse
from django.template.loader import render_to_string
from django.utils.timesince import timesince
import requests
import json
from apps.content.models import Channel, UserChannel
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
import string
import random
import pytz
# from apps.atpace_community.scrap import generate_preview
from apps.community.models import JourneySpace
from apps.users.models import Collabarate, ProgramManager, User
from ravinsight.web_constant import BASE_URL, COMMUNITY_DOMAIN, INFO_CONTACT_EMAIL, LOGIN_URL, PROTOCOL, SITE_NAME
from .models import Attachments, Event, Comment, MemberInvitation, Post, SavedPost, SpaceGroups, SpaceJourney, SpaceMembers, Spaces, likes, UserPinnedPost
from ravinsight.web_constant import Space_Group_ID
# import timeago
from datetime import datetime
from django.utils import timezone
from apps.vonage_api.utils import community_update, create_vonage_api_record, url_shortner
import re

now = datetime.now(timezone.utc)


def local_time(obj):
    return timezone.localtime(obj)

def convert_to_local_time(obj, offset):
    
    # offset is the timezone coming from the session
    # Set the timezone you want to convert to
    tz = pytz.timezone(offset)

    # Get the current time in UTC
    utc_time = obj

    return utc_time.replace(tzinfo=pytz.utc).astimezone(tz)

def convert_to_utc(obj, offset):


    local = pytz.timezone(offset)
    print("local TIME ****", local)

    naive = datetime.strptime(str(obj), "%Y-%m-%d %H:%M:%S")
    print("NAIVE TIME ****", naive)

    local_dt = local.localize(naive, is_dst=None)
    print("local_dt  ****", local_dt)

    utc_dt = local_dt.astimezone(pytz.utc)
    print("utc_dt  ****", utc_dt)

    return utc_dt

def strf_format(obj):
    return obj.strftime("%d-%m-%y %H:%M %p")

def datetime_string(obj):
    day = obj.strftime("%d %B")
    time = obj.strftime("%I:%H %p")
    return day, time

def aware_time(date_time):
    utc = pytz.UTC
    return utc.localize(date_time)


def avatar(user):
    if user.avatar:
        avatar = str(user.avatar.url)
        avatar = avatar.split('?')
        return avatar[0]
    else:
        return ''

def certificate_file(obj):
    if obj.file:
        file = str(obj.file.url)
        file = file.split('?')
        return file[0]
    else:
        return ''

def certificate_image(obj):
    if obj.certificate:
        file = str(obj.certificate.url)
        file = file.split('?')
        return file[0]
    else:
        return ''


def activityFile(data):
    if data.upload_file:
        file = str(data.upload_file.url)
        file = file.split('?')
        return file[0]
    else:
        return ''

def ques_image(test):
    if test.image:
        image = str(test.image.url)
        image = image.split('?')
        return image[0]
    else:
        return ''


def group_avatar(room):
    if room.group_image:
        avatar = str(room.group_image.url)
        avatar = avatar.split('?')
        return avatar[0]
    else:
        return ''


def cover_images(obj):
    if obj.cover_image:
        cover_image = str(obj.cover_image.url)
        cover_image = cover_image.split('?')
        return cover_image[0]
    else:
        return ''

def icons(obj):
    if obj.icon:
        icon = str(obj.icon.url)
        icon = icon.split('?')
        return icon[0]
    else:
        return ''


def post_comment_images(obj):
    if obj.image_upload:
        avatar = str(obj.image_upload.url)
        avatar = avatar.split('?')
        return avatar[0]
    else:
        return ''


def post_comment_file(obj):
    if obj.file_upload:
        avatar = str(obj.file_upload.url)
        avatar = avatar.split('?')
        return avatar[0]
    else:
        return ''

def broadcast_attachment(announcement):
    if announcement.attachment:
        attachment = str(announcement.attachment.url)
        attachment = attachment.split('?')
        return attachment[0]
    else:
        return ''

def like_post_comment(user=None, post=None, comment=None):
    is_like = False
    if user is not None:
        like = likes.objects.filter(comment=comment, is_like=True, created_by=user).count(
        ) if comment else likes.objects.filter(post=post, is_like=True, created_by=user).count()
        if like > 0:
            is_like = True
    like_count = likes.objects.filter(comment=comment, is_like=True).count(
    ) if comment else likes.objects.filter(post=post, is_like=True).count()
    return is_like, like_count


def post_comment_attachments(attachments):
    attachment_list = []
    if attachments is not None:
        attachment_list.extend({"id": attachment.id, "image": post_comment_images(attachment), "file": post_comment_file(
            attachment), "created_at": attachment.created_at, } for attachment in attachments)

    return attachment_list


def Postcomments(comments, user=None):
    commment_list = []
    for comment in comments:
        attachments = Attachments.objects.filter(comment=comment, upload_for="Comment")
        replys = Comment.objects.filter(parent_id=comment, inappropriate_content=False, is_active=True, is_delete=False)
        is_like, likess = like_post_comment(user, post=None, comment=comment)
        reply_list = []
        if replys is not None:
            for reply in replys:
                reply_attachments = Attachments.objects.filter(comment=reply, upload_for="Comment")
                attachment = post_comment_attachments(reply_attachments)
                reply_list.append({
                    "id": reply.id,
                    "parent_id": reply.parent_id.id,
                    "description": reply.Body,
                    "cover_image": cover_images(reply),
                    "attachment": attachment,
                    "likes_count": likess,
                    "is_user_like": is_like,
                    "created_at": time_ago(local_time(comment.created_at)),
                    "created_by_id": comment.created_by.id,
                    "created_by": comment.created_by.first_name+' '+comment.created_by.last_name,
                    "heading": comment.created_by.profile_heading,
                    "user_profile_image": avatar(comment.created_by)
                })
        attachment = post_comment_attachments(attachments)
        commment_list.append({
            "id": comment.id,
            "post_id": comment.post.id,
            "post_name": comment.post.title,
            "description": comment.Body,
            "cover_image": cover_images(comment),
            "attachment": attachment,
            "replys": reply_list,
            "likes_count": likess,
            "is_user_like": is_like,
            "created_by": comment.created_by.first_name+" "+comment.created_by.last_name,
            "created_by_id": comment.created_by.id,
            "created_at": time_ago(local_time(comment.created_at)),
            "heading": comment.created_by.profile_heading,
            "attachments": attachment,
            "user_profile_image": avatar(comment.created_by)
        })
    return commment_list


def EventData(post, filter_by=None,  offset=None):
    try:
        event = Event.objects.get(post_id=post)
    except:
        event_list = []
        return event_list
    event_status = 'upcoming'
    ago_time = time_ago(convert_to_local_time(event.start_time, offset))
    if not Event.objects.filter(post_id=post, end_time__gt=datetime.now()).exists():
        event_status = 'past'
        ago_time = time_ago(convert_to_local_time(event.end_time, offset))
    host = {
        "id": event.host.id,
        "name": f"{event.host.first_name} {event.host.last_name}",
        "profile_image": avatar(event.host)
    }
    attendees_list = []
    for attendees in event.attendees.all():
        attendees_list.append({
            "id": attendees.id,
            "name": f"{attendees.first_name} {attendees.last_name}",
            "profile_image": avatar(attendees)
        })
    members_joined_list = []
    for members in event.members_joined.all()[:3]:
        members_joined_list.append({
            "id": members.id,
            "name": f"{members.first_name} {members.last_name}",
            "profile_image": avatar(members)
        })
    # #print("date",  event.start_time.strftime("%d %b"))
    event_list = {
        "id": event.id,
        "start_date": convert_to_local_time(event.start_time, offset).strftime("%d"),
        "start_month": convert_to_local_time(event.start_time, offset).strftime("%b"),
        "start_time": convert_to_local_time(event.start_time, offset).strftime("%H:%M %p"),
        "complete_start_time": convert_to_local_time(event.start_time, offset),
        "complete_end_time": convert_to_local_time(event.end_time, offset),
        "end_date": convert_to_local_time(event.end_time, offset).strftime("%d"),
        "end_month": convert_to_local_time(event.end_time, offset).strftime("%b"),
        "end_time": convert_to_local_time(event.end_time, offset).strftime("%H:%M %p"),
        "ago_time": ago_time,  
        "location": event.location,
        "attendees": attendees_list,
        "members_joined": members_joined_list,
        "host": host,
        "frequency": event.frequency,
        "is_tbd": event.is_tbd,
        "event_url": url_shortner(event.event_url, BASE_URL),
        "is_location_hidden": event.is_location_hidden,
        "is_email_notification": event.is_email_notification,
        "is_in_app_notification": event.is_in_app_notification,
        "is_email_remainder": event.is_email_remainder,
        "is_in_app_remainder": event.is_in_app_remainder,
        "is_customize_msg": event.is_customize_msg,
        "event_status": event_status,
        "members_joined_count": event.members_joined.all().count() - 3
    }
    return event_list


def response_post(post_id, filter_by=None, offset=None):
    post = Post.objects.get(id=post_id)
    updated_by = User.objects.filter(id=post.update_by).first()
    attachments = Attachments.objects.filter(post=post, upload_for="Post")
    attachment = post_comment_attachments(attachments)
    event_list = []
    if (post.post_type == 'Event'):
        event_list = EventData(post, filter_by, offset)
        #print(f"{post.title}: {event_list}")
    data = {
        "id": post.id,
        "title": post.title,
        "body": post.Body,
        "cover_image": cover_images(post),
        "tags": [],
        "slug": post.slug,
        "post_type": post.post_type,
        "is_comments_enabled": post.is_comments_enabled,
        "is_liking_enabled": post.is_liking_enabled,
        "notify_space_members": post.notify_space_members,
        "space_id": post.space.id,
        "space_name": post.space.title,
        "space_group_id": post.space_group.id,
        "created_by": f"{post.created_by.first_name} {post.created_by.last_name}",
        "created_by_id": post.created_by.id,
        "updated_by_id": post.update_by,
        "updated_by": f"{updated_by.first_name} {updated_by.last_name}" if post.update_by else '',
        "created_at": time_ago(local_time(post.created_at)),
        "heading": post.created_by.profile_heading,
        "user_profile_image": avatar(post.created_by),
        "attachments": attachment,
        "event": event_list
    }
    return data

# def UpdateUrl(text):
#     url = re.search("(<p>https?://[^\s]+</p>)|(^https?://[^\s]+)", text).group()
#     url = re.sub("<p>|</p>", "", url)
#     updated_text = re.sub(url, "<p><a href='"+url+"' rel='noopener noreferrer' target='_blank'>"+url+" </a></p>", text)
#     return updated_text

def replace_links_with_anchor_tags(text):
    print("Calling replace link", text)
    def replace_link(match):
        url = match.group(0)
        return f'<a href="{url}">{url}</a>'

    # Regex pattern to match URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    # Replace URLs with anchor tags using the callback function
    replaced_text = re.sub(url_pattern, replace_link, text)
    print("replaced_text", replaced_text)
    return replaced_text

def all_posts(posts, filter_by=None, user=None, offset=None):
    #print("all_post_user", user, filter_by)
    data = []
    for post in posts:
        is_like = False
        is_saved = False
        attachment_list = []
        if UserPinnedPost.objects.filter(user=user, post=post, is_pinned=True).exists():
            is_pinned = True
        else:
            is_pinned = False
        updated_by = User.objects.filter(id=post.update_by).first()
        comments = Comment.objects.filter(post=post, parent_id=None, inappropriate_content=False,
                                          comment_for="Post", is_active=True, is_delete=False)
        total_comments = comments.count()
        attachments = Attachments.objects.filter(post=post, upload_for="Post")
        is_like, likess = like_post_comment(user, post=post, comment=None)
        if attachments is not None:
            attachment_list.extend({"id": attachment.id, "image": post_comment_images(attachment), "file": post_comment_file(
                attachment), "created_at": local_time(attachment.created_at), } for attachment in attachments)
        if not user:
            is_saved = False
        else:
            saved_post = SavedPost.objects.filter(saved_by=user, is_saved=True,
                                                  post=post, is_active=True, is_delete=False).count()
            if saved_post > 0:
                is_saved = True

        # commment_list = Postcomments(comments, user) if comments else []
        event_list = []
        # event_type = ''
        if post.post_type == 'Event':
            event_list = EventData(post, filter_by=None, offset=offset)
            # if event_list:
                # event_type = event_list['event_status']
                # print("event_list", event_list['event_status'], filter_by, post.post_type)
        # if (post.post_type == 'Event' and event_type == filter_by) | (post.post_type != 'Event'):
        if (post.post_type == 'Event' and filter_by != 'all' ) | (post.post_type != 'Event'):

            # description = replace_links_with_anchor_tags(post.Body) if '<p>http' in post.Body or re.search("(^https?://[^\s]+)", post.Body) else post.Body
            description = post.Body

            data.append({
                "id": post.id,
                "space_id": post.space.id,
                "space_name": post.space.title,
                "space_privacy": post.space.privacy,
                "default_space": post.space.is_default,
                "space_group_id": post.space_group.id,
                "space_group_name": post.space_group.title,
                "space_group_privacy": post.space_group.privacy,
                "title": post.title,
                "description": description,
                # "url_data": body,
                "cover_image": cover_images(post),
                "post_type": post.post_type,
                "is_comments_enabled": post.is_comments_enabled,
                "is_liking_enabled": post.is_liking_enabled,
                "is_active": post.is_active,
                "created_by": f"{post.created_by.first_name} {post.created_by.last_name}",
                "created_by_id": post.created_by.id,
                "user_profile_image": avatar(post.created_by),
                "heading": post.created_by.profile_heading,
                "updated_by_id": post.update_by,
                "updated_by": f"{updated_by.first_name} {updated_by.last_name}" if post.update_by else '',
                "created_at": time_ago(local_time(post.created_at)),
                "likes_count": likess,
                "is_user_like": is_like,
                "is_user_saved": is_saved,
                "attachments": attachment_list,
                "total_comments": total_comments,
                # "comments": commment_list,
                "user_type": delete_post(user, post) if user is not None else None,
                "event": event_list,
                "is_pinned": is_pinned
            })
    return data


def user_comment(comment):
    attachments = Attachments.objects.filter(comment=comment, upload_for="Comment")
    attachments = post_comment_attachments(attachments)
    data = {
        "id": comment.id,
        "parent_id": comment.parent_id.id if comment.parent_id else '',
        "body": comment.Body,
        "post_id": comment.post.id,
        "post_title": comment.post.title,
        "comment_for": comment.comment_for,
        "is_active": comment.is_active,
        "created_by": comment.created_by.first_name+" "+comment.created_by.last_name,
        "created_by_id": comment.created_by.id,
        "heading": comment.created_by.profile_heading,
        "created_at": time_ago(local_time(comment.created_at)),
        "user_profile_image": avatar(comment.created_by),
        "attachments": attachments
    }
    response = {
        "message": "Comment Created",
        "success": True,
        "data": {
            "user_post": data,
        }
    }
    return response


class Pagination(PageNumberPagination):
    page_size = 2


def user_spaces(member_spaces):
    data = []
    for space in member_spaces:
        data.append({
            "id": space.space.id,
            "space_group_id": space.space.space_group.id,
            "space_group": space.space.space_group.title,
            "name": space.space.title,
            "description": space.space.description,
            "slug": space.space.slug,
            "cover_image": cover_images(space.space),
            "privacy": space.space.privacy,
            "member_type": space.user_type,
            "created_by": space.space.created_by.first_name+" "+space.space.created_by.last_name,
            "created_by_id": space.space.created_by.id,
            "heading": space.space.created_by.profile_heading,
            "created_at": local_time(space.space.created_at),
        })
    return data


def space_group_details(space_group, space, user_id, space_member=None):
    data = []
    join = "Join Group"
    if user_id:
        join = space_member.is_joined if space_member.is_joined else "Join Group"
    data.append({
        "id": space_group.id,
        "name": space_group.title,
        "description": space_group.description,
        "cover_image": cover_images(space_group),
        "slug": space_group.slug,
        "privacy": space_group.privacy,
        "is_active": space_group.is_active,
        "is_hidden": space_group.is_hidden,
        "hidden_from_non_members": space_group.hidden_from_non_members,
        "created_by": f"{space_group.created_by.first_name} {space_group.created_by.last_name}",
        "created_by_id": space_group.created_by.id,
        "is_joined": join,
        "created_at": local_time(space_group.created_at)
    })
    return data


def enroll_space_member(user, space, user_type="Member"):
    space_group = space.space_group
    space_members = SpaceMembers.objects.filter(user=user, space=space, space_group=space_group)
    if space_members:
        space_members.update(is_joined=True, is_active=True, is_delete=False, user_type=user_type)
    else:
        SpaceMembers.objects.create(user=user, space=space, invitation_status="Accept", user_type=user_type,
                                    space_group=space_group, is_joined=True, email=user.email)
        return True
    return False


def create_journey_space(journey, user):
    channel = Channel.objects.get(id=journey.id)
    #print("admin ", channel.channel_admin.all())
    user = user
    space_group = SpaceGroups.objects.get(id=Space_Group_ID)
    # if(Spaces.objects.filter(title=journey.title).exists()):
    #     space = Spaces.objects.filter(title=journey.title)
    #     space.is_hidden = True
    #     space.save()
    data = {
        "title": channel.title,
        "description": channel.description,
        "cover_image": channel.image,
        "privacy": "Private",
        "is_hidden": False,
        "hidden_from_non_members": False,
        "is_active": channel.is_active,
        "space_group": space_group,
        "created_by": user,
    }
    space = Spaces.objects.create(**data)
    SpaceJourney.objects.create(space=space, journey=channel)
    user_channel = UserChannel.objects.filter(user=user, Channel=channel)
    if channel.program_team_1:
        enroll_space_member(channel.program_team_1, space, "Moderator")
    if channel.program_team_2:
        enroll_space_member(channel.program_team_2, space, "Moderator")
    #print(f"channel_admin {channel.channel_admin.all()}")
    if journey_admin := channel.channel_admin.all():
        for admin in journey_admin:
            enroll_space_member(admin, space, "Moderator")
    for channels in user_channel:
        enroll_space_member(channels.user, space)
    if not SpaceMembers.objects.filter(user=user, space=space, space_group=space_group).exists():
        if "Admin" in [type.type for type in user.userType.all()]:
            enroll_space_member(user, space, "Admin")
        elif "ProgramManager" in [type.type for type in user.userType.all()]:
            enroll_space_member(user, space, "Moderator")
    return True


def update_space_journey(user, journey, community_required):
    if SpaceJourney.objects.filter(journey=journey).exists():
        channel = Channel.objects.get(id=journey.id)
        space_journey = SpaceJourney.objects.filter(journey=journey).first()
        space_id = space_journey.space.id
        space = Spaces.objects.filter(id=space_id)
        if not community_required:
            space.update(title=channel.title, is_active=False, is_delete=True, deleted_by=user.id)
        else:
            space.update(title=channel.title, is_active=channel.is_active, is_delete=False, update_by=user.id)
            space_member = SpaceMembers.objects.filter(space=space.first(), is_joined=True, space_group=space.first().space_group, user_type="Moderator")
            space_member.update(is_joined=False, is_active=False, is_delete=True)
            if channel.program_team_1:
                enroll_space_member(channel.program_team_1, space.first(), "Moderator")
            if channel.program_team_2:
                enroll_space_member(channel.program_team_2, space.first(), "Moderator")
            if journey_admin := channel.channel_admin.all():
                for admin in journey_admin:
                    enroll_space_member(admin, space.first(), "Moderator")
        return True
    elif community_required:
        create_journey_space(journey, journey.created_by)
        return True
    return False


def add_member_to_space(journey, user):
    if not SpaceJourney.objects.filter(journey=journey).exists():
        create_journey_space(journey, journey.created_by)
    space_journey = SpaceJourney.objects.get(journey=journey)
    space = space_journey.space
    space_group = space_journey.space.space_group
    if not SpaceMembers.objects.filter(user=user, space=space, space_group=space_group).exists():
        SpaceMembers.objects.create(user=user, user_type="Member", space=space, space_group=space_group,
                                    is_joined=True, email=user.email, invitation_status="Accept")
        return True
    return False


def time_ago(created_at):
    # return timeago.format(created_at, now)
    return timesince(created_at, timezone.now())


def time_ago_days(created_at):
    time = timesince(created_at, timezone.now())
    time = time.split(",")[0]
    return time


def whatsapp_message(post, user):

    message = f"{post.title}\n\nhttps://community.growatpace.com/c/growme"
    # message = """Congratulations! For enrolling in the following program

    #             Program Name: Human Resource
    #             Link to access program: https://vonage.sg

    #             Accessible till: 31 Aug 2021

    #             Please send us a message if we can be of help by responding to this message

    #             Regards
    #             Team AtPace'
    #         """
    url = "https://messages-sandbox.nexmo.com/v1/messages"
    from_user = "14157386102"
    to_user = "917000448113"
    message_type = "text"
    payload = json.dumps({
        "from": from_user,
        "to": to_user,
        "message_type": message_type,
        "text": message,
        "channel": "whatsapp"
    })
    # create_vonage_api_record(from_user = from_user, to_user = to_user, message_type=message_type, user = user, post= post)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic MWE2MDUxYjY6Y2FEdXNOTjlVQVVjYXRERw=='
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    message_id = response.json()['message_uuid']
    create_vonage_api_record(from_user=from_user, to_user=to_user, message_type=message_type,
                             user=user, post=post, message_id=message_id, message=message)
    return True


def send_new_post_mail(user, post, email_list):
    subject = str(post.title).capitalize()
    data = {
        'domain': COMMUNITY_DOMAIN,
        'site_name': SITE_NAME,
        "user_name": f"{user.first_name} {user.last_name}",
        "space_name": post.space.title,
        "user_profile_heading": user.profile_heading,
        "post_title": post.title,
        "user_profile_image": avatar(user),
        "description": post.Body,
        "post_id": post.id,
        "url": f"{PROTOCOL}://{COMMUNITY_DOMAIN}/post-details/{post.id}",
        "time_zone": timezone.get_current_timezone(),
    }
    email_message = render_to_string('atpace_email/new-post-email.html', data)
    message = strip_tags(email_message)
    try:
        mail = send_mail(subject, message, INFO_CONTACT_EMAIL, email_list, html_message=email_message)
    except BadHeaderError:
        return HttpResponse('Invalid header found.')
    return True


def send_report_post_mail(user, post, report):
    subject = f"{report.report_by.first_name} {report.report_by.last_name} Reported To This Post"
    data = {
        'domain': COMMUNITY_DOMAIN,
        'site_name': SITE_NAME,
        "user_name": f"{user.first_name} {user.last_name}",
        "space_name": post.space.title,
        "user_profile_heading": user.profile_heading,
        "post_title": post.title,
        "user_profile_image": avatar(user),
        "description": post.Body,
        "post_id": post.id,
        "reported_by": f"{report.report_by.first_name} {report.report_by.last_name}",
        "report_type": report.report_type,
        "description": report.comment,
        "url": f"{PROTOCOL}://{COMMUNITY_DOMAIN}/post-details/{post.id}",
        "time_zone": timezone.get_current_timezone(),
    }
    email_message = render_to_string('atpace_email/report-post.html', data)
    message = strip_tags(email_message)
    try:
        mail = send_mail(subject, message, INFO_CONTACT_EMAIL, ["takvikas259@gmail.com"], html_message=email_message)
    except BadHeaderError:
        return HttpResponse('Invalid header found.')
    return True


def post_filter(posts, filter_by, user=None, offset=None):
    if filter_by == "old":
        posts = posts.order_by('created_at')
    elif filter_by == "new":
        posts = posts.order_by('-created_at')
    #print("filter_by", filter_by)
    return all_posts(posts, filter_by, user, offset=offset)


def random_string():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(32))


def send_invite_user_mail(user, email):
    subject = "Invitation Link to Join the Grow AtPace Community"
    string = random_string()
    data = {
        'domain': COMMUNITY_DOMAIN,
        'site_name': SITE_NAME,
        "user_name": f"{user.first_name} {user.last_name}",
        'token': string,
        "protocol": PROTOCOL,
        "url": f"{COMMUNITY_DOMAIN}/login"
    }
    email_message = render_to_string('atpace_email/invite-user.html', data)
    message = strip_tags(email_message)
    try:
        mail = send_mail(subject, message, INFO_CONTACT_EMAIL, [email], html_message=email_message)
    except BadHeaderError:
        return HttpResponse('Invalid header found.')
    # MemberInvitation.objects.create(Invite_email=email, invited_by=user, invite_by_id=user.id, status=True, string = string)
    return True


def default_space_join_user(user):
    # space = Spaces.objects.get(is_default=True)
    space_list = Spaces.objects.filter(privacy="Public")
    for space in space_list:
        space_group = space.space_group
        if not SpaceMembers.objects.filter(user=user, space=space, space_group=space_group).exists():
            space_member = SpaceMembers.objects.create(user=user, space=space, invitation_status="Accept",
                                                       space_group=space_group, is_joined=True, email=user.email)

            return space_member

    return True


def public_post_response(space, data, user_id, user=None):
    response = {
        "message": "Public Post Data",
        "success": True,
        "data": {
            "user_id": '' if user_id is None else user.id,
            "space_id": space.id,
            "space_name": space.title,
            "space_privacy": space.privacy,
            "public_post": data,
        }
    }
    return response


def create_community_post(user, channel, title, body, type):
    journey_space = SpaceJourney.objects.get(journey=channel)
    #print(journey_space.space)
    space = Spaces.objects.get(id=journey_space.space.id)
    space_group = space.space_group
    if type == "KeyPoints":
        type = "LearningJournal"
        title = f"{title}- Learning Journal"
        body = f"<div><div>Here are the key learnings on this journey</div>{body}</div>"

    elif type == "AskQuestion":
        type = "AskQuestion"
        title = f"Question: - {title}"

    elif type == "WeeklyJournal":
        type = "WeeklyJournal"
        title = f"{title}- Weekly Learning Journal"
    data = {
        "title": title,
        "Body": body,
        "is_comments_enabled": True,
        "is_liking_enabled": True,
        "space": space,
        "space_group": space_group,
        "notify_space_members": False,
        "created_by": user,
        "post_type": type,
        # "post_type": "Post"
    }
    post = Post.objects.create(**data)
    if user_query_set := SpaceMembers.objects.filter(~Q(user=user), space=space):
        user_list = [member.user for member in user_query_set]
        for member in user_list:
            if member.phone and member.is_whatsapp_enable:
                community_update(member, post)
    return True


def get_community_space_post(channel, user):
    space_journey = SpaceJourney.objects.get(journey=channel)
    space = Spaces.objects.get(id=space_journey.space.id, space_group__id=space_journey.space.space_group.id)
    posts = Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False)
    return all_posts(posts, "all", user)


def get_community_space_post_details(channel, post_id):
    # space_journey = SpaceJourney.objects.get(journey=channel)
    # space = Spaces.objects.get(id=space_journey.space.id)
    # post = Post.objects.filter(id=post_id, space=space)
    return response_post(post_id)


def get_community_space_post_comment(channel, post_id):
    space_journey = SpaceJourney.objects.get(journey=channel)
    space = Spaces.objects.get(id=space_journey.space.id)
    post = Post.objects.get(id=post_id, space=space)
    comments = Comment.objects.filter(post=post, parent_id=None, comment_for="Post", inappropriate_content=False, is_active=True, is_delete=False)
    return Postcomments(comments)


def community_post_Comment(channel, post_id, body, user):
    journey_space = SpaceJourney.objects.get(journey=channel)
    space = Spaces.objects.get(id=journey_space.space.id)
    post = Post.objects.get(id=post_id, space=space)
    data = {
        "post": post,
        "Body": body,
        "created_by": user,
        "parent_id": None
    }
    Comment.objects.create(**data)
    return True


def delete_post(user, post):
    user_type = ",".join(str(type.type) for type in user.userType.all())
    space_member = SpaceMembers.objects.filter(user=user, space_group=post.space_group)
    if "Admin" in user_type:
        return "Admin"
    elif "ProgramManager" in user_type and space_member:
        return "ProgramManager"
    else:
        return None


def space_filter(spaces, order_by):
    if order_by == "new":
        spaces = spaces.order_by('-created_at')
    elif order_by == "old":
        spaces = spaces.order_by('created_at')
    elif order_by == "alphabetical":
        spaces = spaces.order_by('title')
    return spaces


def add_to_community_event(data, user, space_id, offset=None):
    #print("inside", space_id)

    if data.add_to_community:
        space = Spaces.objects.get(id=space_id, space_type="Event")
        event_obj = ''
        try:
            event_obj = Event.objects.get(collabarate_id=data.id)
        except:
            pass
        if event_obj:
            #print("post_id", event_obj.post_id.id)
            post = Post.objects.get(pk=event_obj.post_id.id)
            post.title = data.title
            post.Body = data.description
            post.space = space
            post.space_group = space.space_group
            post.updated_by = user
            post.is_active = True
            post.is_delete = False
            post.save()

            event_obj.start_time = convert_to_utc(str(data.start_time).replace("+00:00",""), offset)
            event_obj.end_time = convert_to_utc(str(data.end_time).replace("+00:00",""), offset)
            event_obj.host = data.speaker
            event_obj.event_url = data.custom_url
            for attendee in event_obj.attendees.all():
                event_obj.attendees.remove(attendee)
            attendees = User.objects.filter(company=data.company)
            for attendee in attendees:
                event_obj.attendees.add(attendee)
            event_obj.save()

        else:
            post = Post.objects.create(title=data.title, Body=data.description, space=space,
                                       space_group=space.space_group, created_by=user, post_type='Event')
            event = Event.objects.create(post_id=post, start_time=convert_to_utc(str(data.start_time).replace("+00:00",""), offset),
                                         end_time=convert_to_utc(str(data.end_time).replace("+00:00",""), offset), host=data.speaker, event_url=data.custom_url, collabarate_id=data.id, add_to_collabarate=True)

            attendees = User.objects.filter(company=data.company)

            for attendee in attendees:
                event.attendees.add(attendee)

            event.save()
    else:
        try:
            event_obj = Event.objects.get(collabarate_id=data.id)
            event_obj.add_to_collabarate = False
            event_obj.save()
            post = Post.objects.get(id=event_obj.post_id.id)
            post.is_active = False
            post.is_delete = True
            post.save()

        except:
            pass

    return "true"


def get_text(data):
    h = html2text.HTML2Text()
    h.ignore_links = True
    return h.handle(data)
