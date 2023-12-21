from datetime import datetime
from django.shortcuts import redirect
import requests
import json
from .models import Room, RoomProperties
from django.shortcuts import render
from apps.users.models import User
from ravinsight.settings import API_KEY

def index(request, metting_id):
    room = Room.objects.get(id=metting_id)
    print(room)
    context = {
        "room_url": room.url,
        "token": room.token
    }
    return render(request, "meeting.html", context=context)


def Profile_Details(request):
    url = "https://api.daily.co/v1/"
    headers = {'Authorization': 'Bearer {}'.format(API_KEY)}
    response = requests.request("GET", url, headers=headers)
    context = {
        "data": response.json(),
    }
    print(response.json())
    return render(request, 'Profile_details.html', context)


def rooms(request):
    url = "https://api.daily.co/v1/rooms"
    headers = {'Authorization': 'Bearer {}'.format(API_KEY)}
    response = requests.request("GET", url, headers=headers)
    context = {
        "data": response.json(),
    }
    print(response.json())
    return render(request, 'rooms.html', context)


def roomss(request):
    Uroom = Room.objects.filter(user=request.user)
    print(Uroom)
    print(request.user)
    Proom = Room.objects.filter(Participants=request.user)
    print(Proom)
    context = {
        'Uroom': Uroom,
        'Proom': Proom

    }
    return render(request, 'rooms.html', context=context)


def create_rooms(request):
    if request.method == 'POST':
        name = request.POST['name']
        privacy = request.POST['privacy']
        dateti = request.POST['date']
        dateti = dateti.replace('T', ' ')
        exp = datetime.strptime(dateti, '%Y-%m-%d %H:%M')
        nbf = datetime.strftime(exp, "%s")
        print("exp", exp)
        print("exp", nbf)
        enable_new_call_ui = request.POST['enable_new_call_ui']
        enable_prejoin_ui = request.POST['enable_prejoin_ui']
        enable_knocking = request.POST['enable_knocking']
        enable_screenshare = request.POST['enable_screenshare']
        enable_video_processing_ui = request.POST['enable_video_processing_ui']
        enable_chat = request.POST['enable_chat']
        start_video_off = request.POST['start_video_off']
        start_audio_off = request.POST['start_audio_off']
        owner_only_broadcast = request.POST['owner_only_broadcast']
        is_owner = request.POST['is_owner']
        Participants = User.objects.get(pk=request.POST['participants'])
        context = json.dumps({
            "name": name,
            "privacy": privacy,
            "properties": {
                "start_audio_off": start_audio_off,
                "start_video_off": start_video_off,
                "enable_new_call_ui": enable_new_call_ui,
                "enable_prejoin_ui": enable_prejoin_ui,
                "enable_knocking": enable_knocking,
                "enable_screenshare": enable_screenshare,
                "enable_video_processing_ui": enable_video_processing_ui,
                "enable_chat": enable_chat,
                # "owner_only_broadcast":owner_only_broadcast,
            }
        })
        print("context", context)
        url = "https://api.daily.co/v1/rooms"
        headers = {'Authorization': 'Bearer {}'.format(API_KEY)}
        response = requests.request("POST", url, headers=headers, data=context)
        res = response.json()
        print(res)
        token = ""
        if res['privacy'] == 'private':
            context = json.dumps({"properties":
                                  {
                                      "room_name": res['name'],
                                      "is_owner": is_owner,
                                  }
                                  })
            print("is_owner", is_owner)
            url = 'https://api.daily.co/v1/meeting-tokens'
            headers = {'Authorization': 'Bearer {}'.format(API_KEY)}
            response = requests.request("POST", url, headers=headers, data=context)
            res1 = response.json()
            token = res1['token']

        properties = RoomProperties.objects.create(id=res['id'], start_audio_off=start_audio_off,
                                                   start_video_off=start_video_off,
                                                   enable_new_call_ui=enable_new_call_ui,
                                                   enable_prejoin_ui=enable_prejoin_ui,
                                                   enable_knocking=enable_knocking,
                                                   enable_screenshare=enable_screenshare,
                                                   enable_video_processing_ui=enable_video_processing_ui,
                                                   enable_chat=enable_chat,
                                                   owner_only_broadcast=owner_only_broadcast,
                                                   datetime=dateti)
        properties.save()
        property = RoomProperties.objects.get(id=res['id'])
        print("property", property)
        room = Room.objects.create(name=res['name'], id=res['id'], Participants=Participants, api_created=res['api_created'],
                                   privacy=res['privacy'], url=res['url'], created_at=res['created_at'], user=request.user, token=token, properties=property)
        room.save()

        return redirect('roomss')
    context = {
        "user": User.objects.all()
    }
    return render(request, 'create_rooms.html', context=context)


def roomDetails(request, name):
    url = "https://api.daily.co/v1/rooms/{}".format(name)
    headers = {'Authorization': 'Bearer {}'.format(API_KEY)}
    response = requests.request("GET", url, headers=headers)
    context = {
        "data": response.json(),
    }
    print(context['data'])
    return render(request, 'room.html', context)


def updateRoom(request):
    if request.method == 'POST':
        name = request.POST['name']
        privacy = request.POST['privacy']
        context = json.dumps({
            "name": name,
            "privacy": privacy,
            "properties": {
                "start_audio_off": True,
                "start_video_off": True
            }
        })
        url = "https://api.daily.co/v1/rooms/{}".format(name)
        headers = {'Authorization': 'Bearer {}'.format(API_KEY)}
        response = requests.request("POST", url, headers=headers, data=context)
        res = response.json()
        print(res)
        Room.objects.filter(name=res['name']).update(privacy=res['privacy'])
        return render(request, 'update-room.html')
    return render(request, 'update-room.html')

def dyte(request):
    return render(request, 'dyte.html')
