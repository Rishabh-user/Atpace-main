
from django.shortcuts import render, redirect
from django.urls import reverse
from apps.users.models import User
from .models import Chat, Room as AllRooms
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.utils.decorators import method_decorator

@login_required
def GroupName(request):
    return render(request,   'chat/group_name.html', {})


@login_required
def UserAllRooms(request):
    # all_rooms = AllRooms.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    all_rooms = AllRooms.objects.filter(Q(user1=request.user) | Q(user2=request.user), user1__is_active=True, user2__is_active=True, user1__is_delete=False, user2__is_delete=False)
    return render(request, 'chat/room.html', {"all_rooms": all_rooms})


@login_required
def Room(request, room_name):
    all_rooms = AllRooms.objects.filter(Q(user1=request.user) | Q(user2=request.user), user1__is_active=True, user2__is_active=True, user1__is_delete=False, user2__is_delete=False)
    my_room = AllRooms.objects.get(name=room_name)
    # print("chat views file", all_rooms.values())
    # print(my_room.user2)

    chats = Chat.objects.filter(Q(from_user=my_room.user1) & Q(to_user=my_room.user2) | Q(
        from_user=my_room.user2) & Q(to_user=my_room.user1)).order_by('timestamp')
    # print(chats)
    logged_user = request.user

    return render(request, 'chat/room.html', {
        "all_rooms": all_rooms,
        'room_name': room_name,
        'chats': chats,
        'logged_user': logged_user
    })


# @method_decorator(login_required, name='dispatch')
# def create_group(request):
#     return redirect(reverse('users:user_chat'))
