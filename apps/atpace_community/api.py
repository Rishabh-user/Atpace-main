from datetime import timedelta, datetime
from bs4 import BeautifulSoup
import re
from ravinsight.web_constant import BASE_URL
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from django.db.models import Count
from apps.leaderboard.views import send_push_notification
from rest_framework.response import Response
from rest_framework import status
from ravinsight import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.atpace_community.models import Attachments, Event, Comment, Post, Report, SavedPost, Search, SpaceGroups, SpaceMembers, Spaces, likes, UserPinnedPost, ContentToReview
from apps.atpace_community.serializers import CommentSerializer, InviteLinkSerializer, LikeSerializer, PostSerializer, ReportSerializer, EventSerializer, SavedPostSerializer, SpaceGroupSerializer, SpaceMemberSerializer, SpaceSerializer, PinnedPostSerializer, ApproveRejectContentSerializer, UsersSerializer, SpacesSerializer, SpaceMembersSerializer, PostsSerializer, EventsSerializer, CommentsSerializer, LikessSerializer, \
    AttachmentsSerializer, SavedPostSerializer, UserPinnedPostsSerializer, ContentToReviewsSerializer, CompanySerializer, ReportSerializer, NotificationSettingsSerializer, ChatSerializer, RoomSerializer, SpaceGroupsSerializer
from apps.atpace_community.utils import Pagination, EventData, Postcomments, replace_links_with_anchor_tags, all_posts, avatar, cover_images, delete_post, get_text, like_post_comment, post_comment_file, post_comment_images, post_filter, public_post_response, response_post, send_invite_user_mail, send_new_post_mail, send_report_post_mail, space_filter, time_ago, time_ago_days, user_comment, user_spaces, whatsapp_message, aware_time, icons
from apps.utils.utils import check_inappropriate_words
from apps.push_notification.models import AtPaceNotification, notifye
from apps.users.models import Company, User, UserTypes, Collabarate
from apps.vonage_api.utils import comment_recorded_confirmation, community_update
from ravinsight.constants import report_types
from apps.users.templatetags.tags import get_chat_room
from apps.chat_app.models import Chat, Room
from apps.api.utils import check_valid_user, update_boolean
from apps.users.utils import lives_streaming_room, local_time, convert_to_local_time, convert_to_utc, strf_format

def send_post_notification(user, title, post, description):
    context = {
        "screen": "Post",
        "navigationPayload": {
            "postId": str(post.id)
        }
    }
    send_push_notification(user, title, description, context)
    return True


class GroupSpaces(APIView):
    """
    List all Spaces, or create a new Space.
    """
    serializer_class = SpaceGroupSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            user = check_valid_user(user_id)
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_group = SpaceGroups.objects.filter(is_active=True, is_delete=False)
        data = []
        for group in space_group:
            allspace = Spaces.objects.filter(space_group=group, is_active=True,
                                             is_delete=False, is_hidden=False, hidden_from_non_members=False)
            spaces = []
            for space in allspace:
                user_joined = None
                if user_id:
                    user_joined = SpaceMembers.objects.filter(
                        user=user, space=space, is_active=True, is_delete=False, is_joined=True).first()
                if space.privacy == "Public" or user_joined:
                    spaces.append({
                        "id": space.id,
                        "title": space.title,
                        "descritpion": space.description,
                        "cover_image": cover_images(space),
                        "slug": space.slug,
                        "space_group_id": space.space_group.id,
                        "space_group": space.space_group.title,
                        "privacy": space.privacy,
                        "is_hidden": space.is_hidden,
                        "hidden_from_non_members": space.hidden_from_non_members,
                        "is_active": space.is_active,
                        "is_delete": space.is_delete,
                        "space_type": space.space_type,
                        "created_by": space.created_by.username,
                        "created_by_id": space.created_by.id,
                        "updated_by_id": space.update_by if space.update_by else '',
                        "created_at": local_time(space.created_at),
                    })

            data.append({
                "id": group.id,
                "name": group.title,
                "description": group.description,
                "slug": group.slug,
                "cover_image": cover_images(group),
                "privacy": group.privacy,
                "hidden": group.is_hidden,
                "hidden_from_non_members": group.hidden_from_non_members,
                "is_active": group.is_active,
                "is_delete": group.is_delete,
                "is_created_by": group.created_by.username,
                "created_by_id": group.created_by.id,
                "updated_by_id": group.update_by if group.update_by else '',
                "created_at": local_time(group.created_at),
                "spaces": spaces,
                # "members": member_list,
                "user_id": user_id
            })
        response = {
            "message": "All Group Spaces",
            "success": True,
            "data": {
                "group_spaces": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        user_type = UserTypes.objects.filter(type__in=['Admin', 'ProgramManager'])
        if serializer.is_valid():
            try:
                user = User.objects.get(id=request.data['user_id'], userType__in=user_type)
            except User.DoesNotExist:
                response = {"message": "You are not authorized to create this group", "success": False}
                return Response(response, status=status.HTTP_404_NOT_FOUND)
            title = request.data['title']
            description = request.data['description']
            cover_image = request.data['cover_image']
            privacy = request.data['privacy']
            is_hidden = update_boolean(request.data['is_hidden'])
            hidden_from_non_members = update_boolean(request.data['hidden_from_non_members'])
            is_active = update_boolean(request.data['is_active'])
            space_group = SpaceGroups.objects.create(title=title, description=description, cover_image=cover_image, privacy=privacy,
                                                     is_hidden=is_hidden, hidden_from_non_members=hidden_from_non_members, is_active=is_active, created_by=user)
            data = {
                "id": space_group.id,
                "name": space_group.title,
                "description": space_group.description,
                "slug": space_group.slug,
                "cover_image": cover_images(space_group),
                "privacy": space_group.privacy,
                "created_at": local_time(space_group.created_at),
                "created_by_id": space_group.created_by.id,
            }
            response = {
                "message": "Group Space Created",
                "success": True,
                "data": {
                    "group_space": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetGroupSpace(APIView):
    permission_classes = [AllowAny]
    serializer_class = SpaceGroupSerializer

    def delete(self, request, *args, **kwargs):
        user_type = UserTypes.objects.filter(type__in=['Admin', 'ProgramManager'])
        try:
            user = User.objects.get(id=request.data['user_id'], userType__in=user_type)
        except User.DoesNotExist:
            response = {"message": "You are not authorized to delete this group", "success": False}
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        space_group = SpaceGroups.objects.filter(id=self.kwargs['space_group_id'])
        if not space_group:
            return Response({"message": "SpaceGroup not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_group.update(is_active=False, is_delete=True, deleted_by=user.id)
        return Response({"message": "SpaceGroup successfully deleted", "success": True}, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        user_type = UserTypes.objects.filter(type__in=['Admin', 'ProgramManager'])
        if serializer.is_valid():
            try:
                user = User.objects.get(id=request.data['user_id'], userType__in=user_type)
            except User.DoesNotExist:
                response = {"message": "You are not authorized to update this group", "success": False}
                return Response(response, status=status.HTTP_404_NOT_FOUND)
            title = request.data['title']
            description = request.data['description']
            cover_image = request.data['cover_image']
            privacy = request.data['privacy']
            is_hidden = request.data['is_hidden']
            hidden_from_non_members = request.data['hidden_from_non_members']
            is_active = request.data['is_active']
            space_group = SpaceGroups.objects.filter(id=self.kwargs['space_group_id'])
            if not space_group:
                return Response({"message": "SpaceGroup not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            space_group.update(title=title, description=description, cover_image=cover_image, privacy=privacy, update_by=user.id,
                               is_hidden=is_hidden, hidden_from_non_members=hidden_from_non_members, is_active=is_active)
            space_group = space_group.first()
            data = {
                "id": space_group.id,
                "name": space_group.title,
                "description": space_group.description,
                "slug": space_group.slug,
                "cover_image": cover_images(space_group),
                "privacy": space_group.privacy,
                "created_at": local_time(space_group.created_at),
                "created_by_id": space_group.created_by.id,
                "updated_by": f"{user.first_name} {user.last_name}",
                "updated_by_id": space_group.update_by if space_group.update_by else '',
            }
            response = {
                "message": "Group Space Created",
                "success": True,
                "data": {
                    "group_space": data,
                }
            }
            return Response(response, status=status.HTTP_205_RESET_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllSpaces(APIView):
    """
    List all Spaces, or create a new Space.
    """
    serializer_class = SpaceSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user_id = self.request.query_params.get('user_id')
        allspaces = Spaces.objects.filter(is_active=True, is_delete=False)
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if "Admin" not in ','.join([type.type for type in user.userType.all()]):
            allspaces = allspaces.filter(created_by=user)

        # if user_id:
        #     user = User.objects.get(pk=user_id)
        #     if user.userType == "Admin":
        #         allspaces = allspaces
        #     else:
        #         allspaces = allspaces.filter(is_active=True, is_delete=False,
        #                                      is_hidden=False, hidden_from_non_members=False)
        # else:
        #     allspaces = allspaces.filter(is_active=True, is_delete=False,
        #                                  is_hidden=False, hidden_from_non_members=False)
        spaces = []
        for space in allspaces:
            member_list = []
            spacemember = SpaceMembers.objects.filter(space=space, is_active=True, is_delete=False, is_joined=True)

            for member in spacemember:
                member_list.append({
                    "id": member.id,
                    "user_id": member.user.id,
                    "name": f"{member.user.first_name} {member.user.last_name}",
                    "email": member.email,
                    "user_type": member.user_type,
                    "is_joined": member.is_joined,
                    "is_active": member.is_active,
                    "heading": member.user.profile_heading,
                    "user_profile_image": avatar(member.user)
                })
            spaces.append({
                "id": space.id,
                "user_id": user_id,
                "title": space.title,
                "descritpion": space.description,
                "cover_image": cover_images(space),
                "slug": space.slug,
                "space_group_id": space.space_group.id,
                "space_group": space.space_group.title,
                "privacy": space.privacy,
                "is_default": space.is_default,
                "is_hidden": space.is_hidden,
                "hidden_from_non_members": space.hidden_from_non_members,
                "is_active": space.is_active,
                "is_delete": space.is_delete,
                "created_by": space.created_by.username,
                "created_at": space.created_at,
                "heading": space.created_by.profile_heading,
                "user_profile_image": avatar(space.created_by),
                "members": member_list,
            })

        response = {
            "message": "All Spaces",
            "success": True,
            "data": {
                "spaces": spaces,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            type = self.request.query_params.get('type')
            member_type = "Admin"
            user_type = UserTypes.objects.filter(type__in=['Admin', 'ProgramManager'])
            try:
                user = User.objects.get(id=request.data['user_id'], userType__in=user_type)
            except User.DoesNotExist:
                response = {"message": "User does not exists", "success": False}
                return Response(response, status=status.HTTP_404_NOT_FOUND)
            if type == "ProgramManager":
                member_type = "Moderator"
            title = request.data['title']
            description = request.data['description']
            cover_image = request.data['cover_image']
            privacy = request.data['privacy']
            space_type = request.data['space_type']
            is_hidden = update_boolean(request.data['is_hidden'])
            hidden_from_non_members = update_boolean(request.data['hidden_from_non_members'])
            # is_default = request.data['is_default']
            is_active = update_boolean(request.data['is_active'])
            try:
                group = SpaceGroups.objects.get(id=request.data['space_group_id'])
            except SpaceGroups.DoesNotExist:
                response = {"message": "Space Group does not exists", "success": False}
                return Response(response, status=status.HTTP_404_NOT_FOUND)

            space = Spaces.objects.create(title=title, description=description, cover_image=cover_image, privacy=privacy, space_group=group,
                                          is_hidden=is_hidden, hidden_from_non_members=hidden_from_non_members, is_active=is_active, created_by=user)

            SpaceMembers.objects.create(user=user, space=space, space_group=group, is_joined=True,
                                        email=user.email, invitation_status="Accept", user_type=member_type)

            data = {
                "id": space.id,
                "name": space.title,
                "description": space.description,
                "slug": space.slug,
                "space_group": space.space_group.title,
                "cover_image": cover_images(space),
                "privacy": space.privacy,
                "is_default": space.is_default,
                "created_at": local_time(space.created_at),
                "created_by": space.created_by.username,
                "created_by_id": space.created_by.id,
                "member_type": member_type
            }
            response = {
                "message": "Space Created",
                "success": True,
                "data": {
                    "group_space": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateSpaces(APIView):
    """
    Retrieve, update or delete a Spaces.
    """
    serializer_class = SpaceSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        if user_id := self.request.query_params.get('user_id'):
            user = check_valid_user(user_id)
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            space = Spaces.objects.get(id=self.kwargs['space_id'])
        except Spaces.DoesNotExist:
            return Response({"message": "Space does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "id": space.id,
            "space_group_id": space.space_group.id,
            "space_group": space.space_group.title,
            "name": space.title,
            "description": space.description,
            "slug": space.slug,
            "cover_image": cover_images(space),
            "privacy": space.privacy,
            "created_at": local_time(space.created_at),
        }
        response = {
            "message": "Space Get Data",
            "success": True,
            "data": {
                "group_space": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        user_type = UserTypes.objects.filter(type__in=['Admin', 'ProgramManager'])
        try:
            user = User.objects.get(id=request.data['user_id'], userType__in=user_type)
        except User.DoesNotExist:
            response = {"message": "User does not exists", "success": False}
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        space = Spaces.objects.filter(id=self.kwargs['space_id'])
        if serializer.is_valid():
            title = request.data['title']
            description = request.data['description']
            cover_image = request.data['cover_image']
            privacy = request.data['privacy']
            is_hidden = request.data['is_hidden']
            hidden_from_non_members = request.data['hidden_from_non_members']
            is_default = request.data['is_default']
            is_active = request.data['is_active']
            try:
                group = SpaceGroups.objects.get(id=request.data['space_group_id'])
            except SpaceGroups.DoesNotExist:
                response = {"message": "Space Group does not exists", "success": False}
                return Response(response, status=status.HTTP_404_NOT_FOUND)

            space.update(title=title, description=description, cover_image=cover_image, privacy=privacy, space_group=group, is_default=is_default,
                         update_by=user.id, is_hidden=is_hidden, hidden_from_non_members=hidden_from_non_members, is_active=is_active)
            space = space.first()
            data = {
                "id": space.id,
                "name": space.title,
                "description": space.description,
                "slug": space.slug,
                "space_group": space.space_group.title,
                "cover_image": cover_images(space),
                "privacy": space.privacy,
                "updated_by": f"{user.first_name} {user.last_name}",
                "updated_by_id": space.update_by if space.update_by else '',
                "created_at": local_time(space.created_at),
            }
            response = {
                "message": "Space Updated",
                "success": True,
                "data": {
                    "group_space": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user_type = UserTypes.objects.filter(type__in=['Admin', 'ProgramManager'])
        user_id = self.request.query_params.get('user_id')
        if user_id:
            try:
                user = User.objects.get(pk=user_id, userType__in=user_type)
            except User.DoesNotExist:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            space = Spaces.objects.filter(id=self.kwargs['space_id'])
            if not space:
                return Response({"message": "Space not found", "user_id": user_id, "success": False}, status=status.HTTP_404_NOT_FOUND)
            space.update(is_active=False, is_delete=True, deleted_by=user.id)
            return Response({"message": "Space successfully deleted", "success": True}, status=status.HTTP_200_OK)
        return Response({"message": "Unknown User", "user_id": user_id, "success": False}, status=status.HTTP_404_NOT_FOUND)


class UserSpaces(APIView):
    permission_classes = [AllowAny]
    serializer_class = SpaceMemberSerializer

    def get(self, request, *args, **kwargs):
        spaces = Spaces.objects.filter(is_active=True, is_delete=False, space_type='Post')
        member_spaces = SpaceMembers.objects.filter(
            user__pk=self.kwargs['user_id'], space__in=spaces, is_active=True, is_delete=False, is_joined=True)
        data = user_spaces(member_spaces)
        response = {
            "message": "Space Get Data",
            "success": True,
            "data": {
                "user_space": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                spacegroup = SpaceGroups.objects.get(id=request.data['space_group_id'])
            except SpaceGroups.DoesNotExist:
                return Response({"message": "SpaceGroup is not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                space = Spaces.objects.get(id=request.data['space_id'], space_group=spacegroup)
            except Spaces.DoesNotExist:
                return Response({"message": "Space with this group not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user_type = request.data['user_type']
            try:
                member = SpaceMembers.objects.get(user=user, space=space, space_group=spacegroup)
                if member.is_joined == True:
                    return Response({"message": "User Already joined", "success": False}, status=status.HTTP_208_ALREADY_REPORTED)
                elif member.is_active and not member.is_delete:
                    member.is_joined = True
                member.save()
            except SpaceMembers.DoesNotExist:
                member = SpaceMembers.objects.create(user=user, user_type=user_type, space=space, space_group=spacegroup,
                                                     is_joined=True, email=user.email, invitation_status="Accept")

            data = {
                "user_id": member.user.id,
                "space_id": member.space.id,
                "space_name": member.space.title,
                "full_name": member.user.first_name+" "+member.user.last_name,
                "email": member.email,
                "community_user_type": member.user_type,
                "is_joined": member.is_joined,
                "is_active": member.is_active,
                "created_at": local_time(member.created_at),
                "user_profile_image": avatar(member.user),
            }

            response = {
                "message": "User joined space",
                "success": True,
                "data": {
                    "user_space": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpaceUser(APIView):
    permission_classes = [AllowAny]
    serializer_class = SpaceMemberSerializer

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            space = Spaces.objects.get(id=self.kwargs['space_id'])
        except Spaces.DoesNotExist:
            return Response({"message": "Space_id not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_member = SpaceMembers.objects.filter(
            user=user, space=space, is_joined=True, is_active=True, is_delete=False)
        posts = Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False)
        space_post = all_posts(posts, "all", user, offset=self.request.query_params.get('timezone',None))
        member_list = []
        if space_member is not None:
            for member in space_member:
                member_list.append({
                    "id": member.id,
                    "user_id": member.user.id,
                    "name": member.user.first_name+" "+member.user.last_name,
                    "email": member.email,
                    "user_type": member.user_type,
                    "is_joined": member.is_joined,
                    "is_active": member.is_active,
                    "heading": member.user.profile_heading,
                    "user_profile_image": avatar(member.user),
                })
            data = {
                "id": space.id,
                "title": space.title,
                "slug": space.slug,
                "description": space.description,
                "space_group_id": space.space_group.id,
                "space_group": space.space_group.title,
                "cover_image": cover_images(space),
                "privacy": space.privacy,
                "is_default": space.is_default,
                "space_member": member_list,
                "space_posts": space_post,
                "created_at": local_time(space.created_at),
            }
        else:
            return Response({"message": "No data found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        response = {
            "message": "Space Get Data",
            "success": True,
            "data": {
                "user_space": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user_type = request.data['user_type']
            try:
                space_group = SpaceGroups.objects.get(id=request.data['space_group_id'])
            except SpaceGroups.DoesNotExist:
                return Response({"message": "Space_group not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                space = Spaces.objects.get(id=request.data['space_id'], space_group=space_group)
            except Spaces.DoesNotExist:
                return Response({"message": "Space with this group not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            space_member = SpaceMembers.objects.filter(
                space=space, space_group=space_group, user=user, is_active=True, is_delete=False)
            if not space_member:
                return Response({"message": "No space found for the member", "success": False}, status=status.HTTP_404_NOT_FOUND)
            member = space_member.first()
            if member.is_active and not member.is_delete:
                space_member.update(is_joined=True)
            else:
                space_member.update(is_joined=True, is_active=True, is_delete=False)
            return Response({"message": "Space member updated", "success": True}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = User.objects.get(pk=self.kwargs['user_id'])
        space = Spaces.objects.get(id=self.kwargs['space_id'])
        space_member = SpaceMembers.objects.filter(is_joined=True, user=user, space=space)
        if not space_member:
            return Response({"message": "No member found for the space", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_member.update(is_joined=False)
        return Response({"message": "Space member removed", "success": True}, status=status.HTTP_200_OK)


class UserPosts(APIView):
    permission_classes = [AllowAny]
    serializer_class = PostSerializer
    pagination_class = Pagination

    def get(self, request, *args, **kwargs):
        timezone = request.query_params.get('timezone', None)
        if timezone is None:
            return Response({"message": "timezone is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        elif timezone == "undefined":
            return Response({"message": "Please Update Your Application",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_memeber = SpaceMembers.objects.filter(user=user, is_active=True, is_delete=False)
        spaces = []
        if request.query_params.get('space_id'):
            space_id = request.query_params.get('space_id')
            try:
                space = Spaces.objects.get(id=space_id)
            except Spaces.DoesNotExist:
                return Response({"message": "Space not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            space_memeber = space_memeber.filter(space=space)
        for member in space_memeber:
            spaces.append(member.space)
        posts = Post.objects.filter(created_by=member.user, space__in=spaces,
                                    inappropriate_content=False, is_active=True, is_delete=False)
        if not posts:
            return Response({"message": "no posts available", "success": True}, status=status.HTTP_200_OK)
        data = all_posts(posts, "all", user, offset=timezone)
        pagination = ''
        obj = isinstance(data, list)
        if obj:
            paginator = Paginator(data, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }
        response = {
            "message": "Get Posts",
            "success": True,
            "data": {
                "pages": pagination,
                "All_Posts": pages.object_list if obj else data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            title = request.data['title']
            body = request.data['Body']
            # body = replace_links_with_anchor_tags(body) if ('<p>http' in body) or (re.search("(^https?://[^\s]+)", body)) else body
            body = replace_links_with_anchor_tags(body)
            is_comments_enabled = request.data['is_comments_enabled']
            is_liking_enabled = request.data['is_liking_enabled']
            notify_space_members = request.data['notify_space_members']
            try:
                space_group = SpaceGroups.objects.get(id=request.data['space_group_id'])
            except SpaceGroups.DoesNotExist:
                return Response({"message": "Space_group not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                space = Spaces.objects.get(id=request.data['space_id'], space_group=space_group)
            except Spaces.DoesNotExist:
                return Response({"message": "Space with this group not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                member_space = SpaceMembers.objects.get(user=user, space=space)
            except SpaceMembers.DoesNotExist:
                return Response({"message": "You're not authorized to post on this space", "success": False}, status=status.HTTP_404_NOT_FOUND)
            post = Post.objects.create(title=title, Body=body, notify_space_members=notify_space_members,
                                       is_comments_enabled=is_comments_enabled, is_liking_enabled=is_liking_enabled, space=space, space_group=space_group, created_by=user)
            if data.get('image_upload') and data.get('file_upload'):
                image_file = request.FILES.getlist('image_upload')
                file_upload = request.FILES.getlist('file_upload')
                for image in image_file:
                    Attachments.objects.create(post=post, image_upload=image, upload_for="Post")
                for file in file_upload:
                    Attachments.objects.create(post=post, file_upload=file, upload_for="Post")

            elif data.get('image_upload'):
                image_file = request.FILES.getlist('image_upload')
                for image in image_file:
                    Attachments.objects.create(post=post, image_upload=image, upload_for="Post")
            elif data.get('file_upload'):
                file_upload = request.FILES.getlist('file_upload')
                for file in file_upload:
                    Attachments.objects.create(post=post, file_upload=file, upload_for="Post")

            if data.get('cover_image'):
                cover_image = request.FILES['cover_image']
                post.cover_image = cover_image
            if data.get('post_type'):
                post_type = request.data['post_type']
                post.post_type = post_type
            if data.get('tags'):
                tags = request.data['tags']
                post.tags = tags
            post.save()

            cleantext = BeautifulSoup(body, "html.parser").text
            if words := check_inappropriate_words(cleantext):
                Post.objects.filter(id=post.id).update(inappropriate_content=True)
                ContentToReview.objects.create(title="Inappropriate Content", post=post, profanity_words=",".join(words),
                                               posted_on="Post", user=user, space=space)
                print(f"check_text: {words}")
            else:
                user_query_set = SpaceMembers.objects.filter(~Q(user=user), space=space)
                if user_query_set:
                    user_list = [member.user for member in user_query_set]
                    if len(user_list) > 0:
                        notifye.send(sender=user, to_user=user_list, by_user=user, verb=title, action_id={"post_id": str(post.id)},
                                    description=body, notification_types="Post", category="AtPace_Community")
                        for member in user_list:
                            description = f"""Hi {member.first_name} {member.last_name}!
                            There has been a new topic posted in the {space.title} group! Come check out the content, perhaps it may lead to some new discoveries!"""

                            context = {
                                "screen": "Community",
                            }
                            send_push_notification(member, 'New Post', description, context)
                            if member.phone and member.is_whatsapp_enable:
                                community_update(member, post)
                            else:
                                print("no phone number exist")
                        user_email_list = [user.email for user in user_list]

            # send_new_post_mail(user, post, user_email_list)
            data = response_post(post.id)
            response = {
                "message": "Post Created",
                "success": True,
                "data": {
                    "post_data": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateEventPost(APIView):
    permission_classes = [AllowAny]
    serializer_class = EventSerializer
    pagination_class = Pagination

    def get(self, request, *args, **kwargs):
        timezone = request.query_params.get('timezone', None)
        if timezone is None:
            return Response({"message": "timezone is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        elif timezone == "undefined":
            return Response({"message": "Please Update Your Application",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        if not request.query_params.get('space_id'):
            return Response({"message": "space_id is required in query_params", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        filter_by = self.request.query_params.get('order_by') or None
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        is_joined = False
        space_member_type = ''
        if request.query_params.get('space_id'):
            space_id = request.query_params.get('space_id')
            try:
                space = Spaces.objects.get(id=space_id, space_type="Event")
            except Spaces.DoesNotExist:
                return Response({"message": "Space not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

        space_member = SpaceMembers.objects.filter(
            user=user, space=space, is_joined=True, is_active=True, is_delete=False)
        if space_member:
            space_member_type = space_member.first().user_type
            is_joined = True

        posts = Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False)
        if not posts:
            response = {
                "message": "no posts available",
                "success": True,
                "data": {
                    "space_id": space.id if space else None,
                    "space_name": space.title if space else None,
                    "space_privacy": space.privacy if space else None,
                    "space_group_id": space.space_group.id if space else None,
                    "space_group_name": space.space_group.title if space else None,
                    "space_type": space.space_type if space else None,
                    "public_post": [],
                    "space_member_type": space_member_type,
                    "is_joined": is_joined
                }
            }
            return Response(response, status=status.HTTP_200_OK)

        events = Event.objects.filter(post_id__in=posts).order_by('start_time')
        if filter_by == "upcoming":
            events = events.filter(end_time__gt=datetime.now())
        elif filter_by == "past":
            events = events.filter(end_time__lt=datetime.now())

        event_list = [response_post(event.post_id.id, filter_by, offset=timezone) for event in events]
        data = event_list
        pagination = ''
        obj = isinstance(data, list)
        if obj:
            paginator = Paginator(data, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }
        response = {
            "message": "Get Events",
            "success": True,
            "data": {
                "pages": pagination,
                "space_id": space.id if space else None,
                "space_name": space.title if space else None,
                "space_privacy": space.privacy if space else None,
                "space_group_id": space.space_group.id if space else None,
                "space_group_name": space.space_group.title if space else None,
                "space_type": space.space_type if space else None,
                "public_post": pages.object_list if obj else data,
                "space_member_type": space_member_type,
                "is_joined": is_joined
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        print("EVETN FILES", request.FILES)
        data = request.data
        print("ATTENDEESS ** ", data['attendees'])
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            title = request.data['title']
            body = request.data['Body']
            try:
                space = Spaces.objects.get(id=request.data['space_id'])
            except Spaces.DoesNotExist:
                return Response({"message": "Space with this group not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            space_group = space.space_group
            try:
                member_space = SpaceMembers.objects.get(~Q(user_type='Member'), user=user, space=space)
            except SpaceMembers.DoesNotExist:
                return Response({"message": "You're not authorized to create event on this space", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
            start_time = convert_to_utc(request.data['start_time'].replace('T',' ')+":00", self.request.data['timezone'])
            end_time = convert_to_utc(request.data['end_time'].replace('T',' ')+":00", self.request.data['timezone'])

            if Event.objects.filter(Q(start_time__exact=start_time) | (Q(start_time__gt=start_time) & Q(start_time__lt=end_time))).exists():
                return Response({"message": "Event with this datetime already exist", "success": False}, status=status.HTTP_400_BAD_REQUEST)
            post = Post.objects.create(title=title, Body=body, space=space, space_group=space_group, created_by=user)
            if data.get('image_upload') and data.get('file_upload'):
                image_file = request.FILES.getlist('image_upload')
                file_upload = request.FILES.getlist('file_upload')
                for image in image_file:
                    Attachments.objects.create(post=post, image_upload=image, upload_for="Post")
                for file in file_upload:
                    Attachments.objects.create(post=post, file_upload=file, upload_for="Post")
            elif data.get('image_upload'):
                image_file = request.FILES.getlist('image_upload')
                for image in image_file:
                    Attachments.objects.create(post=post, image_upload=image, upload_for="Post")
            elif data.get('file_upload'):
                file_upload = request.FILES.getlist('file_upload')
                for file in file_upload:
                    Attachments.objects.create(post=post, file_upload=file, upload_for="Post")

            if data.get('bg_image'):
                bg_image = request.FILES['bg_image']
                post.bg_image = bg_image
            if data.get('cover_image'):
                cover_image = request.FILES['cover_image']
                post.cover_image = cover_image
            if data.get('post_type'):
                post_type = request.data['post_type']
                post.post_type = post_type
            if data.get('tags'):
                tags = request.data['tags']
                post.tags = tags
            if data.get('is_comments_enables'):
                post.is_comments_enabled = request.data['is_comments_enabled']

            if data.get('is_liking_enabled'):
                post.is_liking_enabled = request.data['is_liking_enabled']

            if data.get('notify_space_members'):
                notify_space_members = request.data['notify_space_members']
                post.notify_space_members = notify_space_members
            post.save()

            location = request.data['location']
            speaker = request.data['speaker']
            try:
                speaker = SpaceMembers.objects.get(user=speaker, space=space)
            except SpaceMembers.DoesNotExist:
                return Response({"message": "Speaker does not exist on this space", "success": False}, status=status.HTTP_404_NOT_FOUND)

            frequency = request.data['frequency']
            if location == 'URl (Zoom, YouTube Live)':
                event_url = request.data['event_url']
            else:
                event_url = ""
            #print(f"event_url: {event_url}")
            event = Event.objects.create(post_id=post, start_time=start_time, end_time=end_time,
                                         location=location, host=speaker.user, frequency=frequency)

            description = f"""Hi {speaker.user.first_name} {speaker.user.last_name}!
            You have been assigned to an Event as a speaker:
            {title} {strf_format(convert_to_local_time(start_time, request.data['timezone']))}"""
            print("description", description)
            context = {
                "screen": "Calendar",
                "navigationPayload":{
                "meet_id": str(event.id),
                "meet_type": 'Event'
                }
            }
            send_push_notification(speaker.user, 'Event Assigned As Speaker', description, context)
            if data.get('is_tbd'):
                event.is_tbd = request.data['is_tbd']
            if data.get('is_location_hidden'):
                event.is_location_hidden = request.data['is_location_hidden']
            attendees = request.data['attendees']
            attendees = attendees.split(",")
            for attendee in attendees:
                event.attendees.add(attendee)
                user = User.objects.get(id=attendee)
                description = f"""Hi {user.first_name} {user.last_name}!
                You have been assigned to an Event as an attendee:
                {title} {strf_format(convert_to_local_time(start_time, request.data['timezone']))}
                Would you like to RSVP now?"""
                context = {
                    "screen": "Calendar",
                    "navigationPayload":{
                        "meet_id": str(event.id),
                        "meet_type": 'Event'
                    }
                }
                send_push_notification(user, 'Event Assigned Attendance', description, context)

            # whatsapp_message(post, user)
            if data.get('notify_space_members'):
                if notify_space_members == True:
                    user_query_set = SpaceMembers.objects.filter(~Q(user=user), space=space)
                    if user_query_set:
                        user_list = [member.user for member in user_query_set]
                        if len(user_list) > 0:
                            notifye.send(sender=user, to_user=user_list, by_user=user, verb=title, action_id={"post_id": str(post.id)},
                                         description=body, notification_types="Event", category="AtPace_Community")
                        for member in user_list:
                            send_post_notification(member, title, post, get_text(post.Body))
                            if member.phone and member.is_whatsapp_enable:
                                community_update(member, post)
            
            if data.get('livestream'):
                if event_url == "":
                    meet, token = lives_streaming_room(post.title, "event",) # token is the meet_id here
                    if token == 400:
                        return Response({"message": meet['message'], "success": False}, status=status.HTTP_404_NOT_FOUND)
                    url_title = token
                    event.event_url = f"{BASE_URL}/config/dyte/{token}"
                    # print(f"event.event_url: {event.event_url}")
                else:
                    url_title = data['event_url']
                try:
                    collabarate = Collabarate.objects.create(title=post.title, description=post.Body, custom_url=event.event_url, speaker=event.host, url_title=url_title,start_time=event.start_time, end_time=event.end_time, type='LiveStreaming', is_active=True, created_by=event.host, add_to_community=True)
                except Exception as e:
                    print("Data", data)
                    print("EXception in query", e)
                    return Response({"message": "Collabarate with this title already exists!", "success": False}, status=status.HTTP_404_NOT_FOUND)
                for attendee in event.attendees.all():
                    collabarate.participants.add(attendee)
                collabarate.save()

                event.add_to_collabarate = True
                event.collabarate_id = collabarate.id
            event.save()

            data = response_post(post.id, filter_by=None, offset=self.request.data['timezone'])
            response = {
                "message": "Post Created",
                "success": True,
                "data": {
                    "post_data": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateEventPost(APIView):
    permission_classes = [AllowAny]
    serializer_class = EventSerializer
    pagination_class = Pagination

    def put(self, request, *args, **kwargs):
        data = request.data
        #print("data", data)
        post_id = self.kwargs['post_id']
        try:
            Post.objects.get(id=self.kwargs['post_id'])
        except Post.DoesNotExist:
            return Response({"message": "Invalid event id or not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            title = request.data['title']
            try:
                space = Spaces.objects.get(id=request.data['space_id'])
            except Spaces.DoesNotExist:
                return Response({"message": "Space with this group not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
            space_group = space.space_group
            try:
                SpaceMembers.objects.get(~Q(user_type='Member'), user=user, space=space)
            except SpaceMembers.DoesNotExist:
                return Response({"message": "You're not authorized to create event on this space", "success": False}, status=status.HTTP_404_NOT_FOUND)
            body = request.data['Body']
            post = Post.objects.filter(id=post_id)
            post.update(title=title, Body=body, space=space, space_group=space_group, created_by=user)
            post = post.first()
            if data.get('cover_image'):
                cover_image = request.FILES['cover_image']
                post.cover_image = cover_image
            if data.get('post_type'):
                post_type = request.data['post_type']
                post.post_type = post_type
            if data.get('tags'):
                tags = request.data['tags']
                post.tags = tags
            if data.get('is_comments_enables'):
                post.is_comments_enabled = request.data['is_comments_enabled']

            if data.get('is_liking_enabled'):
                post.is_liking_enabled = request.data['is_liking_enabled']

            if data.get('notify_space_members'):
                notify_space_members = request.data['notify_space_members']
                post.notify_space_members = notify_space_members
            post.save()
            print(request.data['start_time'])

            start_time = convert_to_utc(request.data['start_time'].replace('T',' ')+":00", self.request.data['timezone'])
            end_time = convert_to_utc(request.data['end_time'].replace('T',' ')+":00", self.request.data['timezone'])
            location = request.data['location']
            speaker = request.data['speaker']
            try:
                speaker = SpaceMembers.objects.get(user=speaker, space=space)
            except SpaceMembers.DoesNotExist:
                return Response({"message": "Speaker does not exist on this space", "success": False}, status=status.HTTP_404_NOT_FOUND)
            frequency = request.data['frequency']
            if location == 'URl (Zoom, YouTube Live)':
                event_url = request.data['event_url']
            else:
                event_url = ""
            event = Event.objects.filter(post_id=post)
            event.update(start_time=start_time, end_time=end_time,
                         location=location, host=speaker.user, frequency=frequency, event_url=event_url)
            event = event.first()
            if data.get('is_tbd'):
                event.is_tbd = request.data['is_tbd']
            if data.get('is_location_hidden'):
                event.is_location_hidden = request.data['is_location_hidden']

            attendees = request.data['attendees']
            attendees = attendees.split(",")
            attendees_list = [str(attendi.id) for attendi in event.attendees.all()]

            for attendee in attendees:
                if attendee not in attendees_list:
                    event.attendees.add(attendee)
            for attendi in attendees_list:
                if attendi not in attendees:
                    event.attendees.remove(attendi)
            event.save()

            # Updating event to livestream
            if event.add_to_collabarate:
                collabarate = Collabarate.objects.filter(id=event.collabarate_id)
                collabarate.update(title=post.title, description=post.Body, custom_url=event.event_url, speaker=event.host,
                                   start_time=event.start_time, end_time=event.end_time, type='LiveStreaming', is_active=True)
                collabarate = collabarate.first()
                participants_list = [str(attendi.id) for attendi in collabarate.participants.all()]
                for attendee in event.attendees.all():
                    if attendee not in participants_list:
                        collabarate.participants.add(attendee)
                for attendi in participants_list:
                    if attendi not in attendees:
                        collabarate.participants.remove(attendi)

            data = response_post(post.id, None, self.request.data['timezone'])
            response = {
                "message": "Post Created",
                "success": True,
                "data": {
                    "post_data": data,
                }
            }
            return Response(response, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPost(APIView):
    permission_classes = [AllowAny]
    serializer_class = PostSerializer

    def get(self, request, *args, **kwargs):
        timezone = request.query_params.get('timezone', None)
        if timezone is None:
            return Response({"message": "timezone is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        elif timezone == "undefined":
            return Response({"message": "Please Update Your Application",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        if user_id := self.request.query_params.get('user_id'):
            user = check_valid_user(user_id)
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        else:
            user = None
        try:
            post = Post.objects.get(id=self.kwargs['post_id'], is_active=True, is_delete=False)
        except Post.DoesNotExist:
            context = {
                "message": "Post not available",
                "success": False
            }
            return Response(context, status=status.HTTP_404_NOT_FOUND)
        updated_by = User.objects.filter(id=post.update_by).first()
        comments_list, attachments_list = [], []
        comments = Comment.objects.filter(post=post, parent_id=None,
                                          inappropriate_content=False, is_active=True, is_delete=False)
        is_saved = False
        if not user:
            is_saved = False
        else:
            saved_post = SavedPost.objects.filter(saved_by=user, is_saved=True,
                                                  post=post, is_active=True, is_delete=False).count()
            if saved_post > 0:
                is_saved = True
        total_comments = Comment.objects.filter(inappropriate_content=False,
                                                post=post, parent_id=None, comment_for="Post", is_active=True, is_delete=False).count()
        is_like, likess = like_post_comment(user=user, post=post, comment=None)
        if not comments:
            comments_list = []
        else:
            comments_list = Postcomments(comments, user)
        attachments = Attachments.objects.filter(post=post, upload_for="Post")
        if attachments is not None:
            for attachment in attachments:
                attachments_list.append({
                    "id": attachment.id,
                    "image": post_comment_images(attachment) if attachment.image_upload else '',
                    "file": post_comment_file(attachment) if attachment.file_upload else '',
                    "created_at": time_ago(local_time(attachment.created_at)),
                })
        data = []
        event_list = []
        if post.post_type == 'Event':
            event_list = EventData(post, None,  offset=timezone)

        data.append({
            "id": post.id,
            "title": post.title,
            "description": post.Body,
            "cover_image": cover_images(post),
            "slug": post.slug,
            "post_type": post.post_type,
            "default_space": post.space.is_default,
            "is_comments_enabled": post.is_comments_enabled,
            "is_liking_enabled": post.is_liking_enabled,
            "notify_space_members": post.notify_space_members,
            "space_id": post.space.id,
            "space_name": post.space.title,
            "space_privacy": post.space.privacy,
            "is_default": post.space.is_default,
            "space_group_name": post.space_group.title,
            "space_group_id": post.space_group.id,
            "space_group_privacy": post.space_group.privacy,
            "created_by": f"{post.created_by.first_name} {post.created_by.last_name}",
            "created_by_id": post.created_by.id,
            "updated_by_id": post.update_by if post.update_by else '',
            "updated_by": f"{updated_by.first_name} {updated_by.last_name}" if post.update_by else '',
            "is_active": post.is_active,
            "user_profile_image": avatar(post.created_by),
            "created_at": time_ago(local_time(post.created_at)),
            "attachments": attachments_list,
            "likes_count": likess,
            "is_user_like": is_like,
            "is_user_saved": is_saved,
            "total_comments": total_comments,
            "comments": comments_list,
            "user_type": delete_post(user, post) if user is not None else None,
            "event": event_list
        })
        response = {
            "message": "Post data",
            "success": True,
            "data": {
                "user_id": user_id,
                "user_post": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if user_id := self.request.query_params.get('user_id'):
                user = check_valid_user(user_id)
                if not user:
                    return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"message": "user_id required in params", "success": False}, status=status.HTTP_404_NOT_FOUND)
            title = request.data['title']
            body = request.data['Body']
            is_comments_enabled = request.data['is_comments_enabled']
            is_liking_enabled = request.data['is_liking_enabled']
            notify_space_members = request.data['notify_space_members']
            try:
                space = Spaces.objects.get(id=request.data['space_id'])
            except Spaces.DoesNotExist:
                return Response({"message": "Invalid space_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                space_group = SpaceGroups.objects.get(id=request.data['space_group_id'])
            except SpaceGroups.DoesNotExist:
                return Response({"message": "Invalid space_group_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            post_id = self.kwargs['post_id']
            post = Post.objects.filter(id=post_id, is_active=True, is_delete=False)
            if not post:
                return Response({"space_id": space.id, "space_name": space.title, "space_privacy": space.privacy, "message": "Post not available", "success": True}, status=status.HTTP_404_NOT_FOUND)

            post.update(title=title, Body=body, notify_space_members=notify_space_members, update_by=user_id,
                        is_comments_enabled=is_comments_enabled, is_liking_enabled=is_liking_enabled, space=space, space_group=space_group)
            post = post.first()
            if data.get('image_upload') and data.get('file_upload'):
                image_file = request.FILES.getlist('image_upload')
                file_upload = request.FILES.getlist('file_upload')
                for image in image_file:
                    Attachments.objects.create(post=post, image_upload=image, upload_for="Post")
                for file in file_upload:
                    Attachments.objects.create(post=post, file_upload=file, upload_for="Post")

            elif data.get('image_upload'):
                image_file = request.FILES.getlist('image_upload')
                for image in image_file:
                    Attachments.objects.create(post=post, image_upload=image, upload_for="Post")
            elif data.get('file_upload'):
                file_upload = request.FILES.getlist('file_upload')
                for file in file_upload:
                    Attachments.objects.create(post=post, file_upload=file, upload_for="Post")

            if data.get('cover_image'):
                cover_image = request.FILES['cover_image']
                post.cover_image = cover_image
            if data.get('post_type'):
                post_type = request.data['post_type']
                post.post_type = post_type
            if data.get('tags'):
                tags = request.data['tags']
                post.tags = tags
            post.save()
            data = response_post(post_id, filter_by=None, offset=self.request.data['timezone'])
            response = {
                "message": "Space Get Data",
                "success": True,
                "data": {
                    "user_id": user_id,
                    "user_space": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        if user_id := self.request.query_params.get('user_id'):
            user = check_valid_user(user_id)
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "user_id required in params", "success": False}, status=status.HTTP_404_NOT_FOUND)
        post = Post.objects.filter(id=self.kwargs['post_id'])
        if not post:
            return Response({"message": "Post not available", "success": False}, status=status.HTTP_404_NOT_FOUND)
        comments = Comment.objects.filter(post=post.first())
        like = likes.objects.filter(post=post.first())
        post.update(is_active=False, is_delete=True, deleted_by=user_id)
        comments.update(is_active=False, is_delete=True)
        like.update(is_active=False)
        post = post.first()
        if post.post_type == 'Event':
            event = Event.objects.get(post_id=post)
            if event.add_to_collabarate == True:
                collabarate = Collabarate.objects.get(pk=event.collabarate_id)
                collabarate.is_active = False
                collabarate.is_cancel = True
                collabarate.cancel_by = user
                collabarate.save()

        response = {
            "user_id": user_id,
            "message": "Post deleted successfully",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class PublicPosts(APIView):
    permission_classes = [AllowAny]
    serializer_class = PostSerializer
    pagination_class = Pagination

    def get(self, request, *args, **kwargs):
        timezone = request.query_params.get('timezone')
        if not timezone:
            return Response({"message": "timezone is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        elif timezone == "undefined":
            return Response({"message": "Please Update Your Application",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        space = space_group = None
        if group_id := self.request.query_params.get('group_id'):
            try:
                space_group = SpaceGroups.objects.get(id=group_id)
            except SpaceGroups.DoesNotExist:
                return Response({"message": "SpaceGroup not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if space_id := self.request.query_params.get('space_id'):
            try:
                space = Spaces.objects.get(id=space_id)
            except Spaces.DoesNotExist:
                return Response({"message": "Space not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_id = self.request.query_params.get('user_id')
        filter_by = self.request.query_params.get('order_by')
        is_joined = True
        space_member_type = ''
        space_list = []
        data = []
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                user_type = ",".join(str(type.type) for type in user.userType.all())
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

            space_member = SpaceMembers.objects.filter(
                user=user, space=space, is_joined=True, is_active=True, is_delete=False)
            if group_id:
                space_member = SpaceMembers.objects.filter(user=user, space_group=space_group,
                                                           is_joined=True, is_active=True, is_delete=False)
                space_list = [member.space for member in space_member]
            if space_member:
                space_member_type = space_member.first().user_type
            if "Admin" in user_type:
                posts = Post.objects.filter(inappropriate_content=False, is_active=True, is_delete=False)
                if not space and not group_id:
                    is_joined = False
                    posts = posts.filter(~Q(post_type='Event'), space__privacy="Public")
                elif group_id:
                    posts = posts.filter(space_group=space_group, space__in=space_list)
                else:
                    posts = posts.filter(space=space)
                data = post_filter(posts, filter_by, user, offset=timezone)
            elif "ProgramManager" in user_type:
                posts = Post.objects.filter(inappropriate_content=False, is_active=True, is_delete=False)
                if not space and not group_id:
                    is_joined = False
                    posts = posts.filter(~Q(post_type='Event'), space__privacy="Public")
                elif group_id:
                    posts = posts.filter(space_group=space_group, space__in=space_list)
                elif space_member := SpaceMembers.objects.filter(user=user, space_group=space.space_group, is_joined=True, is_active=True, is_delete=False, space=space).first():
                    posts = posts.filter(space_group=space_member.space_group, space=space)
                else:
                    is_joined = False
                    posts = posts.filter(space__privacy="Public", space=space)
                data = post_filter(posts, filter_by, user, offset=timezone)
            else:
                if not space and not group_id:
                    is_joined = False
                    posts = Post.objects.filter(~Q(post_type='Event'), is_active=True,
                                                inappropriate_content=False, is_delete=False, space__privacy="Public")
                    data = post_filter(posts, filter_by, user, offset=timezone)
                elif not space_member:
                    is_joined = False
                    if group_id:
                        spaces = Spaces.objects.filter(space_group=space_group)
                        posts = Post.objects.filter(~Q(post_type='Event'), is_active=True, inappropriate_content=False,
                                                    is_delete=False, space__in=spaces, space__privacy="Public")
                        data = post_filter(posts, filter_by, offset=timezone)
                    elif space:
                        if space.privacy != "Public":
                            data = {"message": "This space is private", "success": True}
                        elif posts := Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False):
                            data = post_filter(posts, filter_by, offset=timezone)
                elif space:
                    space_member = space_member.first()
                    if space.privacy == "Private":
                        if not space_member:
                            is_joined = False
                            data = {"message": "This space is private", "success": True}                            
                        else:
                            posts = Post.objects.filter(
                                space=space, inappropriate_content=False, is_active=True, is_delete=False)
                            data = post_filter(posts, filter_by, user, offset=timezone)
                    elif space.privacy == "Public":
                        if not space_member:
                            is_joined = False
                        posts = Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False)
                        data = post_filter(posts, filter_by, space_member.user, offset=timezone)
                elif group_id:
                    space_member = space_member.first()
                    posts = Post.objects.filter(space_group=space_group,
                                                inappropriate_content=False, space__in=space_list)
                    data = post_filter(posts, filter_by, space_member.user, offset=timezone)
                else:
                    space_member = space_member.first()
                    if space.privacy != "Public":
                        is_joined = False
                        data = {"message": "This space is private", "success": True}
                    elif posts := Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False):
                        data = post_filter(posts, filter_by, space_member.user, offset=timezone)

        else:
            is_joined = False
            if not space and not group_id:
                posts = Post.objects.filter(~Q(post_type='Event'), is_active=True,
                                            inappropriate_content=False, is_delete=False, space__privacy="Public")
                data = post_filter(posts, filter_by, offset=timezone)
            elif group_id:
                spaces = Spaces.objects.filter(space_group=space_group)
                posts = Post.objects.filter(~Q(post_type='Event'), is_active=True, inappropriate_content=False,
                                            is_delete=False, space__in=spaces, space__privacy="Public")
                data = post_filter(posts, filter_by, offset=timezone)
            elif space.privacy != "Public":
                data = {"message": "This space is private", "success": True}
            elif posts := Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False):
                data = post_filter(posts, filter_by, offset=timezone)
        pagination = ''
        obj = isinstance(data, list)
        if obj:
            paginator = Paginator(data, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }

        if group_id:
            space_group_id = space_group.id
            space_group_name = space_group.title
        elif space:
            space_group_id = space.space_group.id
            space_group_name = space.space_group.title
        else:
            space_group_id = None
            space_group_name = None

        response = {
            "message": "Public Post Data",
            "success": True,
            "data": {
                "pages": pagination,
                "user_id": '' if user_id is None else user_id,
                "space_id": space.id if space else None,
                "space_name": space.title if space else None,
                "space_privacy": space.privacy if space else None,
                "is_joined": is_joined,
                "space_group_id": space_group_id,
                "space_group_name": space_group_name,
                "public_post": pages.object_list if obj else data,
                "space_type": space.space_type if space else None,
                "space_member_type": space_member_type
                # "public_post": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class Comments(APIView):
    permission_classes = [AllowAny]
    serializer_class = CommentSerializer

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            post = Post.objects.get(id=self.request.query_params.get('post_id'))
        except Post.DoesNotExist:
            return Response({"message": "Post not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        comments = Comment.objects.filter(created_by=user, post=post, parent_id=None,
                                          inappropriate_content=False, is_active=True, is_delete=False)
        attachments_list = []
        if comments is not None:
            data = Postcomments(comments, user)
        pagination = ''
        obj = isinstance(data, list)
        if obj:
            paginator = Paginator(data, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }
        response = {
            "message": "Comments Get Data",
            "success": True,
            "data": {
                "pages": pagination,
                # "user_Comments": pages.object_list,
                "user_Comments": pages.object_list if obj else data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=self.kwargs['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                post = Post.objects.get(id=request.data['post_id'])
            except Post.DoesNotExist:
                return Response({"message": "Post not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            body = replace_links_with_anchor_tags(request.data['body'])
            parent_id_obj = None
            if data.get('parent_id'):
                parent_id = data.get('parent_id')
                parent_id_obj = Comment.objects.get(id=parent_id)
            comment = Comment.objects.create(Body=body, post=post, created_by=user, parent_id=parent_id_obj)

            if data.get('image_upload') and data.get('file_upload'):
                image_file = request.FILES.getlist('image_upload')
                file_upload = request.FILES.getlist('file_upload')
                for image in image_file:
                    Attachments.objects.create(comment=comment, image_upload=image, upload_for="Comment")
                for file in file_upload:
                    Attachments.objects.create(comment=comment, file_upload=file, upload_for="Comment")

            elif data.get('image_upload'):
                image_file = request.FILES.getlist('image_upload')
                for image in image_file:
                    Attachments.objects.create(comment=comment, image_upload=image, upload_for="Comment")
            elif data.get('file_upload'):
                file_upload = request.FILES.getlist('file_upload')
                for file in file_upload:
                    Attachments.objects.create(comment=comment, file_upload=file, upload_for="Comment")

            if data.get('cover_image'):
                cover_image = request.FILES['cover_image']
                comment.cover_image = cover_image
            if data.get('comment_for'):
                comment_for = request.data['comment_for']
                comment.comment_for = comment_for
            comment.save()
            if words := check_inappropriate_words(body):
                Comment.objects.filter(id=comment.id).update(inappropriate_content=True)
                ContentToReview.objects.create(title="Inappropriate Content", post=post, profanity_words=",".join(words),
                                               comment=comment, posted_on="Comment", user=user, space=post.space)
                print(f"check_text: {words}")
            else:
                if post.created_by != user:
                    send_post_notification(post.created_by, post.title, post, get_text(body))
                    notifye.send(sender=user, to_user=post.created_by, by_user=user, verb=post.title, description=body,
                                notification_types="Comment" if parent_id_obj is None else "Replies", category="AtPace_Community", action_id={"post_id": str(post.id), "comment_id": str(comment.id)})

                response = user_comment(comment)
                if user.phone and user.is_whatsapp_enable:
                    comment_recorded_confirmation(user, comment)
                else:
                    print("no phone number exist")
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateComments(APIView):
    permission_classes = [AllowAny]
    serializer_class = CommentSerializer

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            post = Post.objects.get(id=self.kwargs['post_id'])
        except Post.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if comment_id := self.request.query_params.get('comment_id'):
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({"message": "Please provide valid comment_id in params", "success": False}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "Please provide valid comment_id in params", "success": False}, status=status.HTTP_404_NOT_FOUND)
        response = user_comment(comment)
        return Response(response, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            post = Post.objects.get(id=self.kwargs['post_id'])
        except Post.DoesNotExist:
            return Response({"message": "Post not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if comment_id := self.request.query_params.get('comment_id'):
            comment = Comment.objects.filter(id=comment_id, inappropriate_content=False,
                                             is_active=True, is_delete=False)
        else:
            return Response({"message": "Please provide valid comment_id in params", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if not comment:
            return Response({"message": "Please provide valid comment_id in params", "success": False}, status=status.HTTP_404_NOT_FOUND)
        comment.update(is_active=False, is_delete=True)
        response = {
            "message": "Comment deleted successfully",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class UpdateComment(APIView):
    permission_classes = [AllowAny]
    serializer_class = CommentSerializer

    def put(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=self.kwargs['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                post = Post.objects.get(id=request.data['post_id'])
            except Post.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            comment_id = self.kwargs['comment_id']
            body = request.data['body']
            comment = Comment.objects.filter(id=comment_id)
            comment.update(Body=body, post=post, created_by=user)
            comment = comment.first()
            if data.get('cover_image'):
                cover_image = request.data['cover_image']
                comment.cover_image = cover_image
            if data.get('comment_for'):
                comment_for = request.data['comment_for']
                comment.comment_for = comment_for
            comment.save()
            response = user_comment(comment)
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LikeOnPostComment(APIView):
    permission_classes = [AllowAny]
    serializer_class = LikeSerializer

    def get(self, request, *args, **kwargs):
        data = request.data
        post = None
        comment = None
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        if id := self.request.query_params.get('id'):
            try:
                post = Post.objects.get(id=id)
            except Post.DoesNotExist:
                comment = Comment.objects.get(id=id)
            is_like, likess = like_post_comment(user, post, comment)
        else:
            return Response({"message": "post or comment id required in params"}, status=status.HTTP_400_BAD_REQUEST)
        data = {
            "likes_count": likess,
            "is_user_like": is_like,
        }
        response = {
            "message": "Like Get Data",
            "success": True,
            "data": {
                "user_likes": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=self.kwargs['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            post = ''
            if data.get('post_id'):
                try:
                    post = Post.objects.get(id=data.get('post_id'))
                except Post.DoesNotExist:
                    return Response({"message": "Invalid post_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
                space = post.space
                try:
                    like = likes.objects.get(post=post, created_by=user)
                    like.is_like = False if like.is_like else True
                except likes.DoesNotExist:
                    like = likes.objects.create(post=post, created_by=user, like_for="Post", is_like=True)
                to_user = post.created_by
                notification = AtPaceNotification.objects.filter(to_user=to_user, by_user_obj=ContentType.objects.get_for_model(
                    user), by_user_id=user.pk, action_id__post_id=str(post.id), action_id__like_id=str(like.id), is_active=True, is_delete=False)
                action_id = {"post_id": str(post.id), "like_id": str(like.id)}
                post_title = post.title
                notification_types = "PostLike"
            else:
                try:
                    comment = Comment.objects.get(id=data.get('comment_id'))
                except Comment.DoesNotExist:
                    return Response({"message": "Invalid comment_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
                space = comment.post.space
                try:
                    like = likes.objects.get(comment=comment, created_by=user)
                    like.is_like = False if like.is_like else True
                except likes.DoesNotExist:
                    like = likes.objects.create(comment=comment, created_by=user, like_for="Comment", is_like=True)
                to_user = comment.created_by
                notification = AtPaceNotification.objects.filter(to_user=to_user, by_user_obj=ContentType.objects.get_for_model(
                    user), by_user_id=user.pk, action_id__comment_id=str(comment.id), action_id__like_id=str(like.id), is_active=True, is_delete=False)
                action_id = {"post_id": str(comment.post.id), "comment_id": str(comment.id), "like_id": str(like.id)}
                post_title = comment.post.title
                notification_types = "CommentLike"

            try:
                member = SpaceMembers.objects.get(
                    user=user, space=space, space_group=space.space_group, is_active=True, is_delete=False)
                if member.is_joined != True:
                    member.is_joined = True
                    member.save()
            except SpaceMembers.DoesNotExist:
                member = SpaceMembers.objects.create(user=user, user_type="Member", space=space, space_group=space.space_group,
                                                     is_joined=True, email=user.email, invitation_status="Accept")
            if notification:
                notification.update(is_active=False, is_delete=True)
                
            if like.is_like and not to_user == user:
                post_obj = post if post else comment.post
                send_post_notification(to_user, post_obj.title, post_obj, "Liked")
                notifye.send(sender=user, to_user=to_user, by_user=user, verb=post_title, notification_types=notification_types,
                             category="AtPace_Community", action_id=action_id)
            like.save()
            data = {
                "id": like.id,
                "post_id": like.post.id if like.post else '',
                "comment_id": like.comment.id if like.comment else '',
                "like_for": like.like_for,
                "is_like": like.is_like,
                "liked_by": like.created_by.username,
                "liked_by_id": like.created_by.id,
            }
            response = {
                "message": "Like Get Data",
                "success": True,
                "data": {
                    "user_like": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportPost(APIView):
    permission_classes = [AllowAny]
    serializer_class = ReportSerializer

    def get(self, request, *args, **kwargs):
        data = request.data
        user_type = UserTypes.objects.filter(type__in=['Admin', 'ProgramManager'])
        try:
            user = User.objects.get(pk=self.kwargs['user_id'], userType__in=user_type)
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        try:
            post = Post.objects.get(id=data.get('post_id'))
        except Post.DoesNotExist:
            return Response({"message": "Invalid post_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        reports = Report.objects.filter(is_report=True, post=post)
        if not reports:
            return Response({"message": "No report data", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = [{"id": report.id, "post_id": report.post.id, "post_title": report.post.title, "post_by": f"{report.post.created_by.first_name} {report.post.created_by.last_name}",
                 "post_by_id": report.post.created_by.id, "is_report": report.is_report, "report_type": report.report_type, "comment": report.comment, "report_by": f"{user.first_name} {user.last_name}"} for report in reports]

        response = {
            "message": "Report Get Data",
            "success": True,
            "data": {
                "user_report_post": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=self.kwargs['user_id'])
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                post = Post.objects.get(id=request.data['post_id'])
            except Post.DoesNotExist:
                return Response({"message": "Invalid post_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            report_type = request.data['report_type']
            comment = request.data['comment']
            if Report.objects.filter(post=post, is_report=True, report_by=user).exists():
                return Response({"message": "This post is already reported", "success": True}, status=status.HTTP_208_ALREADY_REPORTED)
            # except Report.DoesNotExist:
            report = Report.objects.create(post=post, post_by=post.created_by, report_by=user, is_report=True,
                                           report_type=report_type, comment=comment)
            # send_report_post_mail(user, post, report)
            data = {
                "id": report.id,
                "post_id": report.post.id,
                "post_title": report.post.title,
                "post_by": report.post.created_by.first_name+" "+report.post.created_by.last_name,
                "is_report": report.is_report,
                "report_type": report.report_type,
                "comment": report.comment,
                "report_by": user.first_name+" "+user.last_name,
            }
            response = {
                "message": "Post reported successfully",
                "success": True,
                "data": {
                    "user_report_post": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchContent(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = None
        if user_id := self.request.query_params.get('user_id'):
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
            member = SpaceMembers.objects.filter(user=user)
            space_list = [space.space for space in member]
        if not (search := self.request.query_params.get('search')):
            return Response({"message": "No Data Found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_member = SpaceMembers.objects.filter(Q(user__first_name__icontains=search) | Q(
            user__last_name__icontains=search), is_active=True, is_delete=False)
        public_posts = Post.objects.filter(
            title__icontains=search, inappropriate_content=False, is_active=True, is_delete=False,)
        public_posts = public_posts.filter(
            space__in=space_list) if user else public_posts.filter(space__privacy="Public")
        data = []
        if space_member is not None:
            temp_member = []
            for member in space_member:
                member_id = member.user.id
                if member_id not in temp_member:
                    temp_member.append(member_id)
                    if not member.user.private_profile:
                        data.append({"id": member_id, "name": f"{member.user.first_name} {member.user.last_name}",
                                     "heading": member.user.profile_heading, "user_profile_image": avatar(member.user), "type": "user"})
        spaces = Spaces.objects.filter(title__icontains=search, privacy="Public")
        for space in spaces:
            data.append({
                "id": space.id,
                "name": space.title,
                "type": "space"
            })
        if user:
            spaces_member = SpaceMembers.objects.filter(
                user=user, space__title__icontains=search, space__privacy="Private")
            for spaces_m in spaces_member:
                data.append({
                    "id": spaces_m.space.id,
                    "name": spaces_m.space.title,
                    "type": "space"
                })
        if public_posts is not None:
            data.extend({"id": post.id, "name": post.title, "type": "user_post"} for post in public_posts)
        Search.objects.create(search_key=search, user=user) if user else Search.objects.create(search_key=search)

        paginator = Paginator(data, 10)
        page_number = self.request.query_params.get('page', 1)
        pages = paginator.get_page(page_number)
        pagination = {
            "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
            "current_page": pages.number,
            "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
            "total_items": pages.paginator.count,
            "total_pages": pages.paginator.num_pages,
        }
        response = {
            "message": "Search Data",
            "success": True,
            "data": {
                "user_id": user_id,
                "pages": pagination,
                # "user_search_data": pages.object_list,
                "user_search_data": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class AllComments(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_member = SpaceMembers.objects.filter(user=user, is_active=True, is_delete=False)
        space_list = [member.space for member in space_member]
        posts = Post.objects.filter(space__in=space_list, inappropriate_content=False, is_active=True, is_delete=False)
        comments = Comment.objects.filter(created_by=user, post__in=posts,
                                          inappropriate_content=False, is_active=True, is_delete=False)
        data = Postcomments(comments, user)
        pagination = ''
        obj = isinstance(data, list)
        if obj:
            paginator = Paginator(data, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }
        response = {
            "message": "User Comments Data",
            "success": True,
            "data": {
                "pages": pagination,
                "user_all_comments": pages.object_list if obj else data,
                # "user_all_comments": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class SpaceGroupMember(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        if user_id := self.request.query_params.get('user_id'):
            user = check_valid_user(user_id)
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)

        try:
            space_group = SpaceGroups.objects.get(pk=self.kwargs['space_group_id'])
        except SpaceGroups.DoesNotExist:
            return Response({"message": "Invalid space_group_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_group_members = SpaceMembers.objects.filter(
            space_group=space_group, is_joined=True, is_active=True, is_delete=False)

        if search := self.request.query_params.get('search'):
            space_group_members = space_group_members.filter(
                Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search))
        if filter_by := self.request.query_params.get('bio'):
            space_group_members = space_group_members.filter(user__about_us__icontains=filter_by)
        if filter_by := self.request.query_params.get('heading'):
            space_group_members = space_group_members.filter(user__profile_heading__icontains=filter_by)
        if filter_by := self.request.query_params.get('location'):
            space_group_members = space_group_members.filter(user__address__icontains=filter_by)
        if filter_by := self.request.query_params.get('role'):
            space_group_members = space_group_members.filter(user__about_us__icontains=filter_by)
        data = []
        temp = []
        if not space_group_members:
            return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
        for member in space_group_members:
            if not member.user.id in temp:
                temp.append(member.user.id)
                data.append({
                    "id": member.id,
                    "user_id": member.user.id,
                    "name": f"{member.user.first_name} {member.user.last_name}",
                    "email": member.email,
                    "user_type": member.user_type,
                    "is_joined": member.is_joined,
                    "is_active": member.is_active,
                    "heading": member.user.profile_heading,
                    "usre_profile_image": avatar(member.user),
                    "space_id": member.space.id,
                    "about_us": member.user.about_us,
                    "location": f"{member.user.city}, {member.user.state}",
                    "space_name": member.space.title,
                    "created_at": local_time(member.created_at),
                })
        response = {
            "message": "group member data",
            "success": True,
            "data": {
                "user_id": user_id,
                "space_group_id": space_group.id,
                "space_group_name": space_group.title,
                "all_group_members": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class EventSpaceMember(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        if user_id := self.request.query_params.get('user_id'):
            user = check_valid_user(user_id)
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)

        try:
            space = Spaces.objects.get(pk=self.kwargs['space_id'])
        except Spaces.DoesNotExist:
            return Response({"message": "Invalid space_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_members = SpaceMembers.objects.filter(space=space, is_active=True, is_delete=False, is_joined=True)

        if search := self.request.query_params.get('search'):
            space_members = space_members.filter(Q(user__first_name__icontains=search)
                                                 | Q(user__last_name__icontains=search))
        if filter_by := self.request.query_params.get('bio'):
            space_members = space_members.filter(user__about_us__icontains=filter_by)
        if filter_by := self.request.query_params.get('heading'):
            space_members = space_members.filter(user__profile_heading__icontains=filter_by)
        if filter_by := self.request.query_params.get('location'):
            space_members = space_members.filter(user__address__icontains=filter_by)
        if filter_by := self.request.query_params.get('role'):
            space_members = space_members.filter(user__about_us__icontains=filter_by)
        data = []
        temp = []
        if not space_members:
            return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
        for member in space_members:
            if not member.user.id in temp:
                temp.append(member.user.id)
                data.append({
                    "id": member.id,
                    "user_id": member.user.id,
                    "name": f"{member.user.first_name} {member.user.last_name}",
                    "email": member.email,
                    "user_type": member.user_type,
                    "is_joined": member.is_joined,
                    "is_active": member.is_active,
                    "heading": member.user.profile_heading,
                    "usre_profile_image": avatar(member.user),
                    "space_id": member.space.id,
                    "about_us": member.user.about_us,
                    "location": f"{member.user.city}, {member.user.state}",
                    "space_name": member.space.title,
                    "created_at": local_time(member.created_at),
                })
        response = {
            "message": "group member data",
            "success": True,
            "data": {
                "user_id": user_id,
                "space_id": space.id,
                "space_name": space.title,
                "all_group_members": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class SpaceGroupDetails(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            space_group = SpaceGroups.objects.get(pk=self.kwargs['space_group_id'])
        except SpaceGroups.DoesNotExist:
            return Response({"message": "Invalid space_group_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        spaces = Spaces.objects.filter(is_active=True, is_delete=False, is_hidden=False, space_group=space_group,
                                       hidden_from_non_members=False)
        if search := self.request.query_params.get('search'):
            spaces = spaces.filter(title__icontains=search)
        if order_by := self.request.query_params.get('order_by'):
            spaces = space_filter(spaces, order_by)
        data = []
        space_member = 0
        is_joined = False
        if not spaces:
            return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
        for space in spaces:
            space_member_count = SpaceMembers.objects.filter(space=space).count()
            if user_id := self.request.query_params.get('user_id'):
                user = User.objects.get(pk=user_id)
                space_member = SpaceMembers.objects.filter(
                    user=user, space=space, is_joined=True, is_active=True, is_delete=False).count()

            is_joined = False if space_member == 0 else True
            if space.privacy == "Public" or is_joined:
                data.append({
                    "id": space.id,
                    "space_name": space.title,
                    "description": space.description,
                    "privacy": space.privacy,
                    "is_default": space.is_default,
                    "is_hidden": space.is_hidden,
                    "hidden_from_non_members": space.hidden_from_non_members,
                    "created_by": space.created_by.username,
                    "is_joined": is_joined,
                    "space_type": space.space_type,
                    "space_member_count": space_member_count,
                    "created_by_id": space.created_by.id,
                    "created_at": local_time(space.created_at)

                })
        response = {
            "message": "space group data",
            "success": True,
            "data": {
                "user_id": user_id,
                "space_group_id": space_group.id,
                "space_group_name": space_group.title,
                "space_group_data": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class ReportTypes(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        report_type = [report_type[0] for report_type in report_types]
        response = {
            "message": "Report data",
            "success": True,
            "data": {
                "user_id": user.id,
                "post_report_data": report_type,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class TrendingPost(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        timezone = request.query_params.get('timezone', None)
        if timezone is None:
            return Response({"message": "timezone is required",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        elif timezone == "undefined":
            return Response({"message": "Please Update Your Application",  "success": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            space = Spaces.objects.get(id=self.kwargs['space_id'])
        except Spaces.DoesNotExist:
            return Response({"message": "Invalid space_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user = None
        all_post = Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False)
        if user_id := self.request.query_params.get('user_id'):
            user = User.objects.get(pk=user_id)
        if like := self.request.query_params.get('like'):
            trending_post = all_post.annotate(like_count=Count('likes')).order_by('-like_count')
        elif comment := self.request.query_params.get('comment'):
            trending_post = all_post.annotate(comment_count=Count("comment")).order_by('-comment_count')
        elif oldest := self.request.query_params.get('oldest'):
            trending_post = all_post.order_by('created_at')
        elif newest := self.request.query_params.get('newest'):
            trending_post = all_post.order_by('-created_at')
        else:
            return Response({"message": "No trending post available", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = all_posts(trending_post, "all", user, offset=timezone)
        response = {
            "message": "Trending post data",
            "success": True,
            "data": {
                "user_id": user_id,
                "trending_post_data": data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class UserSavedPost(APIView):
    permission_classes = [AllowAny]
    serializer_class = SavedPostSerializer

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        saved_post = SavedPost.objects.filter(saved_by=user, is_saved=True, post__inappropriate_content=False,
                                              post__is_active=True, is_active=True, is_delete=False)
        if not saved_post:
            return Response({"message": "No Saved Posts", "success": True}, status=status.HTTP_200_OK)
        data = []
        for post in saved_post:
            attachments = Attachments.objects.filter(post=post.post, upload_for="Post")
            attachments_list = [{"id": attachment.id, "image": post_comment_images(attachment) if attachment.image_upload else '',
                                 "file": post_comment_file(attachment) if attachment.file_upload else '', "created_at": time_ago(local_time(attachment.created_at))} for attachment in attachments]
            is_like = False
            total_comments = Comment.objects.filter(inappropriate_content=False,
                                                    post=post.post, parent_id=None, comment_for="Post", is_active=True, is_delete=False).count()
            is_like, likess = like_post_comment(user, post=post.post, comment=None)
            data.append({
                "id": post.id,
                "post_id": post.post.id,
                "space_id": post.post.space.id,
                "space_name": post.post.space.title,
                "space_privacy": post.post.space.privacy,
                "default_space": post.post.space.is_default,
                "space_group_id": post.post.space_group.id,
                "space_group_name": post.post.space_group.title,
                "space_group_privacy": post.post.space_group.privacy,
                "title": post.post.title,
                "description": post.post.Body,
                "post_type": post.post.post_type,
                "is_comments_enabled": post.post.is_comments_enabled,
                "is_liking_enabled": post.post.is_liking_enabled,
                "is_active": post.post.is_active,
                "created_by": f"{post.post.created_by.first_name} {post.post.created_by.last_name}",
                "created_by_id": post.post.created_by.id,
                "user_profile_image": avatar(post.post.created_by),
                "heading": post.post.created_by.profile_heading,
                "created_at": time_ago(local_time(post.post.created_at)),
                "likes_count": likess,
                "is_user_like": is_like,
                "is_user_saved": post.is_saved,
                "attachments": attachments_list,
                "total_comments": total_comments,
                "comments": [],
                "likes_count": likess,
                "is_user_like": is_like,
                "is_user_saved": post.is_saved,
                "is_saved": post.is_saved,
                "is_active": post.is_active,
                "saved_by": f"{post.saved_by.first_name} {post.saved_by.last_name}",
            })
        pagination = ''
        obj = isinstance(data, list)
        if obj:
            paginator = Paginator(data, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }
        response = {
            "message": "Saved Post data",
            "success": True,
            "data": {
                "user_id": user.id,
                "pages": pagination,
                "saved_post_data": pages.object_list if obj else data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                post = Post.objects.get(id=request.data['post_id'])
            except Post.DoesNotExist:
                return Response({"message": "invalid post_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                saved_post = SavedPost.objects.get(post=post, saved_by=user)
                saved_post.is_saved = not saved_post.is_saved
                saved_post.save()
            except SavedPost.DoesNotExist:
                saved_post = SavedPost.objects.create(
                    post=post, is_saved=True, saved_by=user, created_by=post.created_by)
            data = {
                "id": saved_post.id,
                "post_id": saved_post.post.id,
                "post_name": saved_post.post.title,
                "post_by": f"{saved_post.created_by.first_name} {saved_post.created_by.last_name}",
                "is_saved": saved_post.is_saved,
                "is_active": saved_post.is_active,
                "saved_by": f"{user.first_name} {user.last_name}",
            }
            response = {
                "message": "Saved Post data",
                "success": True,
                "data": {
                    "user_id": user.id,
                    "saved_post_data": data,
                }
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AtpaceNotificationAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        notification = AtPaceNotification.objects.filter(to_user=user, is_active=True, is_delete=False)
        notification.update(unread=False)
        notification_list = []
        for notifie in notification:
            show_noti = False
            action_user = User.objects.get(pk=notifie.by_user_id)
            try:
                post = Post.objects.get(id=notifie.action_id['post_id'])
                if post.is_active == True and post.is_delete == False:
                    show_noti = True
                #print("notifie.notification_type", notifie.notification_types)
                if notifie.notification_types == 'Comment':
                    #print("line 1976")
                    comment = Comment.objects.get(id=notifie.action_id['comment_id'])
                    if comment.is_active == True and comment.is_delete == False:
                        show_noti = True
                    else:
                        show_noti = False

                if show_noti:
                    notification_list.append({
                        "notified_user": f"{notifie.to_user.first_name} {notifie.to_user.last_name}",
                        "notifie_user_id": notifie.to_user.id,
                        "action_by_user": f"{action_user.first_name} {action_user.last_name}",
                        "action_user_id": action_user.id,
                        "user_profile_image": avatar(action_user),
                        "verb": notifie.verb,
                        "post_id": post.id,
                        "category": notifie.category,
                        "notification_types": notifie.notification_types,
                        "description": notifie.description,
                        "created_at": time_ago(local_time(notifie.created_at))
                    })
            except:
                pass
        pagination = ''
        obj = isinstance(notification_list, list)
        if obj:
            paginator = Paginator(notification_list, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }

        response = {
            "message": "Notification",
            "success": True,
            "data": {
                "user_id": user.id,
                "pages": pagination,
                "notification_list": pages.object_list if obj else notification_list,
            }
        }
        return Response(response, status=status.HTTP_200_OK)

# class InvitationLink(APIView):
#     permission_classes = [AllowAny]
#     serializer_class = InviteLinkSerializer

#     def post(self, request, *args, **kwargs):
#         data = request.data
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             try:
#                 user = User.objects.get(id=request.data['user_id'])
#             except User.DoesNotExist:
#                 return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
#             first_name = request.data['first_name']
#             last_name = request.data['last_name']
#             email = request.data['email']
#             send_invite_user_mail(user, first_name, last_name, email)
#             #print(data)
#             return Response({"message": "User Invited Successfully", "success": True}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AtpaceNotificationCount(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs['user_id'])
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
        notification = AtPaceNotification.objects.filter(
            to_user=user, unread=True, is_active=True, is_delete=False).count()

        response = {
            "message": "Notification data",
            "success": True,
            "data": {
                "user_id": user.id,
                "notification_count": notification,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class UserChat(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user1 = self.request.query_params.get('user1')
        user2 = self.request.query_params.get('user2')
        if (user1 == user2):
            return Response({"message": "Both the users should not be same", "success": False}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                user1 = User.objects.get(pk=user1)
            except User.DoesNotExist:
                return Response({"message": "User1 not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

            try:
                user2 = User.objects.get(pk=user2)
            except User.DoesNotExist:
                return Response({"message": "User2 not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

            room_name = get_chat_room(user1, user2)

            room = Room.objects.get(name=room_name)

            chats = Chat.objects.filter(
                Q(from_user=room.user1) & Q(to_user=room.user2) | Q(from_user=room.user2) & Q(
                    to_user=room.user1)).order_by('timestamp')
            # #print("chats", chats)

            # #print("data", data)

            chat_list = []

            for chat in chats:
                chat_list.append({
                    "id": chat.id,
                    "sender_id": chat.from_user.id,
                    "sender_name": f"{chat.from_user.first_name} {chat.from_user.last_name}",
                    "sender_avatar": avatar(chat.from_user),
                    "receiver_id": chat.to_user.id,
                    "receiver_name": f"{chat.to_user.first_name} {chat.to_user.last_name}",
                    "receiver_avatar": avatar(chat.to_user),
                    "message": chat.message,
                    "time_stamp": time_ago_days(chat.timestamp)
                })

            response = {
                "message": "Message data",
                "success": True,
                "data": {
                    "room": room_name,
                    "chats": chat_list,
                    "name": user2.first_name + " " + user2.last_name
                }
            }
        return Response(response, status=status.HTTP_200_OK)


class UserRoom(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = self.request.query_params.get('user')
        all_rooms = Room.objects.filter(Q(user1=user) | Q(user2=user), user1__is_active=True,
                                        user2__is_active=True, user1__is_delete=False, user2__is_delete=False)
        # #print("all rooms", all_rooms)
        all_rooms_list = []
        for rooms in all_rooms:
            if rooms.user1:
                if rooms.user2:
                    all_rooms_list.append({
                        "user1_id": rooms.user1.pk,
                        "user2_id": rooms.user2.pk,
                        "user1_avatar": avatar(rooms.user1),
                        "user2_avatar": avatar(rooms.user2),
                        "user1_full_name": f"{rooms.user1.first_name} {rooms.user1.last_name}",
                        "user2_full_name": f"{rooms.user2.first_name} {rooms.user2.last_name}",
                        "room_name": rooms.name,

                    })
            # #print(all_rooms_list)

        response = {
            "message": "Message data",
            "success": True,
            "data": {
                "rooms": all_rooms_list,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class EventSpace(APIView):
    """
    List all Event Spaces.
    """

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "User not found", "success": False}, status=status.HTTP_404_NOT_FOUND)

        allspaces = Spaces.objects.filter(space_type="Event", is_active=True,
                                          is_delete=False, is_hidden=False, hidden_from_non_members=False)
        space_member = SpaceMembers.objects.filter(user=user, space__in=allspaces, is_joined=True, user_type__in=["Admin", "Moderator"], is_active=True, is_delete=False)
        space_list = [member.space for member in space_member]

        spaces = [{
            "id": space.id,
            "title": space.title,
            "descritpion": space.description,
            "cover_image": cover_images(space),
            "slug": space.slug,
            "space_group_id": space.space_group.id,
            "space_group": space.space_group.title,
            "privacy": space.privacy,
            "is_default": space.is_default,
            "is_hidden": space.is_hidden,
            "hidden_from_non_members": space.hidden_from_non_members,
            "is_active": space.is_active,
            "is_delete": space.is_delete,
            "created_by": space.created_by.username,
            "created_at": space.created_at,
            "heading": space.created_by.profile_heading
        }
            for space in space_list]

        response = {
            "message": "All Spaces",
            "success": True,
            "data": {
                "spaces": spaces,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class PinnedPost(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if space_group := self.request.query_params.get('group_id'):
            try:
                space_group = SpaceGroups.objects.get(id=space_group)
            except SpaceGroups.DoesNotExist:
                return Response({"message": "Space Group does not exist", "succes": False}, status=status.HTTP_404_NOT_FOUND)
        if space := self.request.query_params.get('space_id'):
            try:
                space = Spaces.objects.get(id=space)
            except Spaces.DoesNotExist:
                return Response({"message": "Space does not exist", "succes": False}, status=status.HTTP_404_NOT_FOUND)
        if not user:
            return Response({"message": "User does not exist", "succes": False}, status=status.HTTP_404_NOT_FOUND)
        pinned_post = UserPinnedPost.objects.filter(user=user, is_pinned=True)
        if space:
            pinned_post = pinned_post.filter(space=space)
        elif space_group:
            pinned_post = pinned_post.filter(space_group=space_group)
        post_list = [post.post for post in pinned_post]
        data = all_posts(post_list, "new", user, offset=self.request.query_params.get('timezone',None))
        pagination = ''
        obj = isinstance(data, list)
        if obj:
            paginator = Paginator(data, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }

        is_joined = False
        space_member_type = ''

        if space_group:
            space_group_id = space_group.id
            space_group_name = space_group.title
        elif space:
            space_group_id = space.space_group.id
            space_group_name = space.space_group.title
            space_member = SpaceMembers.objects.filter(
                user=user, space=space, is_joined=True, is_active=True, is_delete=False)
            if space_member:
                space_member_type = space_member.first().user_type
                is_joined = True
        else:
            space_group_id = None
            space_group_name = None

        response = {
            "message": "Pinned Post Data",
            "success": True,
            "data": {
                "pages": pagination,
                "user_id": str(user.id),
                "space_id": space.id if space else None,
                "space_name": space.title if space else None,
                "space_privacy": space.privacy if space else None,
                "space_group_id": space_group_id,
                "space_group_name": space_group_name,
                "public_post": pages.object_list if obj else data,
                "space_type": space.space_type if space else None,
                "is_joined": is_joined,
                "space_member_type": space_member_type
            }
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = PinnedPostSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "User does not exist", "succes": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                post = Post.objects.get(id=request.data['post_id'])
            except Post.DoesNotExist:
                return Response({"message": "Post does not exist", "succes": False}, status=status.HTTP_404_NOT_FOUND)
            space = space_group = None
            if "space_id" in request.data:
                try:
                    space = Spaces.objects.get(id=request.data['space_id'])
                except Spaces.DoesNotExist:
                    return Response({"message": "Space does not exist", "succes": False}, status=status.HTTP_404_NOT_FOUND)
            if "group_id" in request.data:
                try:
                    space_group = SpaceGroups.objects.get(id=request.data['group_id'])
                except SpaceGroups.DoesNotExist:
                    return Response({"message": "Space Group does not exist", "succes": False}, status=status.HTTP_404_NOT_FOUND)
            is_pinned_post = update_boolean(request.data['is_pinned'])
            if not UserPinnedPost.objects.filter(Q(space=space) | Q(space_group=space_group), user=user, post=post).exists():
                pinned_post = UserPinnedPost.objects.create(user=user, post=post, is_pinned=is_pinned_post)
                if space:
                    pinned_post.space = space
                    pinned_post.space_group = space.space_group
                else:
                    pinned_post.space_group = space_group
                pinned_post.save()
            else:
                if space:
                    UserPinnedPost.objects.filter(user=user, post=post, space=space).update(is_pinned=is_pinned_post)
                else:
                    UserPinnedPost.objects.filter(
                        user=user, post=post, space_group=space_group).update(is_pinned=is_pinned_post)
            response = {
                "message": "pinned post updated",
                "success": True,
                "data": post.id,
                "is_pinned": is_pinned_post
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContentsToReview(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        space_members = SpaceMembers.objects.filter(user=user, is_joined=True, is_active=True, is_delete=False).values("space", "user_type")
        data = []
        for space_member in space_members:
            all_content_review = ContentToReview.objects.filter(space=space_member['space'])
            for content in all_content_review:
                post = content.post if content.posted_on == "Post" else content.comment
                data.append({
                    "id": content.id,
                    "title": content.title,
                    "post_id": post.id,
                    "post_title": post.title if content.posted_on == "Post" else content.post.title,
                    "description": post.Body,
                    "space_id": content.space.id,
                    "space_title": content.space.title,
                    "posted_on": content.posted_on,
                    "is_reviewed": content.is_reviewed,
                    "reviewed_by": f"{content.reviewed_by.get_full_name()}" if content.reviewed_by else '',
                    "post_on_community": content.post_on_community,
                    "post_by_id": content.user.id,
                    "post_by_name": f"{content.user.get_full_name()}",
                    "post_by_image": avatar(content.user),
                    "inappropriate_content": content.profanity_words,
                    "created_at": time_ago(local_time(content.created_at)),
                    "comment_post_id": content.post.id if content.posted_on == "Comment" else "",
                    "member_type": space_member['user_type']
                })
        obj = isinstance(data, list)
        if obj:
            paginator = Paginator(data, 10)
            page_number = self.request.query_params.get('page', 1)
            try:
                pages = paginator.page(page_number)
            except Exception:
                return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
            pagination = {
                "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                "current_page": pages.number,
                "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                "total_items": pages.paginator.count,
                "total_pages": pages.paginator.num_pages,
            }

        response = {
            "message": "All Content Review Data",
            "success": True,
            "data": {
                "pages": pagination,
                "user_id": str(user.id),
                "review_data": pages.object_list if obj else data,
            }
        }
        return Response(response, status=status.HTTP_200_OK)


class ApproveRejectContent(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ApproveRejectContentSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(self.kwargs['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            post_on_community = update_boolean(request.data['post_on_community'])
            review_content_id = request.data['review_content_id']
            content_status = "Approved" if post_on_community else "Rejected"
            review_content = ContentToReview.objects.filter(id=request.data['review_content_id'])
            review_content.update(post_on_community=post_on_community, is_reviewed=True, reviewed_by=user)
            if post_on_community:
                review_content = review_content.first()
                obj = review_content.post if review_content.posted_on == "Post" else review_content.comment
                obj.inappropriate_content = False
                obj.save()
            response = {
                "message": f"Content {content_status}",
                "success": True,
                "data": review_content_id,
                "post_on_community": post_on_community
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventHostList(APIView):
    def get(self, request, *args, **kwargs):
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_list = User.objects.filter(userType__type__in=["Mentor", "ProgramManager"])
        host_list = [{"id": host.id, "name": host.get_full_name()} for host in user_list]
        response = {
            "message": "all host list",
            "success": True,
            "host_list": host_list
        }
        return Response(response, status=status.HTTP_200_OK)


class AmaseData(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        company = Company.objects.get(id="0a707050-8093-48cf-a433-b849b526849a")
        companys = CompanySerializer(company).data
        users = company.company.all()
        user = User.objects.filter(id="87649b20-9d04-44cf-937c-d177e14ded2d")
        users = users|user
        user_list = UsersSerializer(users, many=True).data
        rooms = Room.objects.filter(Q(user1__in=users), Q(user2__in=users)).distinct()
        rooms_list = RoomSerializer(rooms, many=True).data
        chats = Chat.objects.filter(room__in=rooms).distinct()
        chats_list = ChatSerializer(chats, many=True).data
        space_group = SpaceGroups.objects.get(id="46c72490-f8a1-463f-bf83-b12c1453e0f5")
        space_groups = SpaceGroupsSerializer(space_group).data
        spaces = Spaces.objects.filter(space_group=space_group)
        space_list = SpacesSerializer(spaces, many=True).data
        space_members = SpaceMembers.objects.filter(space_group=space_group, space__in=spaces)
        space_member_list = SpaceMembersSerializer(space_members, many=True).data
        posts = Post.objects.filter(space_group=space_group, space__in=spaces)
        posts_list = PostsSerializer(posts, many=True).data
        comments = Comment.objects.filter(post__in=posts)
        comments_list = CommentsSerializer(comments, many=True).data
        events = Event.objects.filter(post_id__in=posts)
        events_list = EventsSerializer(events, many=True).data

        response = {
            "company": companys,
            "space_groups": space_groups,
            "users": user_list,
            "rooms": rooms_list,
            "chats": chats_list,
            "spaces": space_list,
            "space_members": space_member_list,
            "posts": posts_list,
            "comments": comments_list,
            "events": events_list,
        }
        return Response(response, status=status.HTTP_200_OK)

class UpdateUserType(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        company = Company.objects.get(id="0a707050-8093-48cf-a433-b849b526849a")
        companys = CompanySerializer(company).data
        users = company.company.all().values("email", "userType__type")
        return Response(users, status=status.HTTP_200_OK)
    
    
class PublicPostWithSpace(APIView):
    def get(self, request, *args, **kwargs):

        space_type = self.request.query_params.get('space_type') or None
        timezone = self.request.query_params.get('timezone')
        if not timezone:
            return Response({"message": "timezone required in query_params", "success": False}, status=status.HTTP_400_BAD_REQUEST)
        filter_by = self.request.query_params.get('order_by') or None
        page_number = self.request.query_params.get('page', 1)
        print(f"page_number {page_number}")
        user = check_valid_user(self.kwargs['user_id'])
        if not user:
            return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user_types = [type.type for type in user.userType.all()]
        is_joined = False
        space_member_type = ''
        data = []
        space_list = []
        if "Admin" in user_types:
            space_list = Spaces.objects.all()
            if space_type:
                space_list = Spaces.objects.filter(space_type=space_type)
            for space in space_list:
                space_member = SpaceMembers.objects.filter(user=user, space=space, is_active=True, is_delete=False, is_joined=True)
                if space_member.exists():
                    is_joined = True
                    space_member_type = space_member.first().user_type
                    all_post = Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False)
                    post_data = post_filter(all_post, filter_by, user, offset=timezone)
                    obj = isinstance(post_data, list)
                    if obj:
                        paginator = Paginator(post_data, 10)
                        pages = paginator.page(page_number)
                        try:
                            pages = paginator.page(page_number)
                        except Exception:
                            return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
                        pagination_data = {
                            "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                            "current_page": pages.number,
                            "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                            "total_items": pages.paginator.count,
                            "total_pages": pages.paginator.num_pages,
                        }
        
                    data.append({
                        "pages": pagination_data,
                        "user_id": str(user.id),
                        "space_id": str(space.id),
                        "space_name": space.title,
                        "space_privacy": space.privacy,
                        "is_joined": is_joined,
                        "space_member_type": space_member_type,
                        "space_group_id": str(space.space_group.id),
                        "space_group_name": space.space_group.title,
                        "post": post_data
                    })
        elif "ProgramManager" in user_types:
            moderator_space_member = SpaceMembers.objects.filter(user=user, is_active=True, is_delete=False, is_joined=True, user_type="Moderator")
            if moderator_space_member.exists():
                space_group = [moderator.space_group for moderator in moderator_space_member]
                spaces = Spaces.objects.filter(space_group__in=space_group)
                if space_type:
                    spaces = Spaces.objects.filter(space_group__in=space_group, space_type=space_type)
                space_list = list(spaces)
            space_members = SpaceMembers.objects.filter(~Q(user_type="Moderator"), ~Q(space__in=spaces), space__space_type=space_type, user=user, is_active=True, is_delete=False, is_joined=True)
            if space_members.exists():
                space_list.extend([space_member.space for space_member in space_members])
            for space in space_list:
                space_member = SpaceMembers.objects.filter(user=user, space=space, is_active=True, is_delete=False, is_joined=True)
                if space_member.exists():
                    is_joined = True
                    space_member_type = space_member.first().user_type
                    all_post = Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False)
                    post_data = post_filter(all_post, filter_by, user, offset=timezone)
                    obj = isinstance(post_data, list)
                    if obj:
                        paginator = Paginator(post_data, 10)
                        pages = paginator.page(page_number)
                        try:
                            pages = paginator.page(page_number)
                        except Exception:
                            return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
                        pagination_data = {
                            "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                            "current_page": pages.number,
                            "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                            "total_items": pages.paginator.count,
                            "total_pages": pages.paginator.num_pages,
                        }
        
                    data.append({
                        "pages": pagination_data,
                        "user_id": str(user.id),
                        "space_id": str(space.id),
                        "space_name": space.title,
                        "space_privacy": space.privacy,
                        "is_joined": is_joined,
                        "space_member_type": space_member_type,
                        "space_group_id": str(space.space_group.id),
                        "space_group_name": space.space_group.title,
                        "post": post_data
                    })
        else:
            space_members = SpaceMembers.objects.filter(user=user, is_active=True, is_delete=False, is_joined=True)
            if space_type:
                space_members = space_members.filter(space__space_type=space_type)
            space_list = [space_member.space for space_member in space_members]
            for space in space_list:
                space_member = SpaceMembers.objects.filter(user=user, space=space, is_active=True, is_delete=False, is_joined=True)
                if space_member.exists():
                    is_joined = True
                    space_member_type = space_member.first().user_type
                    all_post = Post.objects.filter(space=space, inappropriate_content=False, is_active=True, is_delete=False)
                    post_data = post_filter(all_post, filter_by, user, offset=timezone)
                    obj = isinstance(post_data, list)
                    if obj:
                        paginator = Paginator(post_data, 10)
                        pages = paginator.page(page_number)
                        try:
                            pages = paginator.page(page_number)
                        except Exception:
                            return Response({"message": "Content not available", "success": True}, status=status.HTTP_200_OK)
                        pagination_data = {
                            "previous_page": pages.previous_page_number() if pages.has_previous() else pages.start_index(),
                            "current_page": pages.number,
                            "next_page": pages.next_page_number() if pages.has_next() else pages.paginator.num_pages,
                            "total_items": pages.paginator.count,
                            "total_pages": pages.paginator.num_pages,
                        }

                    data.append({
                        "pages": pagination_data,
                        "user_id": str(user.id),
                        "space_id": str(space.id),
                        "space_name": space.title,
                        "space_privacy": space.privacy,
                        "is_joined": is_joined,
                        "space_member_type": space_member_type,
                        "space_group_id": str(space.space_group.id),
                        "space_group_name": space.space_group.title,
                        "post": post_data
                    })

        response = {
            "message": "Public Post Data",
            "success": True,
            "data": data
        }
        return Response(response, status=status.HTTP_200_OK)