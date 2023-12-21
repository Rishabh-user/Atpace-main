from django.urls import path
from .views import TelegramHelpAPI,TelegramPostReplyAPI
urlpatterns = [
    path('help', TelegramHelpAPI.as_view(), name="Telegram Help" ),
    path('post-reply', TelegramPostReplyAPI.as_view(), name="Telegram Post Reply" ),
]