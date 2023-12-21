from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView
)
from django.urls import reverse
from django.urls import reverse_lazy

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View

from apps.mentor_panel.models import MentoringTypes, TargetAudience
from .forms import CreateMentoringTypeForm, CreateTargetAudienceForm

# Create your views here.


@method_decorator(login_required, name='dispatch')
class Dashboard(View):
    def get(self, request):
        return render(request, 'Dashboard/dashboard.html')


@method_decorator(login_required, name='dispatch')
class Learn(View):
    def get(self, request):
        return render(request, 'Learn/mentor-learn.html')


@method_decorator(login_required, name='dispatch')
class Activity(View):
    def get(self, request):
        return render(request, 'Activity/mentor-activity.html')


@method_decorator(login_required, name='dispatch')
class Mentees(View):
    def get(self, request):
        return render(request, 'Mentor/mentees.html')


@method_decorator(login_required, name='dispatch')
class Community(View):
    def get(self, request):
        return render(request, 'Community/community.html')


@method_decorator(login_required, name='dispatch')
class Goals(View):
    def get(self, request):
        print("Hey Shru!")
        return render(request, 'Goals/mentor-goals.html')


@method_decorator(login_required, name='dispatch')
class Support(View):
    def get(self, request):
        return render(request, 'Support/support.html')

@method_decorator(login_required, name='dispatch')
class MentorCalendar(View):
    def get(self, request):
        return render(request, 'MentorCalendar/calendar.html')
@method_decorator(login_required, name='dispatch')
class CreateMentoringTypes(CreateView, ListView):
    model = MentoringTypes
    form_class = CreateMentoringTypeForm
    success_url = reverse_lazy('mentor:create_list_mentoring_types')
    template_name = "AdminPanel/create_mentoring_types.html"
    context_object_name = "mentoring_types"
    
    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super().form_valid(form)

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_delete=False)
    
class UpdateMentoringTypes(UpdateView):
    template_name = "AdminPanel/create_mentoring_types.html"
    model = MentoringTypes
    form_class = CreateMentoringTypeForm
    success_url = reverse_lazy('mentor:create_list_mentoring_types')

@method_decorator(login_required, name='dispatch')
class CreateTargetAudience(CreateView, ListView):
    template_name = "AdminPanel/create_target_audience.html"
    model = TargetAudience
    form_class = CreateTargetAudienceForm
    context_object_name = "target_audiences"
    success_url = reverse_lazy('mentor:create_list_target_audience')
    
    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super().form_valid(form)

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_delete=False)
    
class UpdateTargetAudience(UpdateView):
    template_name = "AdminPanel/create_target_audience.html"
    model = TargetAudience
    form_class = CreateTargetAudienceForm
    success_url = reverse_lazy('mentor:create_list_target_audience')


@login_required
def DeleteMentoringTypes(request):
    MentoringTypes.objects.filter(id=request.POST['id']).update(is_active=False, is_delete=True)
    return redirect(reverse('mentor:create_list_mentoring_types'))

@login_required
def DeleteTargetAudience(request):
    TargetAudience.objects.filter(id=request.POST['id']).update(is_active=False, is_delete=True)
    return redirect(reverse('mentor:create_list_target_audience'))
