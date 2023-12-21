from django.contrib import admin
from .models import BadgeDetails, AutoApproveGoal, UserEngagement, PointsTable, MentorshipGoalComment, UserBadgeDetails, UserGoalLog, UserDrivenGoal, UserPoints, SystemDrivenGoal, UserAssignedGoal, StreakPoints, UserStreakCount, UserStreak, UserStreakHistory

# Register your models here.

admin.site.register(BadgeDetails)
admin.site.register(PointsTable)
admin.site.register(UserBadgeDetails)
admin.site.register(UserPoints)
admin.site.register(SystemDrivenGoal)
admin.site.register(UserAssignedGoal)
admin.site.register(StreakPoints)
admin.site.register(UserStreakCount)
admin.site.register(UserStreak)
admin.site.register(UserStreakHistory)
admin.site.register(UserEngagement)
admin.site.register(UserDrivenGoal)
admin.site.register(UserGoalLog)
admin.site.register(MentorshipGoalComment)
admin.site.register(AutoApproveGoal)
