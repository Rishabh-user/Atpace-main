from django.urls import re_path

from . import consumers
from apps.api.views import Mentor_User

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),

    re_path(r'ws/chat/(?P<uuid>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})/(?P<room_name>\w+)/$',
            Mentor_User.ChatConsumer.as_asgi()),
]
