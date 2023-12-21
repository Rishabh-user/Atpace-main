from multiprocessing import Event
from django.core.paginator import Paginator
from django.forms import model_to_dict
from apps.api.serializers import UserIdSerializer, GetRSVPResponseSerializer
from notifications.models import Notification
from apps.users.models import Collabarate, User
from rest_framework import status
from rest_framework.views import APIView
from apps.api.utils import check_valid_user
from rest_framework.response import Response


class live_all_notification_count(APIView):
    def get(self, request, user_id):
        data = {"user_id": str(user_id)}
        print(data)
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({"message": "No data Found",  "success": False}, status=status.HTTP_404_NOT_FOUND)
            all_count = Notification.objects.filter(recipient=user).count()
            print(all_count)
            response = {
                "message": "Success",
                "success": True,
                "data": {
                    "count": all_count
                }
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


def id2slug(notification_id):
    return notification_id + 110909


class live_all_notification_list(APIView):
    def get(self, request, user_id):
        data = {"user_id": str(user_id)}
        print(data)
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({"message": "No data Found",  "success": False}, status=status.HTTP_404_NOT_FOUND)

            unread_list = []
            for notification in Notification.objects.filter(recipient=user):
                struct = model_to_dict(notification)
                struct['slug'] = id2slug(notification.id)
                if notification.actor:
                    struct['actor'] = str(notification.actor)
                if notification.target:
                    struct['target'] = str(notification.target)
                if notification.action_object:
                    struct['action_object'] = str(notification.action_object)
                if notification.data:
                    struct['data'] = notification.data
                unread_list.append(struct)
            pagination = ''
            obj = isinstance(unread_list, list)
            if obj:
                paginator = Paginator(unread_list, 10)
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
                "message": "All Notification list",
                "success": True,
                "data": {
                    "pages": pagination,
                    "data": pages.object_list if obj else unread_list
                }
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)


class MeetRSVPResponse(APIView):
    def post(self, request):
        data = request.data
        serializer = GetRSVPResponseSerializer(data=data)
        if serializer.is_valid():
            user = check_valid_user(data['user_id'])
            if not user:
                return Response({"message": "Invalid User_id", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                meet_type = data['meet_type']
                if meet_type == 'LiveStreaming' or 'GroupStreaming':
                    meet = Collabarate.objects.get(id=data['meet_id'])
                else:
                    meet = Event.objects.get(id=data['meet_id'])
            except:
                return Response({"message": "Meet id does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            response = data['response']
            rsvp_res = MeetRSVPResponse.objects.filter(user=user, meet_id=meet.id).fisrt()
            if rsvp_res:
                rsvp_res.response = response
                rsvp_res.save()
            else:
                MeetRSVPResponse.objects.create(user=user, response=response, meet_id=meet.id, meet_type=meet_type)
            response = {
                "message": "Success",
                "success": True
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors,  "success": False}, status=status.HTTP_400_BAD_REQUEST)
