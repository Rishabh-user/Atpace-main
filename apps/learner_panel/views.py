from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
# Create your views here.

@method_decorator(login_required, name='dispatch')
class Dashboard(View):
    def get(self, request):
        return render(request, 'Dashboard/dashboard.html')


@method_decorator(login_required, name='dispatch')
class Learn(View):
    def get(self, request):
        return render(request, 'Learn/learn.html')


@method_decorator(login_required, name='dispatch')
class Activity(View):
    def get(self, request):
        return render(request, 'Activity/activity.html')

    
@method_decorator(login_required, name='dispatch')
class Mentor(View):
    def get(self, request):
        return render(request, 'Mentor/mentor.html')


@method_decorator(login_required, name='dispatch')
class Community(View):
    def get(self, request):
        return render(request, 'Community/community.html')

@method_decorator(login_required, name='dispatch')
class Goals(View):
    def get(self, request):
        return render(request, 'Goals/goals.html')

@method_decorator(login_required, name='dispatch')
class Support(View):
    def get(self, request):
        return render(request, 'Support/support.html')