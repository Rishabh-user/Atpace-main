from django.conf import settings

from apps.users.models import User


def debug(context):
    return {'DEBUG': settings.DEBUG}


def get_footer(context):
    context = {
        "APP_VERSION": "2.0.1"
    }
    return context



# def get_sidebar(request):
#     dashboard_user=""
#     if len(str(request.path).split("/"))>2:
#         print(str(request.path).split("/")[2], "id")
#         Cpath=request.path
#         dashoboard_user_id = str(Cpath).split("/")[2]
#         dashboard_user = User.objects.get(id=dashoboard_user_id)
#         context = {
#             "dashboard_user": dashboard_user
#         }
#     context = {
#         "dashboard_user": dashboard_user
#     }
#     return context
