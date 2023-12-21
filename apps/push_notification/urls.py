from django.urls import path
from .views import *

app_name = 'push_notification'

urlpatterns = [
    # path('in/', index, name="index"),
    path('send/', send),
    path('get-token', get_token, name="get_device_token"),
    path('firebase-messaging-sw.js', showFirebaseJS, name="show_firebase_js"),
    path("all/", get_notification, name="show_notification"),
]
