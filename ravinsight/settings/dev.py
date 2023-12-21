from sentry_sdk.integrations.django import DjangoIntegration
import sentry_sdk

import os

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOWED_ORIGINS = [
    "http://forum.dev.growatpace.com",
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CORS_ALLOWED_ORIGINS = [
    "https://forum.dev.growatpace.com",
    "http://forum.dev.growatpace.com",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8000",
]


STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Payment configuration
BRAINTREE_PRODUCTION = False
BRAINTREE_MERCHANT_ID = '854hdy5fnjg48j6b'
BRAINTREE_PUBLIC_KEY = 'hcwwfv4x6kd6mnnm'
BRAINTREE_PRIVATE_KEY = 'c4b6c9f2197a1cbd53a06ded7f34e898'


INTERNAL_IPS = [
    "127.0.0.1",
]

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
