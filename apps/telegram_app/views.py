from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.status import *
# Create your views here.

from apps.users.models import TelegramUserData, User
from apps.atpace_community.models import Spaces, Post

# class TelegramUserData_API(APIView):
#     permission_classes = [AllowAny]
#     serializer_class = TelegramUserData_Serializer

#     def get(self,request):
#         data = request.data
#         serializer = TelegramUserData_Serializer(data=data)
#         if serializer.is_valid():
#             if data['user_id'] and data['message_id']:
#                 telegram_user = TelegramUserData.objects.filter(user_id=data['user_id'], message_id__lt=data['message_id']).first()
#                 print(telegram_user)
#                 return Response({'message':'success', 'response':str(telegram_user)}, status=HTTP_200_OK)
#         else: return Response({'message':'failed'}, status=HTTP_400_BAD_REQUEST)
    
#     def post(self,request):
#         data = request.data
#         serializer = TelegramUserData_Serializer(data=data)

#         if serializer.is_valid():
#             if data['user_id'] and data['username'] and data['description'] and data['message_id'] and data['is_command'] and data['chat_type']:
#             elif data['user_id'] and data['username'] and data['description'] and data['message_id']:
#                 TelegramUserData.objects.create(user_id=data['user_id'], username=data['username'], description=data['description'], message_id=data['message_id'])
#                 print("User created")
#             elif data['user_id'] and data['username'] and data['description'] and data['message_id'] and data['is_command']:
#                 TelegramUserData.objects.create(user_id=data['user_id'], username=data['username'], description=data['description'], message_id=data['message_id'], is_command=data['is_command'])
#                 print("User created")
#                 return Response({"message":"success"}, HTTP_200_OK)
#         else: return Response({"message":"failed"}, 400)

# class UserData_View(APIView):
#     permission_classes = [AllowAny]
#     def get(self,request):
#         data = request.data
#         print(data)

#         if first_name := data['first_name']:
#             db_user = User.objects.filter(first_name__icontains=first_name)
#         else:
#             return Response({'message':'success', 'response'})


class TelegramHelpAPI(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        data= request.data
        print(data)
        try:
            db_user = User.objects.filter(first_name__icontains=data['first_name'])
            
            if data['user_id'] and data['username'] and data['description'] and data['message_id'] and data['is_command'] and data['chat_type']:
                TelegramUserData.objects.create(user_id=data['user_id'], username=data['username'], description=data['description'], message_id=data['message_id'], is_command=data['is_command'], chat_type=data['chat_type'])
            
            elif data['user_id'] and data['username'] and data['description'] and data['message_id']:
                telegram_user = TelegramUserData.objects.create(user_id=data['user_id'], username=data['username'], description=['description'], message_id=data['message_id'])

            elif data['user_id'] and data['username'] and data['description'] and data['message_id'] and data['is_command']:
                TelegramUserData.objects.create(user_id=data['user_id'], username=data['username'], description=data['description'], message_id=data['message_id'], is_command=data['is_command'])

            return Response({'message':'success'}, 200)
        except Exception as e: return Response({'message':f'failed, {e}'}, 400)
    
class TelegramPostReplyAPI(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        data = request.data
        print(data)
        if data['yes'] == True:
            if data['user_id'] and data['message_id']:
                telegram_user = TelegramUserData.objects.filter(user_id=data['user_id'], message_id__lt=['message_id']).first()
                if telegram_user.url_link:
                    # space = Spaces.objects.get(id="d3f1459e-83f8-4908-bee2-b012cab397e5")
                    space = Spaces.objects.get(id=data['space_id'])
                    post = Post.objects.create(title=data['post_title'], Body=data['post_description'], space=space, space_group=space.space_group, created_by=space.created_by)
                    response = {
                        'message':'success',
                        'response':{'post_id':post.id, 'post_title':post.title}
                    }
                    return Response(response, 200)
        else:
            User.objects.filter(first_name__icontains=data['first_name'])
            telegram_user = TelegramUserData.objects.filter(user_id=data['user_id'], message_id__lt=data['message_id']).first()
            if telegram_user.url_link:
                TelegramUserData.objects.create(user_id=data['user_id'], username=data['username'], description=data['description'], message_id=data['message_id'])

class TelegramHandleMessageAPI(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        data = request.data
        print(data)
        
        telegram_user = TelegramUserData.objects.get(user_id=data['user_id'], username=data['username'], description=['description'], message_id=data['message_id'])
        if data['url_link'] == True:
            telegram_user.url_link = True
            telegram_user.save()
        return Response({'message':'success'}, 200)


        
