# from django.contrib.auth.backends import ModelBackend
# # Models
# from users.models import User, UserTypes


# class EmailModelBackend(ModelBackend):
#     """
#     authentication class to login with the email address.
#     """

#     def authenticate(self, request, username=None, password=None, type=None, ** kwargs):
#         # type = request.POST.get('type')

        
#         if '@' in username:
#             kwargs = {'email': username}
#             print(kwargs)
#         else:
#             return None
#         if password is None:
#             return None
#         try:
#             user = User.objects.get(**kwargs)
#             print("user", user)
#         except User.DoesNotExist:
#             return None

#         else:
#             if user.check_password(password) and self.user_can_authenticate(user):
#                 return user

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


UserModel = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(username, "username")

        try:
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
            return
        except UserModel.MultipleObjectsReturned:
            user = UserModel.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user