from django.db.models.query_utils import Q
import requests
from apps.atpace_community.models import SpaceMembers
import sys
from apps.users.models import User, UserTypes
from io import BytesIO
from django.core import files

headers = {"Authorization": "Token TeWPTHJrtyjdXbH8qUva4G4g"}
user_type = UserTypes.objects.get(type="Learner")

def circle_space_group(community_id, space_group_id):
    url = f"http://app.circle.so/api/v1/space_groups/{space_group_id}?community_id={community_id}"
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        print(response.json())
        return sys.exit()
    return response.json()

def circle_space(community_id, space_id):
    url = f"http://app.circle.so/api/v1/spaces/{space_id}?community_id={community_id}"
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        print(response.json())
        return sys.exit()
    return response.json()

def circle_member(page):
    url = f"http://app.circle.so/api/v1/community_members?status=active&page={page}&per_page=100"
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        print(response.json())
        return sys.exit()
    return response.json()

def circle_member_search(community_id, email, space, space_group):
    print("email", email)
    try:
        user = User.objects.get(email=email)
    except Exception:
        url = f"https://app.circle.so/api/v1/community_members/search?community_id={community_id}&email={email}"
        response = requests.get(url=url, headers=headers)
        resp = response.json()
        if response.status_code != 200 or resp['success']==False:
            print(response.json())
            return False
        create_member(response.json(), space, space_group)
    space_member = SpaceMembers.objects.get(email=email, space=space, space_group=space_group)
    return space_member.user

def circle_post(community_id, space_id):
    print(f"page 1\n")
    url = f"http://app.circle.so/api/v1/posts?per_page=1000&page=1&community_id={community_id}&space_id={space_id}"
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        print(response.text)
        return sys.exit()
    return response.json()

def circle_post_comments(community_id, space_id, post_id):
    url = f"http://app.circle.so/api/v1/comments?community_id={community_id}&space_id={space_id}&post_id={post_id}"
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        print(response.json())
        return sys.exit()
    return response.json()

def circle_parent_comment(community_id, comment_id):
    url = f"http://app.circle.so/api/v1/comments/{comment_id}?community_id={community_id}"
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        print(response.json())
        return sys.exit()
    return response.json()

def cover_file_name(cover_image):
    return str(cover_image).split("/")[-1] if ".jpg" in str(cover_image) or ".png" in str(cover_image) or ".jpeg" in str(cover_image) else str(cover_image).split("/")[-1] + ".png"

def upload_cover_images(cover_image):
    response = requests.get(cover_image)
    response.raw.decode_content = True
    if response.status_code == 200:
        fp = BytesIO()
        fp.write(response.content)
        return cover_file_name(cover_image), files.File(fp)
    return None

def create_member(member, space, space_group):
    print("space_members_data['avatar_url'] ", member['avatar_url'])
    try:
        print(member['email'])
        user = User.objects.get(Q(username=member['email']) | Q(email=member['email']))
        if member['avatar_url'] and "secure.gravatar.com" not in str(member['avatar_url']):
            file_name, profile_image = upload_cover_images(member['avatar_url'])
            user.avatar.save(file_name, profile_image)
    except User.DoesNotExist:
        print("last name ",member['last_name'])
        last_name = member['last_name'] or ''
        headline = member['headline'] or ''
        bio = member['bio'] or ''
        user = User.objects.create(first_name=member['first_name'], last_name=last_name, email=member['email'], profile_heading=headline, about_us=bio,
            linkedin_profile=member['linkedin_url'], username=member['email'])
        if member['avatar_url'] and "secure.gravatar.com" not in str(member['avatar_url']):
            file_name, profile_image = upload_cover_images(member['avatar_url'])
            user.avatar.save(file_name, profile_image)
        user.created_at=member['created_at']
        user.updated_at=member['updated_at']
        user.save()
        user.userType.add(user_type.pk)

    try:
        SpaceMembers.objects.get(user=user, email=member['email'], space=space, space_group=space_group)
        return False
    except SpaceMembers.DoesNotExist:
        SpaceMembers.objects.create(user=user, space=space, space_group=space_group, is_joined=True, email=member['email'], 
                invitation_status="Accept", created_at=member['created_at'], updated_at=member['updated_at'])
    return True