import requests

from apps.community.models import AddMemberToSpace, CicleDataDump, CommunityPost, CommunityPostComment, JourneySpace, LearningJournalsAttachment, \
    UserCircleDetails
from apps.webapp.utils import space_groups, spaces
import pandas as pd
from apps.mentor.models import AssignMentorToUser
from apps.leaderboard.views import send_push_notification

def create_journey_private_space(journey, name):
    space_group_id = "53537"
    community_id = "22900"
    print("journey {}, name {}".format(journey, name))
    url = "http://app.circle.so/api/v1/spaces?community_id="+str(community_id)+"&name="+str(
        name)+"&is_private=true&is_hidden_from_non_members=false&is_hidden=false&space_group_id="+str(space_group_id)
    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.post(
        url=url,
        headers=headers,

    )
    data = response_body.json()
    print(data)
    CicleDataDump.objects.create(data=data, type="create_space")

    space = data['space']
    space_group_id = space['space_group_id']
    space_id = space['id']
    slug = space['slug']
    community_id = space['community_id']
    space_group_name = space['space_group_name']
    name = space['name']
    is_private = space['is_private']
    is_hidden_from_non_members = False
    is_hidden = False
    url = space['url']
    create_space = JourneySpace.objects.create(journey=journey, space_id=space_id, community_id=community_id, space_group_name=space_group_name, name=name,
                                               is_private=is_private, is_hidden_from_non_members=is_hidden_from_non_members, is_hidden=is_hidden, slug=slug, space_group_id=space_group_id, circle_url=url)
    print(create_space)
    return True


def create_post_to_journey():
    return True


def AddMembertoSpace(user, Channels):
    response = True
    space_id = Channels.journryspace.space_id
    community_id = Channels.journryspace.community_id
    group_id = Channels.journryspace.space_group_id
    email = user.email
    add_member_to_space = AddMemberToSpace.objects.filter(
        community_id=community_id, email=user.email, space_id=space_id)
    print(add_member_to_space)
    if add_member_to_space.count() == 0:

        url = "http://app.circle.so/api/v1/space_members?email=" + \
            str(email)+"&space_id="+str(space_id)+"&community_id="+str(community_id)
        headers = {
            'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
        }
        print(url)
        response_body = requests.post(
            url=url,
            headers=headers,

        )
        data = response_body.json()
        
        CicleDataDump.objects.create(data=data, type="add_member_to_space")

        if data['success']:
            AddMemberToSpace.objects.create(space_id=space_id, community_id=community_id, email=email)
            return response
    
    return response
                
                
    


def RemoveMemberFromSpace():
    space_id = "179132"
    community_id = "22900"
    email = "prashantk794@gmail.com"
    url = "http://app.circle.so/api/v1/space_members?email=" + \
        str(email)+"&space_id="+str(space_id)+"&community_id="+str(community_id)
    # request.delete()
    data = {
        "success": True,
        "message": "User added to space"
    }
    print(data)
    CicleDataDump.objects.create(data=data, type="remove_member_to_space")
    if data['success']:
        AddMemberToSpace.objects.filter(space_id=space_id, community_id=community_id,
                                        email=email).update(is_joined=False)
    return True


def InviteMember(user, space_id, community_id, group_id):
    response = True
    space_ids = space_id
    community_id = community_id
    email = user.email
    name = user.first_name
    password = "Pass@1234"
    space_group_ids = group_id
    url = "http://app.circle.so/api/v1/community_members?email="+str(email)+"&name="+str(
        name)+"&password="+str(password)+"&community_id="+str(community_id)+"&space_ids[]="+str(space_ids)+"&space_group_ids[]="+str(space_group_ids)+"&skip_invitation=true"

    print(url)
    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.post(
        url=url,
        headers=headers,

    )
    data = response_body.json()
    print(data)
    try:
        CicleDataDump.objects.get(data=data)
    except CicleDataDump.DoesNotExist:
        CicleDataDump.objects.create(data=data, type="invite_member")
        if data['success']:
            circle_id = data['user']['id']

            UserCircleDetails.objects.create(circle_id=circle_id, user=user, email=email)

    return response


def create_post(user, channel, title, body, type, microskill_id):
    circle_url = slug = ""
    community_id = space_id = id = 0

    if type == "key_point":
        record_type = "LearningJournal"
        name = title + "- Learning Journal"
        body = "<div><div>Here are the key learnings on this journey</div>"+body+"</div>"
    else:
        record_type = "AskQuestion"
        name = "Question: - " + title
    record_for = "Atpace"
    user_email = user.email
    user_name = user.first_name + " " + user.last_name
    if channel.is_community_required:
        record_for = "Circle"
        space_id = channel.journryspace.space_id
        community_id = channel.journryspace.community_id
        print(community_id)
        print(space_id)
        group_id = channel.journryspace.space_group_id
        community_id = community_id
        space_id = space_id

        # is_pinned:true
        # is_comments_enabled:true
        # is_liking_enabled:true

        # skip_notifications:true
        url = "http://app.circle.so/api/v1/posts?community_id="+str(community_id)+"&space_id="+str(space_id)+"&name="+str(name)+"&body="+str(
            body)+"&is_pinned=false&is_comments_enabled=true&is_liking_enabled=true&user_email="+user_email+"&skip_notifications=true"
        headers = {
            'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
        }
        response_body = requests.post(
            url=url,
            headers=headers,

        )
        data = response_body.json()

        CicleDataDump.objects.create(data=data, type="community_post")
        if data['success']:
            data = data['topic']
            id = data['id']

            space_id = data['space_id']

            community_id = data['community_id']
            name = data['name']
            body = data['body']['body']
            circle_url = data['url']
            slug = data['slug']

    CommunityPost.objects.create(post_id=id, space_id=space_id, community_id=community_id, name=name,
                                 body=body, record_type=record_type, record_for=record_for, circle_url=circle_url, slug=slug, user_email=user.email, user_name=user_name, journey=channel, microskill_id=microskill_id)
    return True


# def delete_post():
#     post_id = "1421570"
#     url = "http://app.circle.so//api/v1/posts/"+str(post_id)+"?community_id=22900"


def get_space_post(community_id, space_id):
    url = "httpS://app.circle.so/api/v1/posts?community_id="+str(community_id)+"&space_id="+str(space_id)
    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.get(
        url=url,
        headers=headers,
    )
    data = response_body.json()
    return data


def get_space_post_details(community_id, post_id):
    url = "http://app.circle.so/api/v1/posts/"+str(post_id)+">community_id="+str(community_id)
    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.get(
        url=url,
        headers=headers,
    )
    data = response_body.json()
    print(data)

    return data


def get_space_post_comment(community_id, space_id, post_id):
    url = "http://app.circle.so/api/v1/comments/?community_id=" + \
        str(community_id)+"&space_id="+str(space_id)+"&post_id="+str(post_id)
    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.get(
        url=url,
        headers=headers,
    )
    data = response_body.json()

    return data


def post_Comment(channel, post_id, body, user):
    community_id = space_id = id = 0
    user_email = user.email
    user_name = user.first_name + " " + user.last_name
    kwargs = {
        "id": post_id
    }

    if channel.is_community_required:
        kwargs = {
            "post_id": post_id
        }
        space_id = channel.journryspace.space_id
        community_id = channel.journryspace.community_id
        group_id = channel.journryspace.space_group_id
        url = "http://app.circle.so/api/v1/comments/?community_id=" + \
            str(community_id)+"&space_id="+str(space_id)+"&post_id=" + \
            str(post_id)+"&body="+str(body)+"&user_email="+user_email

        headers = {
            'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
        }
        response_body = requests.post(
            url=url,
            headers=headers,
        )
        data = response_body.json()
        if data['success']:
            data = data['comment']
            id = data['id']

            space_id = data['space_id']
            community_id = data['community_id']

            body = data['body']['body']

            post_id = data['post_id']
        CicleDataDump.objects.create(data=data, type="community_post_comment")

    try:
        community_post = CommunityPost.objects.get(**kwargs)
    except CommunityPost.DoesNotExist:
        community_post = None
    CommunityPostComment.objects.create(comment_id=id, community_post=community_post,  post_id=post_id,
                                        space_id=space_id, community_id=community_id, body=body, user_email=user_email, user_name=user_name)
    return True


def check_user_accept_invite(user, Channels):
    space_id = Channels.journryspace.space_id
    community_id = Channels.journryspace.community_id
    group_id = Channels.journryspace.space_group_id
    email = user.email
    response = False
    url = "http://app.circle.so/api/v1/community_members/search?community_id="+str(community_id)+"&email="+str(email)
    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.get(
        url=url,
        headers=headers,
    )
    data = response_body.json()
    print("data",response_body.json())
    response = user_community_status(data['active'])
    print("accepted_invitation", True)
    return response

def user_community_status(status):
    response = False
    if status == True:
        response = True 
    return response

def delete_post(channel, post_id):
    if channel.is_community_required:
        community_id = channel.journryspace.community_id
        print(community_id)
        community_id = community_id
        
        url = "https://app.circle.so/api/v1/posts/"+str(post_id)+"?community_id="+str(community_id)
        headers = {
            'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
        }
        response_body = requests.delete(
            url=url,
            headers=headers,

        )
        data = response_body.json()
        print(data)
    return True



def CommunityAllSpaces(community_id):
    all_spaces = []
    group_space = []
    space_group = space_groups(community_id)
    spae = spaces(community_id)
    # space_group_df = pd.DataFrame.from_dict(space_group, orient="index")
    space_df = pd.DataFrame(spae)
    # print(space_df)
    for space_group in space_group:
        print(space_group['name'])
        all_group_spaces = space_df[space_df['space_group_id'].isin([space_group['id']])]
        all_spaces_list = []
        for index,row in all_group_spaces.iterrows():
            all_spaces_list.append({
                "name":row['name'] if row['name'] else "",
                "url":row['url'],
                "is_private":row['is_private']
            })
        all_spaces.append({
            "space_group_name":space_group['name'],
            "space":all_spaces_list
        })
    return all_spaces

def get_files(files, learning_journal_create):
    if files:
        image_type = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif']
        for file in files:
            print("file.content_type", file.content_type)
            if file.content_type in image_type:
                LearningJournalsAttachment.objects.create(post=learning_journal_create, image_upload=file, upload_for="Post")
            else:
                LearningJournalsAttachment.objects.create(post=learning_journal_create, file_upload=file, upload_for="Post")
    return True

def journal_push_notification(user, journey_id, journal_name, journal_type):
    mentor = AssignMentorToUser.objects.filter(
        user=user, journey__id=journey_id, is_assign=True).first()

    if mentor:
        mentor = mentor.mentor
        description = f"""Hi {mentor.first_name} {mentor.last_name}!
        Your Mentee,{user.first_name} {user.last_name} has just posted a {journal_type} Journal {journal_name} for your review """

        context = {
            "screen": "Journal",
        }
        send_push_notification(mentor, 'New Journal Posted', description, context)
    return True