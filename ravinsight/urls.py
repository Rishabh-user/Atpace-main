"""ravinsight URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, re_path
from django.urls.conf import include

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import debug_toolbar
from django.views.generic.base import TemplateView

# from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView, OAuth2LoginView  
# from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
# import notifications.urls
urlpatterns = [
    path('server-admin/', admin.site.urls),
    path('', include('apps.users.urls')),
    path('survey/', include('apps.survey_questions.urls')),
    path('feedback/', include('apps.feedback.urls')),
    path('website/', include('apps.webapp.urls')),
    path('content/', include('apps.content.urls')),
    path('test-series/', include('apps.test_series.urls')),
    path('community/', include('apps.community.urls')),
    path('atpace-community/', include('apps.atpace_community.urls')),
    path('push-notification/', include('apps.push_notification.urls')),
    path('leaderboard/', include('apps.leaderboard.urls')),
    path('api/', include('apps.api.urls')),
    path('api-v1/', include('apps.webapi.urls')),
    path('config/', include('apps.utils.urls')),
    path('call/', include('apps.video_calling.urls')),
    path('chat/', include('apps.chat_app.urls')),
    path('telegram/', include('apps.telegram_app.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path("verifyzoom.html", TemplateView.as_view(template_name="zoomverify/verifyzoom.html")),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt",
                                            content_type="text/plain")),
    path(".well-known/assetlinks.json", TemplateView.as_view(template_name="assetlinks.json",
                                            content_type="application/json")),
    path("apple-app-site-association", TemplateView.as_view(template_name="ios_deeplink.json",
                                            content_type="application/json")),
    # path('checkout/', include('apps.payment_gateway.urls')),
    path('kpi_urls/', include('apps.kpi.urls')),
    path('checkout/', include('apps.payment_gateway.urls')),
    path('manager/', include('apps.program_manager_panel.urls')),
    path('learner/', include('apps.learner_panel.urls')),
    path('mentor/', include('apps.mentor_panel.urls')),

    # path('accounts/', include('allauth.urls')),
    # path('apple/login', OAuth2LoginView.as_view())


    # url('^inbox/notifications/', include(notifications.urls, namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += [
        # path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
