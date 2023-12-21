from django.urls import path
from .views import *
from .utils import *

app_name = "utils"

urlpatterns = [
    path('category/', Category.as_view(), name="category"),
    path('tags/', TagsView.as_view(), name="tags"),
    path('industry/', IndustryView.as_view(), name="industry"),
    path('pool/', PoolView.as_view(), name="pool"),
    path('edit-pool/<uuid:pk>/', UpdatePool.as_view(), name="edit_pool"),
    path('delete-pool/', DeletePool, name="delete_pool"),
    path('matching/', Matching.as_view(), name="matching"), 
    path('update_mentor_pool/', update_mentor_pool, name="update_mentor_pool"), 
    path('add_mentor_pool/', add_mentor_pool, name="add_mentor_pool"),
    path('email-list/', UserEmailStatus.as_view(), name="email_list"),
    path('url-shortner/', UrlShortnerView.as_view(), name="url_shortner"),
    path('dyte/<uuid:meet_id>', RedirectToDyte.as_view(), name="dyte_redirect"),
    path('dyte-guest-user/<uuid:meet_id>', RedirectToGuestUser.as_view(), name="dyte_guest_user"),
    path('get-guest-user/<uuid:meet_id>', get_guest_user, name="get_guest_user"),
    path('populate', populate),
    path('log-file/', LogFileView.as_view(), name="log_file" ),
    path('logs/<str:folder_name>/', FileView.as_view(), name="logs" )
]