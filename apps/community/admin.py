from django.contrib import admin

from apps.community.models import AddMemberToSpace, CicleDataDump, CommunityPost, CommunityPostComment, JourneySpace, LearningJournals, LearningJournalsAttachment, LearningJournalsComments, UserCircleDetails, WeeklyLearningJournals, WeeklyjournalsTemplate

# Register your models here.


class CicleDataDumpAdmin(admin.ModelAdmin):
    list_display = ('pk', 'type')

class LearningJournalsAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "user_name", "is_weekly_journal", "weekely_journal_id")
    list_filter = ('is_weekly_journal', 'weekely_journal_id')


admin.site.register(JourneySpace)
admin.site.register(CicleDataDump, CicleDataDumpAdmin)
admin.site.register(CommunityPost)
admin.site.register(AddMemberToSpace)
admin.site.register(UserCircleDetails)
admin.site.register(CommunityPostComment)
admin.site.register(LearningJournals, LearningJournalsAdmin)
admin.site.register(LearningJournalsComments)
admin.site.register(WeeklyLearningJournals)
admin.site.register(WeeklyjournalsTemplate)
admin.site.register(LearningJournalsAttachment)