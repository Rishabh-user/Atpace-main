from django.contrib import admin
from apps.mentor.models import *

class PoolMentorAdmin(admin.ModelAdmin):
    list_display = ('pool', 'mentor', 'pool_journey' )

    def pool_journey(self, obj):

        return obj.pool.journey
class MentorCalendarAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')

    def __str__(self):
        return self.title[:-5]
class DyteAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'email', 'meeting_id', 'preset')

class DyteMeetDetailsAdmin(admin.ModelAdmin):
    list_display = ('meet_id', 'meet_title', 'user_name', 'user_custom_id')

class MenteeSummaryAdmin(admin.ModelAdmin):
    list_display = ('id',)

class MentorSummaryAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(Pool)
admin.site.register(PoolMentor, PoolMentorAdmin)
admin.site.register(mentorCalendar, MentorCalendarAdmin)
admin.site.register(BookmarkMentor)
admin.site.register(AssignMentorToUser)
admin.site.register(AllMeetingDetails)
admin.site.register(MeetingParticipants)
admin.site.register(DyteAuthToken,DyteAuthTokenAdmin)
admin.site.register(DyteMeetDetails, DyteMeetDetailsAdmin)
admin.site.register(MenteeSummary, MenteeSummaryAdmin)
admin.site.register(MentorSummary, MentorSummaryAdmin)