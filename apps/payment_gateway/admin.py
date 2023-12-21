from django.contrib import admin
from .models import CardDetails, Transaction , AddJourneyToCart

# Register your models here.
admin.site.register(CardDetails)
admin.site.register(Transaction)
admin.site.register(AddJourneyToCart)