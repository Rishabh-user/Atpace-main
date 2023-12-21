from calendar import c
from os import name
from django.db import models
from django.db.models.deletion import CASCADE
import uuid
from colorfield.fields import ColorField
from django.db.models.signals import pre_save
from django.dispatch import receiver
# Create your models here.


class Timestamps(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ModelActiveDelete(models.Model):
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    class Meta:
        abstract = True

class JourneyCategory(models.Model):
    category = models.CharField(max_length=100)
    color = ColorField(default="#000000")
    icon = models.ImageField(upload_to='category/icon/', default="")
    parent_id = models.ForeignKey("self", on_delete=CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.category

class Tags(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    alernate_name = models.CharField(max_length=200)
    color = ColorField(default='#423282')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Industry(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    alernate_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Languages(models.Model):
    name = models.CharField(max_length=100)
    short_form = models.CharField(max_length=100)
    language_code = models.CharField(max_length=100)
    text_direction = models.CharField(max_length=100)
    text_editor_lang = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    language_order = models.IntegerField(default=1)


class language_translations(models.Model):
    lang_id = models.IntegerField()
    label = models.CharField(max_length=100)
    translation = models.CharField(max_length=255)
    
class EmailStatusList(Timestamps):
    Choices = (
        ("OTP","OTP"),
        ("Assessment","Assessment"),
        ("Register","Register"),
        ("Survey","Survey"),
        ("journey_Enroll","journey_Enroll"),
        ("Journey_Complete","Journey_Complete")
    )
    subject = models.CharField(max_length=200)
    body = models.CharField(max_length=1000)
    email = models.EmailField(max_length=254)
    type = models.CharField(max_length=50, choices=Choices)
    status = models.IntegerField(True)


class UrlShortner(Timestamps):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_url = models.CharField(max_length=255)
    long_url = models.TextField()
    count = models.IntegerField(default=0)