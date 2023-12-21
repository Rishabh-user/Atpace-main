from django.contrib.auth.views import (
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordChangeView,
    PasswordChangeDoneView,

)
from django.urls import path
from django.urls import reverse_lazy
# from push_notification.views import f_notification
from apps.webapp.views import *
from . import views
from .views import (
    ActiveUserList,
    AddMentorToPool,
    AllAssessmentReport,
    BookMentorSlot,
    BookMentorSlots,
    BulkIncativeArchieveUser,
    BulkUserJourneyRemoved,
    ContactProgramTeamMember,
    ContactProgramTeamS,
    CreateCouponCode,
    CreateGroupCollabarate,
    DeleteAssessmentQuestion,
    DeleteCouponCode,
    DetailMatchQuestion,
    EditAssessment,
    EditCouponCode,
    EditMatchQuestion,
    EditProfileAssessment,
    question_reorder,
    Email_Verify,
    update_email,
    update_phone,
    verify_phone_otp,
    verify_email_otp,
    update_phone,
    verify_phone_otp,
    CreateCollabarate,
    InactiveUserList,
    ListCollabarate,
    ListGroupCollabarate,
    MatchQuestionList,
    MatchingMentorAlgo,
    MatchingMentorPreview,
    company_journey,
    journey_pool,
    MeetingDetails,
    ProgramAnnouncementList,
    ProgramUserList,
    ResendOtp,
    SocialLoginType,
    StartMeeting,
    UserMentorList,
    UserMentorProfile,
    UserSetPassword,
    # CouponCode,
    CustomLoginView,
    AdminList,
    CompanyList,
    DeleteCompany,
    UpdateCompany,
    CreateAdmin,
    CreateCompany,
    CreateUser,
    DashBorad,
    UsersDashboardForAdmin,
    DeleteUser,
    UserProfile,
    UpdateUser,
    MentorList,
    ContentCreaterList,
    CreateUsersFromCSV,
    LogoutView,
    CompanyUser,
    AlloteChannelToUser,
    CreateRole,
    UpdateRole,
    DeleteRole,
    WeeklyJournalPost,
    Check_lite_signup_user_data,
    cancelMentorSlot,
    deleteMentorSlot,
    removeUserSlot,
    check_coupon_code,
    check_lite_signup_user,
    check_phone,
    check_username,
    get_user_company,
    save_user_company,
    delete_Collabarate,
    google_login,
    google_register,
    lite_signup_edit,
    login_otp,
    login_attempt,
    check_match_ques_config,
    register,
    check_user_name,
    EditProfile,
    AdvanceProfile,
    AdvanceProfilePreview,
    CompleteProfileAssessment,
    Calendar,
    ChatModule,
    MatchingMentor,
    assign_mentor,
    mentor_users,
    alloted_journeys,
    JourneyReport,
    ManualAssign,
    ALLCouponCodes,
    # UserDeviceDetail,
    CreateAssessment,
    ALLAssessment,
    ProgramUserReport,
    mentorMatchingRepost,
    UserProfileCheck,
    mentor_users_details,
    # social_login_type,
    user_chat_status,
    user_jourey_removed,
    weeklyjournalComment,
    resend_Verify_Email,
    UserCalendar,
    GenerateAttendenceReport,
    ProgramJourneys,
    UserChatModule,
    journey_mentor,
    assign_survey_list,
    UserJourneyList,
    ShowUserRewards,
    UserDashBoard,
    ProgramAnnouncement,
    SignupLite,
    UserEnrollCheck,
    AssesmentQuestions,
    signup_lite_post,
    user_enroll_check,
    assessment_question,
    signup_thankyou,
    merge_user_record,
    create_group,
    MatchingQuestion,
    question_options1,
    question_options2,
    question_options3,
    EditCollabarate,
    EditGroupCollabarate, MentorDashboardForAdmin, 
    RedirectShortUrl,
    UserCertificates,
    apple_login, apple_login_callback
)

app_name = 'user'
web_URLPattern = [
    path('', Index.as_view(), name="index"),
    path('about-us', AboutUs.as_view(), name="about_us"),
    path('contact-us', ContactUs.as_view(), name="contact_us"),
    path('resources', Resources.as_view(), name="resources"),
    path('program', Program.as_view(), name="program"),
    path('pricing', Pricing.as_view(), name="pricing"),
    path('transition-to-success', TransitionToSuccess.as_view(), name="transition_to_success"),
    path('community', PublicCommunity.as_view(), name="community"),
    path('community-signup/', CommunitySignup.as_view(), name="community_signup"),
    path('course-detail/<uuid:course_id>', CourseDetailsView.as_view(), name="course_detail"),
    path('thank-you/', ThankYou.as_view(),  name="thank-you")

]

admin_urlpatterns = [
    # home login
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register', register, name="register"),
    path('signup-lite/<uuid:journey_id>/', SignupLite.as_view(), name="signup-lite"),
    path('signup_lite_post', signup_lite_post, name="signup_lite_post"),
    path('check-user', check_lite_signup_user, name="check_user"),
    path('check-user-data', Check_lite_signup_user_data.as_view(), name="check_user_data"),
    path('check-coupon', check_coupon_code, name="check_coupon"),
    path('check-phone/', check_phone, name="check_phone"),
    path('check-username/', check_username, name="check_username"),
    path('edit-signup-lite/<uuid:journey_id>', lite_signup_edit, name="edit_signup_lite"),
    path('user-enroll-check', user_enroll_check, name="user_enroll_check"),
    path('user-enroll-check-data', UserEnrollCheck.as_view(), name="user_enroll_check_data"),
    path('assesment-questions', AssesmentQuestions.as_view(), name="assesment_questions"),
    path('check-user-name/', check_user_name, name="check_user_name"),
    path('signup-thankyou/', signup_thankyou, name="signup-thankyou"),
    path('merge-user-record/', merge_user_record, name="merge_user_record"),
    path('assessment_question/<uuid:journey>', assessment_question, name="assessment_question"),
    path('verify-email/<uidb64>/<token>/', Email_Verify, name="verify_email"),
    path('verify-email/', resend_Verify_Email, name="resend_verify_email"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('otp/', login_otp, name="otp_login"),
    path('re-otp/', ResendOtp, name="resend_otp_login"),
    path('login-phone/', login_attempt, name="login_otp"),
    path('get-user-company/', get_user_company, name="get_user_company"),
    path('save-user-company/', save_user_company, name="save_user_company"),
    # passwords
    path('password_change/', PasswordChangeView.as_view(
        template_name='auth/password_change_form.html', success_url=reverse_lazy('user:password_change_done')),
        name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(template_name='auth/password_reset_complete.html'),
         name='password_change_done'),
    path("password_reset", views.password_reset_request,
         name="password_reset"
         ),
    path("password_reset/done/", PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'),
        name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name="auth/password_reset_confirm.html",
        success_url=reverse_lazy('user:password_reset_complete')),
        name='password_reset_confirm'
    ),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'),
        name='password_reset_complete'
    ),

    # Users-urls
    path('dashboard/', DashBorad.as_view(), name="user-dashboard"),
    path('user-dashboard/', UserDashBoard.as_view(), name="userdashboard"),
    path('user-dashboard-admin/<uuid:pk>/', UsersDashboardForAdmin, name="user-dashboard-admin"),
    path('mentor-dashboard-admin/<uuid:pk>/', MentorDashboardForAdmin, name="mentor-dashboard-admin"),
    path('user/create/', CreateUser.as_view(), name="create-user"),
    path('user/bulk-create/', CreateUsersFromCSV.as_view(), name="create-bulk-user"),
    path('user/list/', ActiveUserList.as_view(), name="user-list"),
    path('user/inactive-list/', InactiveUserList.as_view(), name="inactive_user_list"),
    path('bulk-inactive-archive/', BulkIncativeArchieveUser.as_view(), name="bulk_inactive_archive"),
    path('bulk-journey-remove/', BulkUserJourneyRemoved.as_view(), name="bulk_journey_remove"),
    path('user/profile/<uuid:pk>/', UserProfile.as_view(), name="user-profile"),
    path('update-email/', update_email, name="update_email"),
    path('update-phone/', update_phone, name="update_phone"),
    path('verify-phone-otp/', verify_phone_otp, name="verify_phone_otp"),
    path('verify-email-otp/', verify_email_otp, name="verify_email_otp"),
    path('update-phone/', update_phone, name="update_phone"),
    path('verify-phone-otp/', verify_phone_otp, name="verify_phone_otp"),
    path('user/delete/<uuid:pk>/', DeleteUser.as_view(), name="delete-user"),
    path('user/update/<uuid:pk>/', UpdateUser.as_view(), name="update-user"),
    path('user/edit/<uuid:pk>/', EditProfile.as_view(), name="edit_profile"),
    path('user/advance-profile/<uuid:pk>/', AdvanceProfile.as_view(), name="advance_profile"),
    path('user/advance-profile-preview/<uuid:pk>/', AdvanceProfilePreview.as_view(), name="advance_profile_preview"),
    path('user/set-password/<uuid:pk>/', UserSetPassword, name='set-password'),
    path('user/profile-assessment/<uuid:pk>/', CompleteProfileAssessment.as_view(), name="profile_assessment"),
    path('user/edit-assessment/<uuid:pk>', EditProfileAssessment.as_view(), name="edit_assessment"),
    path('calendar/', Calendar.as_view(), name="calendar"),
    path('user-calendar/', UserCalendar.as_view(), name="user_calendar"),
    path('user-calendar/<str:pk>/', UserCalendar.as_view(), name="user_calendar_with_id"),
    path('archive_user', views.archive_user, name="archive_user"),
    path('assign-survey-list/', views.assign_survey_list, name="assign_survey_list"),
    path('assign-survey-list/<str:pk>/', views.assign_survey_list, name="assign_survey_list_with_id"),
    path("user-journeys-list/", UserJourneyList.as_view(), name="user-journeys-list"),
    path("remove-journey/<int:user_channel_id>/", user_jourey_removed, name="remove_journey"),
    path('user/rewards/<uuid:pk>/', ShowUserRewards.as_view(), name="user-rewards"),
    path('certificates/', UserCertificates.as_view(), name="user_certificates"),
    # path('calendar_data/', views.calendar_data, name="calendar_data"),
    # path('notify/', f_notification, name="notify"),

    # Company
    path('company/create/', CreateCompany.as_view(), name="create_company"),
    path('company/list/', CompanyList.as_view(), name="company_list"),
    path('company/delete/<uuid:pk>/', DeleteCompany.as_view(), name="delete-company"),
    path('company/update/<uuid:pk>/', UpdateCompany.as_view(), name="update-company"),
    path('company/user/<uuid:company>', CompanyUser.as_view(), name="company_user"),

    # User-admin
    path('user-admin/create/', CreateAdmin.as_view(), name="create_admin"),
    path('user-admin/list/', AdminList.as_view(), name="admin_list"),
    path('mentor/list/', MentorList.as_view(), name="mentor_list"),
    path('content-creater/list/', ContentCreaterList.as_view(), name="content_creator_list"),
    path('allote-channel', AlloteChannelToUser.as_view(), name="allote-channel"),
    path('create-role/', CreateRole.as_view(), name="create_role"),
    path('edit-role/<uuid:pk>/', UpdateRole.as_view(), name="update-role"),
    path('delete-role/<uuid:pk>/', DeleteRole.as_view(), name="delete-role"),
    path('chat/', ChatModule.as_view(), name="chat"),
    path('chat/<str:room_name>/', UserChatModule.as_view(), name="user_chat"),
    path('chat/<str:pk>/', ChatModule.as_view(), name="chat_with_id"),
    path('user-chat-status', user_chat_status, name="user_chat_status"),
    path('create-group/', create_group, name="create_group"),
    path('program-user-list', ProgramUserList.as_view(), name="program_user_list"),
    path('mentor-matching-report', mentorMatchingRepost.as_view(), name="mentor_matching_repost"),
    path('program-user-report', ProgramUserReport.as_view(), name="program_user_repost"),
    path('user-profile-check', UserProfileCheck.as_view(), name="user_profile_check"),
    path('add-mentor/', AddMentorToPool.as_view(), name="add_mentor"),
    path('matching-mentor/', MatchingMentor.as_view(), name="matching_mentor"),
    path('company-journey/', company_journey, name="company_journey"),
    path('journey-pool/', journey_pool, name="journey_pool"),
    path("journey_mentor/", journey_mentor, name="journey_mentor"),
    path('assign_mentor/', assign_mentor.as_view(), name="assign_mentor"),
    path('mentor_users/', mentor_users.as_view(), name="mentor_users"),
    path('mentee-details/<uuid:user_id>/<uuid:journey_id>/',
         mentor_users_details.as_view(), name="mentor_users_details"),
    path('mentor-list/', UserMentorList.as_view(), name="user_mentor_list"),
    path('mentor-list/<str:pk>/', UserMentorList.as_view(), name="user_mentor_list_with_id"),
    path('user-mentor-profile/<uuid:mentor_id>/', UserMentorProfile.as_view(), name="user_mentor_profile"),
    path('Book-mentor-slots/', BookMentorSlots.as_view(), name="book_mentor_slots"),
    path('Book-mentor-slots/<str:pk>/', BookMentorSlots.as_view(), name="book_mentor_slots_with_id"),
    path('Book-mentor-slot/', BookMentorSlot, name="book_mentor_slot"),
    path('cancel-mentor-slot', cancelMentorSlot, name="cancel_mentor_slot"),
    path('delete-mentor-slot', deleteMentorSlot, name="delete_mentor_slot"),
    path('remove-user-slot', removeUserSlot, name="remove_user_slot"),
    path('alloted_journeys/', alloted_journeys.as_view(), name="alloted_journeys"),
    path('journal-comment/', weeklyjournalComment, name="journal_comment"),
    path('learning-journal-post/<uuid:user_id>/<int:pk>/', WeeklyJournalPost.as_view(), name="learning_journal_post"),
    path('update_events/', views.update_events, name="update_events"),
    path('update_manager_task/', views.update_manager_task, name="update_manager_task"),
    path('add_events/', views.add_events, name="add_events"),
    path('manual-assign/', ManualAssign.as_view(), name="manual_assign"),
    path('journey-report/<uuid:journey>', JourneyReport.as_view(), name="journey_report"),
    path('contact-program-team', ContactProgramTeamS.as_view(), name="contact_program_team"),
    path('program-team-list/', ContactProgramTeamMember.as_view(), name="program_team_list"),
    path("program-announcement/", ProgramAnnouncement.as_view(), name="program_announcement"),
    path('program-announcement-list/', ProgramAnnouncementList.as_view(), name="program_announcement_list"),
    # path('user-device-details/', UserDeviceDetail, name='user-device-details'),

    # Meeting-data
    path('create-meet/', CreateCollabarate.as_view(), name="create_meet"),
    path('meetings/', ListCollabarate.as_view(), name="list_meeting"),
    path('delete-meet/<uuid:pk>/', delete_Collabarate, name="delete_meet"),
    path('edit-meet/<uuid:pk>/', EditCollabarate.as_view(), name="edit_meet"),
    path('edit-group-meet/<uuid:pk>/', EditGroupCollabarate.as_view(), name="edit_group_meet"),
    path('create-group-meet/', CreateGroupCollabarate.as_view(), name="create_group_meet"),
    path('group-meetings/', ListGroupCollabarate.as_view(), name="list_group_meeting"),
    path('start/<uuid:pk>/', StartMeeting.as_view(), name="start"),
    path('meeting-details/<uuid:id>/', MeetingDetails, name="meeting_details"),

    # path('create-coupon/', CouponCode, name='create_coupon'),
    path('create-coupon/', CreateCouponCode.as_view(), name='create_coupon'),
    path('all-coupon-codes/', ALLCouponCodes.as_view(), name="list_coupon"),
    path('edit-coupon/<uuid:pk>/', EditCouponCode.as_view(), name="edit_coupon"),
    path('delete-coupon/<uuid:pk>/', DeleteCouponCode, name="delete_coupon"),
    path('assessment-question/', CreateAssessment.as_view(), name="create_assessment"),
    path('assessment-list/', ALLAssessment.as_view(), name="assessment_list"),
    path('edit-question/<int:pk>/', EditAssessment.as_view(), name="edit_question"),
    path('question-reorder/', question_reorder, name="question_reorder"),
    path('delete-assessment/<int:pk>/', DeleteAssessmentQuestion, name="delete_assessment"),
    path('attendance/', GenerateAttendenceReport.as_view(), name="attendance"),


    path('user-activity/', views.UserActivity, name="user_activity"),
    path('user-assessment/', AllAssessmentReport, name="assessment_report"),
    path("program-journeys/", ProgramJourneys.as_view(), name="program_journeys"),
    path('mentor-matching-auto/', MatchingMentorAlgo.as_view(), name="mentor_matching_auto"),
    path('check-match-ques-config/', check_match_ques_config, name="check_match_ques_config"),
    path('create-match-question/', MatchingQuestion.as_view(), name="create_match_question"),
    path('edit-match-question/<uuid:config_id>', EditMatchQuestion.as_view(), name="edit_match_question"),
    path('all-match-question/', MatchQuestionList.as_view(), name="all_match_question"),
    path('match-question-preview/<uuid:config_id>', DetailMatchQuestion.as_view(), name="match_question_preview"),
    path("question_options1/", question_options1, name="question_options1"),
    path("question_options2/", question_options2, name="question_options2"),
    path("question_options3/", question_options3, name="question_options3"),
    path('mentor-match-preview/', MatchingMentorPreview.as_view(), name="mentor_match_preview"),

    # oauth url patterns
    path('google-login', google_login, name="google_login"),
    path('google-register', google_register, name="google_register"),
    # oauth apple url patterns
    path('apple-login', apple_login, name="apple_login" ),
    path('apple-login-callback', apple_login_callback, name="apple_login_callback"),
    path('social-login-type/', SocialLoginType.as_view(), name="social_login_type"),
    path('re/<str:short_url>/', RedirectShortUrl.as_view(), name="redirect_short_url"),

]

urlpatterns = web_URLPattern + admin_urlpatterns
