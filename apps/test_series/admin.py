from django.contrib import admin
from .models import (TestSeries,
                     TestQuestion,
                     TestOptions)
# Register your models here.

admin.site.register(TestSeries)
admin.site.register(TestQuestion)
admin.site.register(TestOptions)

