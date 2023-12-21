from django.contrib import admin
from .models import *

# Register your models here.



class SpaceMembersAdmin(admin.ModelAdmin):
    list_display = ('user', 'space', 'space_group', 'user_type', 'is_joined')
    list_filter = ('space', 'space_group', 'user_type', "is_joined")

class ContentReview(admin.ModelAdmin):
    list_display = ('user', 'title', 'post', 'posted_on')

admin.site.register(SpaceGroups)
admin.site.register(Spaces)
admin.site.register(SpaceMembers, SpaceMembersAdmin)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(likes)
admin.site.register(Report)
admin.site.register(Search)
admin.site.register(SpaceJourney)
admin.site.register(MemberInvitation)
admin.site.register(SavedPost)
admin.site.register(Attachments)
admin.site.register(Event)
admin.site.register(UserPinnedPost)
admin.site.register(ContentToReview, ContentReview)
