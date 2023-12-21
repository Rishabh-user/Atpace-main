from django.urls.base import reverse
from apps.users.models import UserTypes
from django.shortcuts import redirect, render


def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func


def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if not "user_type" in request.session:
                return redirect(reverse('user:logout'))
            group = None
            # if request.user.userType.all():
            #     group = request.user.userType.all().type
            #     print(group)
            if request.session['user_type'] in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return render(request, '404.html')
        return wrapper_func
    return decorator


def admin_only(view_func):
    def wrapper_function(request, *args, **kwargs):
        group = None
        if not "user_type" in request.session:
            return redirect(reverse('user:logout'))
        if request.session['user_type'] == "Admin":

            user_type = UserTypes.objects.get(type="Admin")
            if user_type in request.user.userType.all():
                group = "Admin"
                print(group)

        if request.session['user_type'] == 'Learner':
            return redirect(reverse('content:browse_channel'))
        elif request.session['user_type'] == "Mentor":
            return redirect(reverse('user:user-dashboard'))

        if group == 'Admin':

            return view_func(request, *args, **kwargs)

    return wrapper_function

def user_only(view_func):
    def wrapper_function(request, *args, **kwargs):
        group = None
        if not "user_type" in request.session:
            return redirect(reverse('user:logout'))
        
        if request.session['user_type'] == "Learner":
            
            user_type = UserTypes.objects.get(type="Learner")
            if user_type in request.user.userType.all():
                group = "Learner"

        if group == 'Learner':

            return view_func(request, *args, **kwargs)
        else:
            return render(request, '404.html')

    return wrapper_function
