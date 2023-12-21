from pickle import FALSE
from django.shortcuts import render, redirect
from django.urls import reverse
import requests
import json
from django.http import HttpResponse, JsonResponse
from apps.users.models import FirebaseDetails
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from notifications.models import Notification
from django.core.paginator import Paginator
from apps.atpace_community.utils import time_ago
# Create your views here.


def send_notification(registration_ids, message_title, message_desc, context=None):
    fcm_api = "AAAAKeZ9DfI:APA91bGsuvmBhlp1hiRJ5pqKqyJvGxNqzjp7PosTbIpYzW9RffLoLIYRmu8uDTQJaEbMli9939ponl1bfEc64iHcdbMD1LwuUjA7yf3Ewb7zdjn40t8WJ4a4LlsFZlMhnbStGBU0eJo3"
    url = "https://fcm.googleapis.com/fcm/send"

    headers = {"Content-Type": "application/json", "Authorization": f'key={fcm_api}'}
    payload = {
        "registration_ids": registration_ids,
        "priority": "high",
        "notification": {
            "body": message_desc,
            "title": message_title,
            # "image": "	https://growatpace.com/static/website/img/logo.png",
            "icon": "images/logo/at-pace-logo-icon.png"

        },
        "data": context
    }
    # print("pAYLOAD FOR noTIFIcation", payload)
    result = requests.post(url,  data=json.dumps(payload), headers=headers)
    # if result.status_code == 200 or result.status_code == 201:
    #     print("Notification sent")
    # print(result.json())


def get_token(request):
    if request.method == "POST":
        token = request.POST.get('token')
        print(token)
        # device_id = request.POST.get('device_id')
        try:
            firebase_details = FirebaseDetails.objects.get(user=request.user, device_id="")
            print("previous token ", firebase_details.firebase_token)
            firebase_details.firebase_token = token
            firebase_details.save()
            print("updated token ", firebase_details.firebase_token)
        except FirebaseDetails.DoesNotExist:
            FirebaseDetails.objects.create(firebase_token=token, device_id="", user=request.user)
        return HttpResponse("True")
    return HttpResponse("False")


def send(request):
    firebase = FirebaseDetails.objects.all()
    resgistration = [token.firebase_token for token in firebase]
    print(resgistration[:5])
    # resgistration = [
    #     'cDxFwclVBFXZBl5_aOECqS:APA91bHLdor1o4UQpZclnkVocdv-e6GgF8hs9r2jBVpAHFtzKLGHoDtKfdTxYK8CkDKJdZDLDApfgnvumYnYCp6loscpjyg9jHN8oBYzFDr6tlENrhdEgE1SWJcXlSjk8VGsQ-l_FzlV'
    #     'efilD5H2SYmRzFPYGJ6Yz6:APA91bGi1AKdt6T-GQWJJX7tint7_SebEanSFtGjDcxrw8sEdYuNblbi0JKqQh2DsvCnJRwfGgvGa1qLOvGLfz4-AFhFd5gHk-ehl50xR2tZ7jG3Gt49EFNW3cJP11qIgV7Hb0i4lLQH'
    # ]
    send_notification(resgistration, 'Growatpace', 'growatpace new video alert')
    return HttpResponse("sent")


def showFirebaseJS(request):
    data = 'importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-app.js");' \
        'importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-messaging.js"); ' \
        'var firebaseConfig = {' \
        '        apiKey: "AIzaSyBF5_N7gLh5bS-DX-zsJWAflA_eY1GKixI",' \
        '        authDomain: "atpacce-91da3.firebaseapp.com",' \
        '        projectId: "atpacce-91da3",' \
        '        storageBucket: "atpacce-91da3.appspot.com",' \
        '        messagingSenderId: "179960614386",' \
        '        appId: "1:179960614386:web:5526ced85b3d4203e4af6b",' \
        '        measurementId: "G-BGL17Q76NV"' \
        ' };' \
        'firebase.initializeApp(firebaseConfig);' \
        'const messaging=firebase.messaging();' \
        'messaging.setBackgroundMessageHandler(function (payload) {' \
        '    console.log(payload);' \
        '    const notification=JSON.parse(payload);' \
        '    const notificationOption={' \
        '        body:notification.body,' \
        '        icon:notification.icon' \
        '    };' \
        '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
        '});'

    return HttpResponse(data, content_type="application/javascript")

@login_required
def get_notification(request):

    notification__list = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    per_page = 10
    p = Paginator(notification__list, per_page)
    # list of objects on first page
    data = p.page(1).object_list
    # print("data", data)
    # range iterator of page numbers
    page_range = p.page_range
    # print("page_range", page_range)
    noti_list = []
    for d in data:
        noti_list.append({
            "description": d.description,
            "timestamp": time_ago(d.timestamp),
        })

    context = {
        'notification__list': noti_list,
        'page_range': page_range
    }

    if request.method == 'POST':
        # getting page number
        page_no = request.POST.get('page_no', 1)
        data = p.page(page_no).object_list
        noti_list = []
        for d in data:
            noti_list.append({
                "description": d.description,
                "timestamp": time_ago(d.timestamp),
            })

        return JsonResponse({"results": noti_list, "is_next": p.page(page_no).has_next(), "is_previous": p.page(page_no).has_previous()})

    return render(request, 'notifications.html', context)
