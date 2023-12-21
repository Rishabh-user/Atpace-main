from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm
from .models import (
    AdminUser,
    Collabarate,
    Coupon,
    CouponApply,
    Learner,
    Company,
    ProgramManager,
    Mentor,
    Profile,
    User,
    UserCompany,
    UserProfileAssest,
    UserTypes,
    UserRoles,
    ProficiencyLevel,
    ProfileAssestQuestion,
    UserEarnedPoints,
    FirebaseDetails,
    ContactProgramTeam,
    ContactProgramTeamImages,
    TelegramUserData,
    UserEmailChangeRecord,
    UserPhoneChangeRecord,
    CSVFile,
    SaveRasaManagerFiles
    # UserDeviceDetails
)
# Register your models here.


class CustomAdmin(UserAdmin):
    model = User
    add_form = CustomUserCreationForm

    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'User Infos',
            {
                'fields': (
                    'company',
                    'userType'
                )
            }
        )
    )

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp')


class ProfileAssestQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "display_order", "question_for")
    list_filter = ('question_for',)
    list_editable = ['display_order']


class UserProfileAssestAdmin(admin.ModelAdmin):
    list_display = ("user", "assest_question", "question_for")
    list_filter = ('question_for',)

class CollaborateAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "type")


admin.site.register(Mentor)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(UserProfileAssest, UserProfileAssestAdmin)
admin.site.register(ProfileAssestQuestion, ProfileAssestQuestionAdmin)
admin.site.register(Learner)
admin.site.register(Company)
admin.site.register(UserTypes)
admin.site.register(AdminUser)
admin.site.register(ProgramManager)
admin.site.register(User, CustomAdmin)
admin.site.register(ProficiencyLevel)
admin.site.register(UserRoles)
admin.site.register(UserCompany)
# admin.site.register(UserDeviceDetails)
admin.site.register(UserEarnedPoints)
admin.site.register(Coupon)
admin.site.register(CouponApply)
admin.site.register(FirebaseDetails)
admin.site.register(Collabarate, CollaborateAdmin )
admin.site.register(ContactProgramTeam)
admin.site.register(ContactProgramTeamImages)
admin.site.register(TelegramUserData)
admin.site.register(UserPhoneChangeRecord)
admin.site.register(UserEmailChangeRecord)
admin.site.register(CSVFile)
admin.site.register(SaveRasaManagerFiles)
