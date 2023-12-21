import os
from pathlib import Path
import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "pt5fr1jpz+*$)mr(#w#h7=0t3sd^-&+b3h5=3*6y78m0&f@n"

APPEND_SLASH = True

# Application definition

DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'colorfield',
    'channels'
]

THIRD_PARTY_APPS = [
    'django_extensions',
    'crispy_forms',
    'rest_framework',
    'storages',
    'rest_framework.authtoken',
    'notifications',
    'user_visit',
    'django_user_agents',
    'django_crontab',
    'corsheaders',
    "debug_toolbar",
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',
    # 'allauth.socialaccount.providers.apple'
]

LOCAL_APPS = [
    'apps.users',
    'apps.survey_questions',
    'apps.feedback',
    'apps.content',
    'apps.test_series',
    'apps.community',
    'apps.webapi',
    'apps.utils',
    'apps.api',
    'apps.mentor',
    'apps.video_calling',
    'apps.users.templatetags',
    'apps.leaderboard',
    'apps.webapp',
    'apps.atpace_community',
    'apps.chat_app',
    'apps.push_notification',
    'apps.vonage_api',
    'apps.payment_gateway',
    'apps.program_manager_panel',
    'apps.learner_panel',
    'apps.mentor_panel',
    'apps.kpi',
    'apps.telegram_app',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

INSTALLED_APPS = DEFAULT_APPS + LOCAL_APPS + THIRD_PARTY_APPS

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user_visit.middleware.UserVisitMiddleware',
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

ROOT_URLCONF = 'ravinsight.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'ravinsight.context_processors.debug',
                'ravinsight.context_processors.get_footer',
                # 'ravinsight.context_processors.get_sidebar',
                'django.template.context_processors.request',
            ],
        },
    },
]

# WSGI_APPLICATION = 'ravinsight.wsgi.application'

# Channels
ASGI_APPLICATION = 'ravinsight.asgi.application'

SESSION_COOKIE_SECURE = False

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            # "hosts": [('127.0.0.1', 6379)],
            "hosts": [('redis://:mqxh492mj0SHSC8YRxoxWvQwBq5lrYQM@redis-19605.c212.ap-south-1-1.ec2.cloud.redislabs.com:19605')],
        },
    },
}

AUTH_USER_MODEL = 'users.User'
# SPACE_MODEL = 

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.users.backends.EmailBackend',
    # 'allauth.account.auth_backends.AuthenticationBackend'
]

# SITE_ID = 1

GOOGLE_CLIENT_KEY = '48095677608-s8sk01j4fhipaj25p8q644h30uctgfdr.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'

FACEBOOK_CLIENT_KEY = '423600063206280'
FACEBOOK_CLIENT_SECRET = 'ed04dfc685b52cc46dfcda9cbadb34d6'

# API Key for daily video call
API_KEY = "3097cfda7000870fff2426c391452ed6d12cf1ddab97830831fc3972c5b88e83"


# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = '/login'

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# MEDIA_URL = '/media/'
MEDIA_URL = 'https://atpace-storage.s3.ap-south-1.amazonaws.com/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# SMTP configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = "info@growatpace.com"
EMAIL_HOST_PASSWORD = "wyuprcuzycunfvmt"
EMAIL_PORT = 587 
EMAIL_USE_TLS = True

# DYTE CONFIGURATION
DYTE_BASE_URL = "https://api.dyte.io/v2"
DYTE_APP_URL = "https://growatpace.dyte.live/v2"
DYTE_ORG_ID = "1ea430b5-33f1-4ba5-af0f-62a4338c3e49"
DYTE_API_KEY = "d55c575d19ea9f7fada3"

# S3 configuration
AWS_ACCESS_KEY_ID = 'AKIA6MXK4RXL6LPMCSFZ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'atpace-storage'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

SUMMARY_ACCESS_ID = "AKIA6MXK4RXL2RHJFKLG"
SUMMARY_ACCESS_KEY = "eX9iKe2yCcJkTnUVb9SwKqAETtdOXF0CsU6tp7Ew"

# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
dir_path = str(BASE_DIR)+"/logs/web/{}".format(datetime.date.today())
if not os.path.isdir(dir_path):
    os.makedirs(dir_path)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': dir_path+"/debug.log",
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# apple creds
# APPLE_TEAM_ID = "M5XQ6M34PZ"
# APPLE_KEY_ID = "G83684CZKZ"
# APPLE_APP_ID = "com.atpace.applesignintestapp"
# APPLE_SERVICE_ID = "com.atpace.applesignintestservice"
# with open("static/cred/apple_private_key.p8", 'r') as f:
#     APPLE_PRIVATE_KEY = f.read().strip()

# # SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.providers.apple.adapter.AppleSocialAccountAdapter'

# SOCIALACCOUNT_PROVIDERS = {
#     "apple": {
#         "APP": {
#             # Your service identifier.
#             "client_id":APPLE_SERVICE_ID,
#             # The Key ID (visible in the "View Key Details" page).
#             "secret": APPLE_KEY_ID,
#             "key": APPLE_TEAM_ID,
#             "certificate_key": """-----BEGIN PRIVATE KEY-----
# MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgdbcsYevqOpa7gMbk
# TyRpLeWRf8qDKOMbr0njOFvILBWgCgYIKoZIzj0DAQehRANCAAT21wvqo/qmBG98
# S56A239Wbq1ELdXJhoTuLEtqUZKCBU08UqBBBksnOdsYdXNmm4ZKngytsR5hmNp3
# r/pOU9eZ
# -----END PRIVATE KEY-----"""
#                 }
#             }
#         }

# Last login check and ideal time session
CRONTAB_COMMAND_SUFFIX = '2>&1'
CRONJOBS = [
    
    ('0 9 * * 1', 'apps.users.cron.monday_jobs', '>>'+os.path.join(BASE_DIR, 'logs/cron/monday_jobs.log')),
    ('0 9 * * 5', 'apps.users.cron.every_friday', '>>'+os.path.join(BASE_DIR, 'logs/cron/to_lerner_message_scheduler.log')),
    ('*/10 * * * *', 'apps.users.cron.meeting_reminder', '>>'+os.path.join(BASE_DIR, 'logs/cron/meeting_reminder.log')),
    ('0 11 */10 * *', 'apps.users.cron.every_ten_days', '>>'+os.path.join(BASE_DIR, 'logs/cron/UserLastLogin.log')),
    ('*/1 * * * *', 'apps.users.cron.message_scheduler_and_task_reminder_and_rsvp_reminder', '>>'+os.path.join(BASE_DIR, 'logs/cron/MessageScheduler_TaskReminder.log')),
    ('0 0 * * *', 'apps.users.cron.event_collabrate_rsvp', '>>'+os.path.join(BASE_DIR, 'logs/cron/EventCollabrateRsvp.log')),
    ('*/5 * * * *', 'apps.users.cron.collabarate_event_notification', '>>'+os.path.join(BASE_DIR, 'logs/cron/CollabarateEventNotification.log')),
    ('0 8 * * *', 'apps.users.cron.risk_data_update', '>>'+os.path.join(BASE_DIR, 'logs/cron/risk_data_update.log')),
    ('0 9 * * 0', 'apps.users.cron.to_lerner_slot_scheduler', '>>'+os.path.join(BASE_DIR, 'logs/cron/to_lerner_slot_scheduler.log')),
    ('0 11 * * 5', 'apps.users.cron.unread_chat_and_open_slot', '>>'+os.path.join(BASE_DIR, 'logs/cron/unread_msg.log')),
    ('0 10 */7 * *', 'apps.users.cron.every_seven_days', '>>'+os.path.join(BASE_DIR, 'logs/cron/EverySevenDays.log')),
    ('0 11 * * 1,4', 'apps.users.cron.incomplete_profile_assessment', '>>'+os.path.join(BASE_DIR, 'logs/cron/IncompleteProfileAssessment.log')),
    ('* 9 * * 1', 'apps.users.cron.journey_new_content', '>>'+os.path.join(BASE_DIR, 'logs/cron/journey_new_content.log')),
    ('* 10 * * *', 'apps.users.cron.mentor_call_reminder', '>>'+os.path.join(BASE_DIR, 'logs/cron/mentor_call_reminder.log')),
    
    # not able to add it

]