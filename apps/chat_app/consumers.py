from cgitb import text
from datetime import datetime
import json

from requests import request
from apps.api.utils import chat_notification
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Chat, Room as AllRooms
from apps.users.models import User
from apps.vonage_api.utils import send_chat_info
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from apps.users.utils import convert_to_local_time, convert_to_utc
from channels.db import database_sync_to_async


@method_decorator(login_required, name='dispatch')
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        print("Websocket connected")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code,):
        print("Websocket disconnected", close_code)
        # Leave room group
        result = await database_sync_to_async(self.update_status)()
        print(result)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self,request, text_data=None, bytes_data=None):
        print("bytes data", bytes_data)
        text_data_json = json.loads(text_data)
        print("text_data_json", text_data_json, type(text_data_json))
        message = text_data_json['message']
        print("message", message, type(message))

        self.user_id = self.scope['user'].id
        from_user = self.scope["user"]
        # print("from_user", from_user, self.user_id)
        user_id = self.user_id
        room_name = self.room_name
        # print("from_user", from_user)
        my_room = await database_sync_to_async(AllRooms.objects.get)(name=room_name)
        print("my_room", my_room.type)
        if(my_room.type == 'OneToOne'):
            to_user = await database_sync_to_async(User.objects.get)(pk=my_room.user2_id)

            if to_user == from_user:
                to_user = await database_sync_to_async(User.objects.get)(pk=my_room.user1_id)

            print("to_user", to_user.id)

            result = await database_sync_to_async(self.check_status)(to_user)
            print("User Status of ", to_user, "is", result)
            if(result == False):

                print("Send Notification")
                # if to_user.phone and to_user.is_whatsapp_enable:
                #     send_chat_info(to_user, message)
                # else:
                #     print("no phone number exist")

                await chat_notification(result, to_user, from_user, message, my_room)


            chat = Chat(
                from_user=from_user,
                to_user=to_user,
                message=message,
                # created_at= convert_to_utc(datetime.now(), request.session['timezone'])
                is_read=True
            )

        else:
            chat = Chat(
                from_user=from_user,
                message=message,
                room=my_room,
            )
        my_room.updated_at = datetime.now()
        await database_sync_to_async(my_room.save)()
        print("line 54", from_user)
        # await database_sync_to_async(chat.read_by.add)(from_user)
        await database_sync_to_async(chat.save)()

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': str(user_id),
                "from_user": from_user.first_name + " " + from_user.last_name
            }
        )

    def get_rooms(self):
        all_rooms = AllRooms.objects.get(name="mentoruser")
        # print(all_rooms, "line 72")
        return all_rooms

    def update_status(self):
        logged_user = self.scope['user'].id
        # print(logged_user)
        user = User.objects.get(pk=logged_user)
        # print("user_status1", user.user_status)
        user.user_status = False
        user.save()
        # print("user_status2", user.user_status)
        return "True"

    def check_status(self, to_user):
        user = User.objects.get(pk=to_user.id)
        # print(user.user_status)
        return user.user_status

    # Receive message from room group

    async def chat_message(self, event):
        message = event['message']
        # print("event", event)
        user_id = event['user_id']
        from_user = event['from_user']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user_id': user_id,
            'from_user': from_user
        }))
