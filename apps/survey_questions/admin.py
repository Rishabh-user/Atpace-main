from django.contrib import admin
from .models import (Answer,
                     Question,
                     Survey,
                     Options,
                     UserAnswer,
                     SurveyAttempt,
                     SurveyLabel)
# Register your models here.

admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(Options)
admin.site.register(Survey)
admin.site.register(UserAnswer)
admin.site.register(SurveyAttempt)
admin.site.register(SurveyLabel)
