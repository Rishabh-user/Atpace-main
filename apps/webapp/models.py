from django.db import models
from apps.content.models import Channel
from apps.users.models import User
from apps.utils.models import Timestamps
# Create your models here.

class GeneralSettings(models.Model):
    site_title = models.CharField(max_length= 255)
    home_title = models.CharField(max_length= 255)
    Countries = models.CharField(max_length= 255)
    site_description = models.TextField()
    application_name = models.CharField(max_length= 100)
    facebook_url = models.URLField(max_length=200, blank=True)
    twitter_url = models.URLField(max_length=200, blank=True)
    instagram_url = models.URLField(max_length=200, blank=True)
    pinterest_url = models.URLField(max_length=200, blank=True)
    linkedin_url = models.URLField(max_length=200, blank=True)
    vk_url = models.URLField(max_length=200, blank=True)
    telegram_url = models.URLField(max_length=200, blank=True)
    youtube_url = models.URLField(max_length=200, blank=True)
    about_footer = models.TextField()
    contact_text = models.TextField()
    contact_address = models.CharField(max_length= 255)
    contact_email  = models.EmailField()
    contact_phone  = models.CharField(max_length= 255)
    copyright = models.CharField(max_length= 255)
    cookies_warning   = models.BooleanField(default = False)
    cookies_warning_text = models.TextField()

class contact_us(models.Model):
    name = models.CharField(max_length = 100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    profession = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_term_apply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    
class Review(models.Model):
    name = models.CharField(max_length = 100)
    email = models.EmailField()
    title = models.CharField(max_length = 100)
    summary = models.TextField()
    rating = models.IntegerField(default = 1)
    user_type = models.CharField(max_length = 20)
    user_id = models.CharField(max_length = 30)
    created_at = models.DateTimeField(auto_now_add=True)

class GrowAtpaceTeam(models.Model):
    name = models.CharField(max_length = 100)
    country = models.CharField(max_length = 100)
    position = models.CharField(max_length = 100)
    linkedin_url =  models.URLField(blank = True, null=True)
    facebook_url= models.URLField(blank = True, null=True)
    instagram_url =  models.URLField(blank = True, null=True)
    about_us = models.TextField(null = True, blank=True)
    profile =  models.ImageField(upload_to='website/team/')
    is_active = models.BooleanField(default = False)
    display_order = models.IntegerField(default = 0)


class HomepageJourneys(models.Model):
    journey = models.ForeignKey(Channel, on_delete=models.CASCADE)
    is_display = models.BooleanField(default = True)
    display_order = models.IntegerField(default = 0)

class subscribeEmails(Timestamps):
    subscriber_mail = models.EmailField(max_length=254, unique=True)

class Testimonial(models.Model):
    name = models.CharField(max_length = 100)
    position = models.CharField(max_length = 100)
    message = models.TextField()

class DeviceDetails(Timestamps):
    OS_Type = (
        ("Linux", "Linux"),
        ("iOS", "iOS"),
        ("Android", "Android"),
        ("Windows", "Windows"),
    )
    Device_Type = (
        ("Pc","Pc"),
        ("Mobile", "Mobile"),
        ("Tablet", "Tablet"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    os_type = models.CharField(max_length=50, choices=OS_Type, default="Windows")
    os_version = models.CharField(max_length=50)
    device_type = models.CharField(max_length=50, choices=Device_Type, default="Pc")
    device = models.CharField(max_length=50)