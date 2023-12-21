from django.contrib import admin
from django.contrib.admin.decorators import display
from django.db import models
from .models import (Channel,
                     ContentData, VideoSubtitles,
                     Content, MentoringJourney, ProgramTeamAnnouncement, SurveyAttemptChannel, SurveyChannel,
                     UserChannel,
                     ChannelGroup,
                     UserChannelLevel,
                     ChannelGroupContent,
                     ContentDataOptions,
                     ContetnOptionSubmit,
                     TestAttempt,
                     UserTestAnswer,
                     SkillConfig,
                     SkillConfigLevel,
                     UserCourseStart,
                     UserReadContentData,
                     MatchQuesConfig,
                     MatchQuestion,
                     ProgramAnnouncementWhatsappReport,
                     journeyContentSetup,
                     JourneyContentSetupOrdering,
                     PublicProgramAnnouncement,
                     UserActivityData,
                     CertificateTemplate,
                     CertificateSignature,
                     UserCertificate,
                     )
# Register your models here.


class UserChannelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'Channel', 'status')


class ChannelGroupContentAdmin(admin.ModelAdmin):
    list_display = ('channel_group', 'content', 'display_order')
    list_editable = ['display_order']


class ContentDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'content', 'type', 'display_order')
    list_filter = ('content', 'type')


class VideoSubtitlesAdmin(admin.ModelAdmin):
    list_display =('id', 'video_id', 'lang_type')


class ChannelAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', "channel_type")


class ChannelGroupAdmin(admin.ModelAdmin):
    list_display = ('channel_for', 'title', 'channel')


class UserCourseStartAdmin(admin.ModelAdmin):
    list_display = ("user", 'channel_group', 'content', 'status')


class JourneyContentSetupOrderingAdmin(admin.ModelAdmin):
    list_display = ('journey', 'type', 'data', 'display_order')
    list_editable = ['display_order']

admin.site.register(Channel, ChannelAdmin)
admin.site.register(Content)
admin.site.register(ContentData, ContentDataAdmin)
admin.site.register(VideoSubtitles, VideoSubtitlesAdmin)
admin.site.register(ContentDataOptions)
admin.site.register(ChannelGroup, ChannelGroupAdmin)
admin.site.register(UserChannel, UserChannelAdmin)
admin.site.register(UserChannelLevel)
admin.site.register(ChannelGroupContent, ChannelGroupContentAdmin)
admin.site.register(ContetnOptionSubmit)
admin.site.register(TestAttempt)
admin.site.register(UserTestAnswer)
admin.site.register(SkillConfig)
admin.site.register(UserCourseStart, UserCourseStartAdmin)
admin.site.register(SurveyChannel)
admin.site.register(SurveyAttemptChannel)
admin.site.register(UserReadContentData)
admin.site.register(MentoringJourney)
admin.site.register(ProgramTeamAnnouncement)
admin.site.register(MatchQuestion)
admin.site.register(MatchQuesConfig)
admin.site.register(ProgramAnnouncementWhatsappReport)
admin.site.register(journeyContentSetup)
admin.site.register(JourneyContentSetupOrdering, JourneyContentSetupOrderingAdmin)
admin.site.register(PublicProgramAnnouncement)
admin.site.register(UserActivityData)
admin.site.register(CertificateTemplate)
admin.site.register(CertificateSignature)
admin.site.register(UserCertificate)
admin.site.register(SkillConfigLevel)
