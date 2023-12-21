from django.contrib import admin
from .models import DeviceDetails, GrowAtpaceTeam, HomepageJourneys, contact_us, Review, subscribeEmails, Testimonial
# Register your models here.

admin.site.register(contact_us)
admin.site.register(Review)
admin.site.register(GrowAtpaceTeam)
admin.site.register(HomepageJourneys)
admin.site.register(subscribeEmails)
admin.site.register(Testimonial)
admin.site.register(DeviceDetails)