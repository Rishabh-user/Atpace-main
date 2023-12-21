from django.contrib import admin
from apps.program_manager_panel.models import(
    MentorMenteeRatio,
    MentorMenteeTrack,
    SubcribedUser,
    Subscription,
    SubscriptionOffer,
    MessageScheduler,
    ProgramManagerTask,
    TaskRemainder,
    AssignTaskToUser
)

# Register your models here.

admin.site.register(Subscription)
admin.site.register(SubscriptionOffer)
admin.site.register(SubcribedUser)
admin.site.register(MentorMenteeRatio)
admin.site.register(MentorMenteeTrack)
admin.site.register(MessageScheduler)
admin.site.register(ProgramManagerTask)
admin.site.register(TaskRemainder)
admin.site.register(AssignTaskToUser)