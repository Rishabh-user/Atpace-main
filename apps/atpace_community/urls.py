from django.urls import path

from apps.atpace_community.api import (AllComments, AmaseData,
                                       AllSpaces, AtpaceNotificationAPI, AtpaceNotificationCount,
                                       Comments, UpdateUserType,
                                       GetGroupSpace,
                                       GroupSpaces,
                                       LikeOnPostComment,
                                       PublicPosts,
                                       PublicPostWithSpace,
                                       ReportPost, ReportTypes,
                                       SearchContent,
                                       SpaceUser, TrendingPost, UpdateComment,
                                       UpdateComments, UpdateEventPost,
                                       UpdateSpaces,
                                       UserPost,
                                       UserPosts,
                                       CreateEventPost,
                                       UserSavedPost,
                                       UserSpaces,
                                       SpaceGroupMember,
                                       EventSpaceMember,
                                       SpaceGroupDetails,
                                       UserChat,
                                       UserRoom,
                                       EventSpace,
                                       PinnedPost,
                                       ContentsToReview,
                                       ApproveRejectContent,
                                       EventHostList)
from .views import CreateSpace, EditSpace, EditSpaceGroup, EditSpaceMember, InvitationList, ListReport, ListSpace, CreateSpaceMember, SpaceMemberList, delete_group_space, GroupSpace, delete_space, delete_space_member, get_spacegroup_space, ContentReviewList, ContentReview
# , CreateEvent
app_name = 'atpace_community'

urlpatterns = [
    # Admin Panel Urls
    path('group-space/', GroupSpace.as_view(), name="group_space"),
    path('edit-group-space/<uuid:pk>/', EditSpaceGroup.as_view(), name="edit_group_space"),
    path('delete-group-space/', delete_group_space, name="delete_group_space"),
    path('create-space/', CreateSpace.as_view(), name="create_space"),
    path('list-space/', ListSpace.as_view(), name="space_list"),
    path('edit-space/<uuid:pk>/', EditSpace.as_view(), name="edit_space"),
    path('delete-space/', delete_space, name="delete_space"),
    path('space-member-list/', SpaceMemberList.as_view(), name="space_member_list"),
    path('create-space-member/', CreateSpaceMember.as_view(), name="create_space_member"),
    path('delete-space-member/', delete_space_member, name="delete_space_member"),
    path('edit-space-member/<uuid:pk>/', EditSpaceMember.as_view(), name="edit_space_member"),
    path('report-space/', ListReport.as_view(), name="report_list"),
    path('invite-list/', InvitationList.as_view(), name="invite_list"),
    path('get-spacegroup-space/', get_spacegroup_space, name="get_spacegroup_space"),
    path('content-review-list/', ContentReviewList.as_view(), name="content_review_list"),
    path('review-content/<uuid:review_content_id>', ContentReview.as_view(), name="review_content"),

    # Space API URLs
    path('all-groups/', GroupSpaces.as_view(), name="space_group"),
    path('groups/<uuid:space_group_id>/', GetGroupSpace.as_view(), name="space_group"),
    path('all-space/', AllSpaces.as_view(), name="member_spaces"),
    path('update-space/<uuid:space_id>/', UpdateSpaces.as_view(), name="update_spaces"),
    path('user-space/<uuid:user_id>/', UserSpaces.as_view(), name="user_spaces"),
    path('space-user/<uuid:user_id>/<uuid:space_id>/', SpaceUser.as_view(), name="space_user"),
    path("space-group-member/<uuid:space_group_id>", SpaceGroupMember.as_view(), name="space_group_member"),
    path("event-space-member/<uuid:space_id>", EventSpaceMember.as_view(), name="event_space_member"),
    path("space-group-details/<uuid:space_group_id>", SpaceGroupDetails.as_view(), name="space_group_member"),


    # Post API Urls UserPost
    path('user-posts/<uuid:user_id>/', UserPosts.as_view(), name="user_posts"),
    path('user-post/<uuid:post_id>/', UserPost.as_view(), name="user_post"),
    path('user-saved-post/<uuid:user_id>/', UserSavedPost.as_view(), name="user_saved_post"),
    path('trending-post/<uuid:space_id>/', TrendingPost.as_view(), name="trending_post"),
    path('public-posts/', PublicPosts.as_view(), name="public_posts"),
    path('public-posts-with-space/<uuid:user_id>/', PublicPostWithSpace.as_view(), name="public_posts_with_space"),
    path('user-all-comment/<uuid:user_id>/', AllComments.as_view(), name="user_all_comments"),
    path('user-comments/<uuid:user_id>/', Comments.as_view(), name="user_comments"),
    path('user-comment/<uuid:user_id>/<uuid:post_id>/', UpdateComments.as_view(), name="user_comment"),
    path('update-comment/<uuid:user_id>/<uuid:comment_id>/', UpdateComment.as_view(), name="user_update_comment"),
    path('likes-post-comment/<uuid:user_id>/', LikeOnPostComment.as_view(), name="likes_post_comment"),
    path('report-post/<uuid:user_id>/', ReportPost.as_view(), name="report_post"),
    path('report-type/<uuid:user_id>/', ReportTypes.as_view(), name="report_type"),
    path('search-content/', SearchContent.as_view(), name="search_content"),
    path('notificaton/<uuid:user_id>/', AtpaceNotificationAPI.as_view(), name="notification"),
    path('notificaton-count/<uuid:user_id>/', AtpaceNotificationCount.as_view(), name="notification_count"),
    path('pinned-post/<uuid:user_id>/', PinnedPost.as_view(), name="pinned_post"),
    path('review-content-api/<uuid:user_id>/', ContentsToReview.as_view(), name="review_content_api"),
    path('approve-reject-content-api/<uuid:user_id>/', ApproveRejectContent.as_view(), name="approve_reject_content_api"),
    
    # Chat URL
    path('user-chat', UserChat.as_view(), name="user_chat"),
    path('user-room', UserRoom.as_view(), name="user_room"),

    # Event URL
    path('create-event-post/<uuid:user_id>/', CreateEventPost.as_view(), name="create_event_post"),
    path('update-event-post/<uuid:user_id>/<uuid:post_id>/', UpdateEventPost.as_view(), name="update_event_post"),
    path('event-space/<uuid:user_id>/', EventSpace.as_view(), name="event_space"),
    path('host-list/<uuid:user_id>/', EventHostList.as_view(), name="host_list"),

    # Amase Data Migrations
    path('amase-data/', AmaseData.as_view(), name="amase_data_migrate"),
    path('update-user-type/', UpdateUserType.as_view(), name="update_user_type"),
]