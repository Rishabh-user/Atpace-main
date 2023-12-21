from django.contrib import admin
from .models import VonageApiHistory, VonageWhatsappReport
# Register your models here.

admin.site.register(VonageApiHistory)
admin.site.register(VonageWhatsappReport)