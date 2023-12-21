from django.urls import path
from .views import Dashboard, Learn, Activity, Mentees, Community, Goals, Support, CreateMentoringTypes, CreateTargetAudience, UpdateMentoringTypes, UpdateTargetAudience, DeleteMentoringTypes,MentorCalendar, DeleteTargetAudience
from apps.mentor_panel.marketplace_apis import MentorAdvanceProfile, GetMentorWorkEperience, PostMentorWorkEperience, GetMentorCertificate, \
   GetMentorEducation,PostMentorCertificate, PostMentorEducation, UserSkillSet, ProfileConstantData, MarketplaceInviteEmail, PublishOnMarketPlace

app_name = 'mentor'
urlpatterns = [
    path('dashboard/', Dashboard.as_view(), name='mentor_dashboard'),
    path('learn/', Learn.as_view(), name='mentor_learn'),
    path('goals/', Goals.as_view(), name='mentor_goals'),
    path('activity/', Activity.as_view(), name='mentor_activity'),
    path('mentees/', Mentees.as_view(), name='mentor_mentees'),
    path('community/', Community.as_view(), name='mentor_community'),
    path('support/', Support.as_view(), name='mentor_support'),
    path('calendar/', MentorCalendar.as_view(), name='mentor_calendar'),
    path('mentor-advance-profile/<uuid:mentor_id>/', MentorAdvanceProfile.as_view(), name='mentor_advance_profile'),
    path('get-mentor-work-experience/<uuid:mentor_id>/<uuid:experience_id>/', GetMentorWorkEperience.as_view(), name='get_mentor_work_experience'),
    path('post-mentor-work-experience/<uuid:mentor_id>/', PostMentorWorkEperience.as_view(), name='post_mentor_work_experience'),
    path('get-mentor-certificate/<uuid:mentor_id>/<uuid:certificate_id>/', GetMentorCertificate.as_view(), name='get_mentor_certificate'),
    path('get-mentor-education/<uuid:mentor_id>/<uuid:education_id>/', GetMentorEducation.as_view(), name='get_mentor_education'),
    path('post-mentor-certificate/<uuid:mentor_id>/', PostMentorCertificate.as_view(), name='post_mentor_certificate'),
    path('post-mentor-education/<uuid:mentor_id>/', PostMentorEducation.as_view(), name='post_mentor_education'),
    path('user-skillset/<uuid:mentor_id>/', UserSkillSet.as_view(), name='user_skillset'),
    path('profile-constant-data/', ProfileConstantData.as_view(), name='profile_constant_data'),
    path('marketplace-invite-email/', MarketplaceInviteEmail.as_view(), name='marketplace_invite_email'),
    path('publish-to-marketplace/', PublishOnMarketPlace.as_view(), name='publish_to_marketplace'),
    
    #admin side urls
    path('create-list-mentoring-types/', CreateMentoringTypes.as_view(), name="create_list_mentoring_types"),
    path('update-mentoring-types/<uuid:pk>/', UpdateMentoringTypes.as_view(), name="update_mentoring_types"),
    path('delete-mentoring-type/', DeleteMentoringTypes, name="delete_mentoring_type"),
    path('create-list-target-audience/', CreateTargetAudience.as_view(), name="create_list_target_audience"),
    path('update-target-audience/<uuid:pk>/', UpdateTargetAudience.as_view(), name="update_target_audience"),
    path('delete-target_audience/', DeleteTargetAudience, name="delete_target_audience"),
]