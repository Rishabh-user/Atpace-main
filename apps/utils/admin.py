from django.contrib import admin
from .models import Industry, JourneyCategory, Tags, UrlShortner
# Register your models here.


admin.site.register(JourneyCategory)
admin.site.register(Tags)
admin.site.register(Industry)
admin.site.register(UrlShortner)
