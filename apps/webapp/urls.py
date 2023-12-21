from django.urls import path
from .views import *
from .utils import renderpartners

app_name = "web_app"

urlpatterns = [
    path('general-settings/', GeneralSettings.as_view(), name="general_settings"),
    path('homepage-journey/', CreateHomepageJourney.as_view(), name="homepage_journey"),
    path('add-testimonial/', CreateTestimonial.as_view(), name="add_testimonial"),
    path('contace-messages/', ContactMessages.as_view(), name="contace_messages"),
    path('delete-journey/', delete_HomepageJourney, name="delete_journey"),
    path('team-members/', AddTeamMembers.as_view(), name="team_members"),
    path('edit-member/<int:pk>/', EditTeamMembers.as_view(), name="edit_members"),
    path('delete-member/', delete_TeamMembers, name="delete_member"),
    path('subsribe-mail/', SubscriptionMails, name='subsribe_mail'),
    path('post-details/<int:space_id>/<int:community_id>/<int:post_id>/',
         CommunityPostDetails.as_view(), name='post_details'),
    path('post-comment/', PostComment.as_view(), name="post_comment"),
    path('redirect-partners', renderpartners, name="redirect-partners")

    # path('add-journey-to-cart/', add_journey_to_cart, name="add_journey_to_cart"),
]
