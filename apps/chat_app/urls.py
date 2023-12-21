# chat/urls.py
from django.urls import path

from . import views 

app_name = 'chat_app'
urlpatterns = [
    path('', views.UserAllRooms, name='group-name'),
    path('<str:room_name>/', views.Room, name='room'),
    # path('create-group/', views.create_group, name="create_group"),


]