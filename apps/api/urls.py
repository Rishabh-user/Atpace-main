from django.urls import path
from rest_framework import routers
from django.urls.conf import include
from apps.api.views.leaderboard import Dashboard, IndividualGoalProgressChart, UserActivityChart, UserGoalDetail, MentorshipGoalsChart, GetMentorMentees, UserGoalsChart, GetDeleteUserGoal, GoalCategoryList, LogGoalProgress, GoalComment, UpdateUserGoal, UserGoalLogProgress, UserGoals, UserLeaderBoard, UserPoint, Userbadge, GoalCompleteRequest, MentorshipGoals, MentorshipGoalDetail, DeleteMentorshipGoal, UserAllCertificates, MailCertificate

from apps.api.views.feedback import CreateFeedbackTemplate, FeedbackResponseList, FeedbackFormAPI, SubmitFeedbackForm
from .views.views import (
    ChangePassword,
    AssignSurveyList,
    CommunityLoginWithEmailOrOtp,
    ContacProgramTeamAPI,
    DeletePost,
    EditUserProfileAssest,
    EndEngagementTime,
    GetUserCompany,
    IndustryExpertiseList,
    JourneyAllPost,
    JourneyPostCreate,
    LoginWithEmailOrOtp,
    PostComment,
    ResendEmail,
    ShowUnreadMsgCount,
    SignUp,
    AllChannels,
    ConfirmPassword,
    Logout,
    SocialLogin,
    StartEngagementTime,
    UserProfileAssestAnswerView,
    UserProfileAssestApiView,
    UserValidation,
    resetPassword,
    BrowseChannel,
    SentOtpRequest,
    VerifyOtpRequest,
    UserProfileViewSet,
    HomePageApiView,
    ProfileAssestQuestionViewSet,
    AddReferalCode,
    JourneyDetails,
    JourneyAssessment,
    CategoryJourney,
    SubmitAssessment,
    JourneyDetailsAPIView,
    UnlockJourney,
    AssessmentAnswer,
    QuestContentRevise,
    QuestSummary,
    QuestContentLearn,
    UserJoinedChannel,
    JourneySearchAPI,
    ContentQuizAsnwer,
    AvatarUpdate,
    DataTranslate,
    MarkasComplete,
    ProgramTeamAnnouncementList,
    PublicAnnouncementList,
    MobileLogs,
    GetCompanyJourney,
    GetTimeZone,
    UpdateEmail,
    VerifyEmailOtp,
    Check_lite_signup_user_data,
    AssesmentQuestions,
    UserEnrollCheck, SignupLitePost
)
from .views.views import *

from .views.community_journal import UpdateLearningJournal, AllJournal, WeekelyJournals, CommunityList, JourneyJournal
from .views.notifications import *
from .views.Mentor_User import ChatMessages, CreateEvent, SubmitProfileAssessment, JournalDetail, CreateChatGroup, DeleteEvent, EditProfileAssessmentQues, UpdateJournal, CreateJournal, LearningJournalPostComment, UpdateJournalComment, MentorAllotedJourneys, Journal, MentorDashboard, MentorsScheduedSession, MentorMentees, MentorCalendar, MenteeJourneyDetails, MentorLearningJournal, MentorWeeklyLearningJournal, MentorChatModule, UpdateEvent, WeeklyJournalPostAPI
from .views.survey import SubmitSurvey, JourneySurvey, SurveyAnswer, survey_upload_file
from .views.webhook import *
from .views.mentor import AvailableSlots, CancelAppointment, NewAppoinment, HistoryAppoinment, BookAppoinment, MentorProfile, MentorCalendarAPIVIew, UserMentor, add_favourite, add_favouritelist, WebAvaiableSlots, BookAppoinments
from .views.activity import AllActivity, ActivityUser

router = routers.DefaultRouter()
router.register(r'user-profile', UserProfileViewSet, basename="user-profile")
router.register(r'profile-assest', ProfileAssestQuestionViewSet, basename="profile-assest")
router.register(r'user-assest', UserProfileAssestApiView, basename="user-assest")

app_name = 'webapi'
urlpatterns = [
    path('', include(router.urls), name="api"),
    path('home-page/<uuid:pk>/', HomePageApiView.as_view(), name="home_page"),
    path('login/', LoginWithEmailOrOtp.as_view(), name='login'),
    path('community-login/', CommunityLoginWithEmailOrOtp.as_view(), name="community_login"),
    path('social-login/', SocialLogin.as_view(), name="social_login"),

    path('add-referal-code/', AddReferalCode.as_view(), name="add_referal_coda"),
    path('signup/', SignUp.as_view(), name='register'),
    path('logout/', Logout.as_view(), name='logout'),
    path('get-user-company/', GetUserCompany.as_view(), name='get_user_company'),
    path('reset-password/', resetPassword.as_view(), name='resetpassword'),
    path('set-password/', ConfirmPassword.as_view(), name='confirm-password'),
    path('change-password/', ChangePassword.as_view(), name='change_password'),
    path('profile-data/<uuid:user_id>/', IndustryExpertiseList.as_view(), name="profile_data"),
    path('user-channels/<uuid:user_id>/', BrowseChannel.as_view(), name='user-channels'),
    path('channels/<uuid:user_id>/', AllChannels.as_view(), name="all_channels"),
    path('request-otp/', SentOtpRequest.as_view(), name="request-otp"),
    path('verify-otp/', VerifyOtpRequest.as_view(), name="verify-otp"),
    path('verify-email/<uuid:user_id>/', ResendEmail.as_view(), name="verify_email"),
    path('category-journey/', CategoryJourney.as_view(), name="category-journey"),
    path('journey-details/<uuid:user_id>/<uuid:journey>/', JourneyDetails.as_view(), name="journey-details"),
    path('user-journey-data/<uuid:user_id>/<uuid:journey>/', JourneyDetailsAPIView.as_view(), name="user-journey-data"),
    path('assessment/', JourneyAssessment.as_view(), name="journey_assessment"),
    path('submit-assessment/', SubmitAssessment.as_view(), name="submit-assessment"),
    path('survey/', JourneySurvey.as_view(), name="journey_assessment"),
    path('submit-survey/', SubmitSurvey.as_view(), name="submit-survey"),
    # path("survey-answer/", SurveyAnswer.as_view(), name="assessment-answer"),
    path('unlock-journey/', UnlockJourney.as_view(), name="unlock-journey"),
    path("assessment-answer/", AssessmentAnswer.as_view(), name="assessment-answer"),
    path('survey-answer/<uuid:user_id>/<uuid:attempt_id>/', SurveyAnswer.as_view(), name="survey-answer"),
    path('quest-content-learn/', QuestContentLearn.as_view(), name="quest-content-learn"),
    path('quest-summary/', QuestSummary.as_view(), name="quest-summary"),
    path('quest-content-revise/', QuestContentRevise.as_view(), name="quest-content-revise"),
    path('user-joined-channel/<uuid:user_id>/', UserJoinedChannel.as_view(), name="user-joined-channel"),
    path('mentor-profile/', MentorProfile.as_view(), name="mentor-profile"),
    path("update-learning-journal/", UpdateLearningJournal.as_view(), ),
    path('learnings-journal/', AllJournal.as_view(), name="all_journal"),
    path('journey-search/', JourneySearchAPI.as_view(), name="journey-search"),
    path('notification/count/<uuid:user_id>/', live_all_notification_count.as_view()),
    path('notification/list/<uuid:user_id>/', live_all_notification_list.as_view()),
    path('new-appoinment/<uuid:user_id>/', NewAppoinment.as_view(), name="new-appoinment"),
    path('appoinment-history/<uuid:user_id>/', HistoryAppoinment.as_view(), name="appoinment_old"),
    path('book-appoinment/', BookAppoinment.as_view(), name="book-appoinment"),
    path('mentor-calendar/', MentorCalendarAPIVIew.as_view(), name="mentor-calendar"),
    path('mentor-avaliable-slots/', AvailableSlots.as_view(), name="avaliable+slots"),
    path('web-avaiable-slots/', WebAvaiableSlots.as_view(), name="web_avaiable_slots"),
    path('assign-survey-list/', AssignSurveyList.as_view(), name="assign_survey_list"),
    path('mark-complete/', MarkasComplete.as_view(), name="mark_as_complete"),
    path('user-assesst-answer/<uuid:user_id>/', UserProfileAssestAnswerView.as_view(), name="user_assesst_answer"),
    path('edit-profile-assesst', EditUserProfileAssest.as_view(), name="edit_profile_assesst"),
    path('quize-answer/', ContentQuizAsnwer.as_view(), name="quize-answer"),
    path('user-mentor/<uuid:user_id>/', UserMentor.as_view(), name="user-mentor"),
    path("add-favourite/", add_favourite.as_view(), name="add_favourite"),
    path("add-favourite-list/", add_favouritelist.as_view(), name="add_favouritelist"),
    path("book-appoinments/", BookAppoinments.as_view(), name="book-appoinments"),
    path('cancel-appoinments/', CancelAppointment.as_view(), name="cancel-appoinments"),
    path('avatar-update/', AvatarUpdate.as_view(), name="avatar-update"),
    path('create-post/', JourneyPostCreate.as_view(), name='create-post'),
    path('journey-post/<uuid:user_id>/<uuid:journey_id>/', JourneyAllPost.as_view(), name="journey-post"),
    path('post-comment/', PostComment.as_view(), name="post-comment"),
    path('delete-post/<uuid:user_id>/<uuid:journey_id>/<int:post_id>/', DeletePost.as_view(), name="delete-post"),
    path('weekely-journals/', WeekelyJournals.as_view(), name="weekely_journals"),
    path('user-badge/<uuid:user_id>/', Userbadge.as_view(), name="user_badge"),
    path('user-point/<uuid:user_id>/', UserPoint.as_view(), name="user_point"),
    path('community-list/<uuid:user_id>/', CommunityList.as_view(), name="community_list"),
    path('contact-program-team/', ContacProgramTeamAPI.as_view(), name="contact_program_team"),
    path('survey-file-upload/', survey_upload_file, name="survey_file_upload"),

    # mentoruser-apis
    path('mentor-mentees/<uuid:mentor_id>/', MentorMentees.as_view(), name="user_mentees"),
    path('mentor-journeys/<uuid:mentor_id>/', MentorAllotedJourneys.as_view(), name="mentor_alloted_journeys"),
    path('mentor-sessions/', MentorsScheduedSession.as_view(), name="mentor_sessions"),
    path('mentor-``dashboard``/<uuid:mentor_id>/', MentorDashboard.as_view(), name="mentor_dashboard"),
    path('mentor-calendar/<uuid:mentor_id>/', MentorCalendar.as_view(), name="mentor_calendar"),
    path('mentee-journey-details/<uuid:mentor_id>/<uuid:mentee_id>/<uuid:journey_id>',
         MenteeJourneyDetails.as_view(), name="mentee_journey_details"),
    path('learning-journal/<uuid:user_id>/<str:type>', MentorLearningJournal.as_view(), name="mentor_learning_journal"),
    path('weekly-learning-journal/<uuid:user_id>/<str:type>',
         MentorWeeklyLearningJournal.as_view(), name="mentor_weekly_learning_journal"),
    path('weekly-journal-details/<uuid:mentor_id>/<int:journal_id>/',
         WeeklyJournalPostAPI.as_view(), name="weekly_journal_details_post"),
    path('chat/<uuid:mentor_id>/', MentorChatModule.as_view(), name="chat"),
    path('chat-messages/', ChatMessages.as_view(), name="chat_messages"),
    path('create-chat-group/', CreateChatGroup.as_view(), name="create_chat_group"),
    path('create-event', CreateEvent.as_view(), name="create_event"),
    path('update-event', UpdateEvent.as_view(), name="update_event"),
    path('learning-journal-comment', LearningJournalPostComment.as_view(), name="learning_journal_comment"),
    path('edit-profile-assessment/<uuid:user_id>/', EditProfileAssessmentQues.as_view(), name="edit_profile_assessment"),
    path('delete-slot/', DeleteEvent.as_view(), name="delete_slot"),
    path("webhook/inbond/", vonage_inbond.as_view(), name="vonage_inbond"),
    path("webhook/status/", vonage_status.as_view(), name="vonage_status"),
#     path("webhook/dyte-webhooks/", dyte_redirect_webhook_function, name="dyte_webhooks"),
    path("webhook/dyte-webhook/", DyteWebhook.as_view(), name="dyte_webhook"),
    path("atpace/app/", app_redirect_url, name="app_redirection"),
    path('dashboard/', Dashboard.as_view(), name="dashboard"),
    path('user-goals/<uuid:user_id>/', UserGoals.as_view(), name="user_goals"),
    path('get-delete-goal/<uuid:user_id>/<uuid:goal_id>/', GetDeleteUserGoal.as_view(), name="get_delete_goal"),
    path('update-user-goal/<uuid:user_id>/<uuid:goal_id>/', UpdateUserGoal.as_view(), name="update_user_goal"),
    path('user-goal-progress/<uuid:user_id>/', UserGoalLogProgress.as_view(), name="user_goal_progress"),
    path('mentorship-goals/', MentorshipGoals.as_view(), name="mentorship_goals"),
    path('user-activity-chart/<uuid:user_id>/', UserActivityChart.as_view(), name="user_activity_chart"),
    path('mentorship-goal-detail/', MentorshipGoalDetail.as_view(), name="mentorship_goal_detail"),
    path('delete-mentorship-goal/', DeleteMentorshipGoal.as_view(), name="delete_mentorship_goal"),
    path('goal-complete-request/', GoalCompleteRequest.as_view(), name="goal_complete_request"),
    path('goal-comment/', GoalComment.as_view(), name="goal_comment"),
    path('log-goal-progress/', LogGoalProgress.as_view(), name="log_goal_progress"),
    path('goal-category-list/', GoalCategoryList.as_view(), name="goal_category_list"),
    path('message-count/<uuid:user_id>', ShowUnreadMsgCount.as_view(), name="message_count"),
    path('user-goal-detail/<uuid:goal_id>/', UserGoalDetail.as_view(), name="user_goal_detail"),
    path('user-goals-chart/<uuid:user_id>', UserGoalsChart.as_view(), name="user_goals_chart"),
    path('get-mentor-mentees', GetMentorMentees.as_view(), name="get_mentor_mentees"),
    path('mentorship-goals-chart/<uuid:user_id>/', MentorshipGoalsChart.as_view(), name="mentorship_goals_chart"),
    path('journal/<uuid:user_id>/<str:type>', Journal.as_view(), name="journal"),
    path('journey-journal/<uuid:journey_id>/', JourneyJournal.as_view(), name="journey_journal"),
    path('create-journal/', CreateJournal.as_view(), name='create_journal'),
    path("update-journal/", UpdateJournal.as_view(), name='update_journal'),
    path("update-journal-comment/", UpdateJournalComment.as_view(), name='update_journal_comment'),
    path("submit-profile-assessment/", SubmitProfileAssessment.as_view(), name='submit_profile_assessment'),
    path('journal-detail/<int:id>', JournalDetail.as_view(), name="journal_detail"),
    path('start-engagement-time/<uuid:user_id>', StartEngagementTime.as_view(), name="start_engagement_time"),
    path('end-engagement-time/<uuid:user_id>', EndEngagementTime.as_view(), name="end_engagement_time"),
    path('individual-goal-progress/<uuid:user_id>/<uuid:goal_id>/', IndividualGoalProgressChart.as_view(), name="individual_goal_progress"),
    path('user-leaderboard/<uuid:user_id>', UserLeaderBoard.as_view(), name="user_leaderboard"),
    path('announce-list/<uuid:user_id>/', ProgramTeamAnnouncementList.as_view(), name="announce_list"),
    path('translate/<uuid:user_id>/', DataTranslate.as_view(), name="translate"),
    path('public-announcement-list/<uuid:user_id>/', PublicAnnouncementList.as_view(), name="public-announcement-list"),
    path('mobile-logs/', MobileLogs.as_view(), name="mobile_logs"),
    path('get-company-journey/', GetCompanyJourney.as_view(), name="get_company_journey"),
    path('validate-user', UserValidation.as_view(), name="validate_user"),
    path('timezone', GetTimeZone.as_view(), name="get_timezone"),
    path('feedback-data/<uuid:user_id>/', CreateFeedbackTemplate.as_view(), name="feedback-data"),
    path('user-response-list/<uuid:user_id>/', FeedbackResponseList.as_view(), name="user_response_list"),
    path('feedback-form/', FeedbackFormAPI.as_view(), name="feedback_form_api"),
    path('submit-feedback-form/', SubmitFeedbackForm.as_view(), name="submit_feedback_form"),
    path('all-activity/<uuid:user_id>/', AllActivity.as_view(), name="all_activity"),
    path('activity-user/<uuid:user_id>/<int:activity_id>/', ActivityUser.as_view(), name="activity_user"),
    path('user-certificates/<uuid:user_id>/', UserAllCertificates.as_view(), name="user_certificates"),
    path('mail-certificate/<uuid:user_id>/<uuid:certificate_id>', MailCertificate.as_view(), name="mail_certificate"),
    path('update-email/', UpdateEmail.as_view(), name="update_email"),
    path('verify-email-otp/', VerifyEmailOtp.as_view(), name="verify_email_otp"),
#     rasa lite apis
     path('check-user-data', Check_lite_signup_user_data.as_view(), name="check-user-data" ),
     path('assesment-questions', AssesmentQuestions.as_view(), name="assesment-questions" ),
     path('user-enroll-check', UserEnrollCheck.as_view(), name="check-user-enroll" ),
     path('signup-lite-post', SignupLitePost.as_view(), name="signup-lite-post" ),
     path('get-journey-title', GetJourneyTitle.as_view(), name="get-journey-title"),
     # rasa program manager command apis
     path('run-cron-jobs', RuntheCronjobs.as_view(), name='run-cron-jobs'),
     path('mentee-activity', MenteeActivityData.as_view(), name='mentee-activity'),
     path('mentor-activity', MentorActivityData.as_view(), name='mentee-activity'),
     path('pair-activity', PairActivityData.as_view(), name='pair-activity'),
     path('attendance-report', GenerateAttendance.as_view(), name='attendance-report'),
     path('get-manager-companies', ManagerCompanies.as_view(), name='manager-companies'),
     path('get-journey-list', GetJourneyList.as_view(), name='get-journey-list'),
     # apple signin
     path('apple-auth', generate_apple_redirect_url, name='apple-auth'),
     # path('apple-login-callback', AppleLogin.as_view(), name='apple_login_callback'),
     path('meet-rsvp-response', MeetRSVPResponse.as_view(), name='meet_rsvp_response'),
     path('get-dyte-token/<uuid:user_id>', GetDyteAuthToken.as_view(),)
]
