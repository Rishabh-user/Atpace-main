import pandas as pd
from apps.api.utils import assessment_data_sheet
from apps.content.models import Channel
from ravinsight.decorators import admin_only
from datetime import datetime
from django.urls import reverse_lazy
from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from apps.content.models import Channel
from apps.program_manager_panel.forms import SubscriptionForm, SubscriptionOfferForm, UpdateSubscriptionOfferForm, MentorMenteeRatioForm
from apps.program_manager_panel.models import Subscription, SubscriptionOffer, MentorMenteeRatio
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView
)
import pandas as pd
from apps.users.models import Company, User, UserTypes
from django.contrib import messages
import csv
from ravinsight.web_constant import SITE_NAME, DOMAIN, PROTOCOL
from django.http import HttpResponse
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
# Create your views here.

@method_decorator(login_required, name='dispatch')
class Billing(View):
    def get(self, request):
        return render(request, 'billing/billing.html')


@method_decorator(login_required, name='dispatch')
class Communication(View):
    def get(self, request):
        return render(request, 'communication/communication.html')


@method_decorator(login_required, name='dispatch')
class Analytics(View):
    def get(self, request):
        return render(request, 'analytics/analytics.html')

@method_decorator(login_required, name='dispatch')
class Marketplace(View):
    def get(self, request):
        return render(request, 'marketplace/marketplace.html')

@method_decorator(login_required, name='dispatch')
class GenerateCertificate(View):
    def get(self, request):
        return render(request, 'generate_certificate/generate_certificate.html')


@method_decorator(login_required, name='dispatch')
class ReviewMentorMarketplace(View):
    def get(self, request):
        return render(request, 'admin/review_mentor_marketplace.html')


@method_decorator(login_required, name='dispatch')
class Manage(View):
    def get(self, request):
        if 'UserDashboardView' in request.session:
            del request.session['UserDashboardView']
            del request.session['dashbordId']
        return render(request, 'manage/manage.html')

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CreateSubscriptions(CreateView):
    '''
        Create Subscriptions.
    '''
    model = Subscription
    context_object_name = "subscriptions"
    form_class = SubscriptionForm
    template_name = "AdminPanal/create-subscription.html"
    success_url = reverse_lazy('program_manager:subscription_list')

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super().form_valid(form)

    

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class SubscriptionsList(ListView):
    '''
        Render Subscriptions.
    '''
    model = Subscription
    context_object_name = "subscriptions"
    template_name = "AdminPanal/subscription-list.html"

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_delete=False)

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class UpdateSubscriptions(UpdateView):
    '''
        Update Subscriptions.
    '''
    model = Subscription
    form_class = SubscriptionForm
    success_url = reverse_lazy('program_manager:subscription_list')
    template_name = "AdminPanal/create-subscription.html"

@admin_only
@login_required
def delete_subscription(request, subscription_id):
    '''
        Delete Subscriptions.
    '''
    Subscription.objects.filter(id=subscription_id).update(is_active=False, is_delete=True)
    return redirect(reverse('program_manager:subscription_list'))

@method_decorator(login_required, name='dispatch')
class Matching(View):
    def get(self, request):
        return render(request, 'matching/matching.html')

@method_decorator(login_required, name='dispatch')
class Content(View):
    def get(self, request):
        return render(request, 'content/content.html')
    
@method_decorator(login_required, name='dispatch')
class Calendar(View):
    def get(self, request):
        return render(request, 'calendar/calendar.html')


@method_decorator(login_required, name='dispatch')
class Security(View):
    def get(self, request):
        return render(request, 'security/security.html')

@method_decorator(login_required, name='dispatch')
class Setup(View):
    def get(self, request):
        return render(request, 'setup/setup.html')
    
@method_decorator(login_required, name='dispatch')
class Proxy(View):
    def get(self, request):
        return render(request, 'proxy/proxy.html')

@method_decorator(login_required, name='dispatch')
class Activity(View):
    def get(self, request):
        return render(request, 'Activity/program_manager_activity.html')

@method_decorator(login_required, name='dispatch')
class RiskPairs(View):
    def get(self, request):
        return render(request, 'risk/risk.html')
@method_decorator(login_required, name='dispatch')
class TaskStatusTemplate(View):
    def get(self, request, *args, **kwargs):
        context = {
            "task_id":self.kwargs["task_id"]
        }
        return render(request, 'calendar/task_status.html', context)

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CreateSubscriptionOffer(CreateView):
    '''
        Create Subscriptions Offer.
    '''
    model = SubscriptionOffer
    form_class = SubscriptionOfferForm
    template_name = "AdminPanal/create-subscription.html"
    success_url = reverse_lazy('program_manager:subscription_offer_list')

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        print("obj1 ",f)
        if f.discount_percentage>0:
            f.subs_price(f.discount_percentage, f.subscription)
            print("obj2 ",f)
        if f.discount_price>0:
            f.final_prices(f.discount_price, f.subscription)
            print("obj3 ",f)
        if f.end_date and f.start_date:
            f.durations(f.end_date, f.start_date)
        f.save()
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class SubscriptionOfferList(ListView):
    '''
        Render Subscriptions Offer.
    '''
    model = SubscriptionOffer
    context_object_name = "subscriptions_offer"
    template_name = "AdminPanal/subscription-offer-list.html"

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_delete=False)

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class UpdateSubscriptionOffer(UpdateView):
    '''
        Update Subscriptions Offer.
    '''
    model = SubscriptionOffer
    form_class = UpdateSubscriptionOfferForm
    success_url = reverse_lazy('program_manager:subscription_offer_list')
    template_name = "AdminPanal/create-subscription.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        if f.discount_percentage>0:
            f.subs_price(f.discount_percentage, f.subscription)
        elif f.discount_price>0:
            f.final_prices(f.discount_price, f.subscription)
        if f.end_date and f.start_date:
            f.durations(f.end_date, f.start_date)
        f.created_by = self.request.user
        f.save()
        return super().form_valid(form)

@admin_only
@login_required
def delete_subscription_offer(request, offer_id):
    '''
        Delete Subscriptions Offer.
    '''
    SubscriptionOffer.objects.filter(id=offer_id).update(is_active=False, is_delete=True)
    return redirect(reverse('program_manager:subscription_offer_list'))

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CreateMenteeRatio(CreateView):
    '''
        Create Mentor Mentee Ratio.
    '''
    model = MentorMenteeRatio
    form_class = MentorMenteeRatioForm
    template_name = "AdminPanal/create-mentee-ratio.html"
    success_url = reverse_lazy('program_manager:mentor_mentee_ratio_list')

    def form_valid(self, form):
        f = form.save(commit=False)
        f.max_member_count(f.max_mentor, f.max_learner)
        f.created_by=self.request.user
        f.save()
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class MenteeRatioList(ListView):
    '''
        Render Mentor Mentee Ratio.
    '''
    model = MentorMenteeRatio
    context_object_name = "mentor_mentee_ratio"
    template_name = "AdminPanal/mentor-mentee-ratio-list.html"

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_delete=False, created_by=self.request.user)

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class UpdateMenteeRatio(UpdateView):
    '''
        Update Mentor Mentee Ratio.
    '''
    model = MentorMenteeRatio
    form_class = MentorMenteeRatioForm
    success_url = reverse_lazy('program_manager:mentor_mentee_ratio_list')
    template_name = "AdminPanal/create-mentee-ratio.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.max_member_count(f.max_mentor, f.max_learner)
        f.save()
        return super().form_valid(form)

@admin_only
@login_required
def delete_mentee_ratio(request, ratio_id):
    '''
        Delete Mentor Mentee Ratio.
    '''
    MentorMenteeRatio.objects.filter(id=ratio_id).update(is_active=False, is_delete=True)
    return redirect(reverse('program_manager:mentor_mentee_ratio_list'))


@method_decorator(login_required, name='dispatch')
class InviteMentorFromCSV(View):

    def post(self, request, *args, **kwargs):

        company = Company.objects.get(pk=request.POST['company_id'])
        file = request.FILES['file']
        decoded_file = file.read().decode('utf-8').splitlines()

        # try:
        reader = csv.reader(decoded_file)
        for data in reader:
            email = data[3]
            mentor = User.objects.filter(email__iexact=email).first()
            if mentor:
                print("mentor exists")
                if mentor.userType.filter(type='Mentor').exists():
                    # Send mail for profile enhancement
                    print("mentor exists with mentor type")
                else:
                    # Send mail for change user type
                    print("mentor exists with different type")
            else:
                print("Mentor does not exists")
                # Send mail for registration    
                subject = "Invitation for Marketplace"
                email_template_name = "email/marketplace_mentor_registration.txt"

                c = {
                    'domain': DOMAIN,
                    'site_name': SITE_NAME,
                    "company": company,
                }
                email_string = render_to_string(email_template_name, c)
                try:
                    send_mail(subject, email_string, 'info@growatpace.com', [email], fail_silently=False)
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')  

        # except Exception:
            # messages.error(request, "Invalid csv file or data format incorrect")
        return redirect(reverse('program_manager:marketplace'))
    
@method_decorator(login_required, name='dispatch')
class GenerateAssessmentDataReport(View):
    def get(self, request):

        company = request.user.company.all()
        all_journey = Channel.objects.filter(company__in=company, parent_id=None, is_delete=False, is_active=True, closure_date__gt=datetime.now())
        context = {
            "journey": all_journey
        }
        return render(request, 'manage/assessment_report.html', context)

    def post(self, request):
        journey = Channel.objects.get(pk=request.POST['journey'])
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="AssessmentDataReport.csv"'
        headers = ["Attemp_ID", "Test_Name", "Question", "Answer_Selected", "Question_Mark", "Marks_Obtained", "Journey_Name", "Assessment_type", "Attempt_Time", "User_Email", "Microskill", "Q No"]
        res = assessment_data_sheet(journey)
        df = pd.DataFrame(res ,columns=headers )
        df.to_csv(response, index=False)
        print("csv done")   
        return response
