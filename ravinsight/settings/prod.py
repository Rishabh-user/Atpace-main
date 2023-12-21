from sentry_sdk.integrations.django import DjangoIntegration
import sentry_sdk

import os
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['growatpace.com']


CORS_ALLOWED_ORIGINS = [
    "https://forum.growatpace.com",
    "http://forum.growatpace.com",
]

DATABASES = {
    'default':{
        'ENGINE': 'django.db.backends.mysql',
        'NAME': "atpace",
        'USER': 'atpaceuser',
        'PASSWORD': '#$%Atpace#$%1234',
        'HOST': 'atpace-db.clotrw59hjr4.ap-south-1.rds.amazonaws.com',
        'PORT': '3306',
    }
}



STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Payment configuration
BRAINTREE_PRODUCTION = True
BRAINTREE_MERCHANT_ID = 'fyzwhs27p27rb5ct'
BRAINTREE_PUBLIC_KEY = '53f37cwc85jvk7qx'
BRAINTREE_PRIVATE_KEY = '961e8326766aa8cf4a93fe9fe74205f9'

sentry_sdk.init(
    dsn="https://60c085545ce44f5ba3c872345a88fcea@o4504252633513984.ingest.sentry.io/4504252635021312",
    integrations=[
        DjangoIntegration(),
    ],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)