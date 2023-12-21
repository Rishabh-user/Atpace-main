from django.contrib import admin
from apps.mentor_panel.models import WorkExperience, MentoringTypes, TargetAudience, MentorMarketPlaceCertificates, \
    MentorMarketPlace, MentorMarketPlaceEducation
# Register your models here.


admin.site.register(WorkExperience)
admin.site.register(MentoringTypes)
admin.site.register(TargetAudience)
admin.site.register(MentorMarketPlaceCertificates)
admin.site.register(MentorMarketPlace)
admin.site.register(MentorMarketPlaceEducation)