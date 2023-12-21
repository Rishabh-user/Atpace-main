from datetime import datetime
import requests
from apps.content.models import Channel, Content, MentoringJourney, UserChannel, journeyContentSetup
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.views.generic import ListView, CreateView, UpdateView
from apps.users.views import check_check_box
from apps.utils.models import JourneyCategory, Tags
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator
from apps.webapp.forms import GrowAtpaceTeamForm, HomepageJourneyForm, TestimonialForm
from apps.webapp.utils import public_Post_Comment, add_user_to_sheets, journey_content_list
from apps.atpace_community.models import SpaceJourney
from .models import GrowAtpaceTeam, HomepageJourneys, contact_us, Review, subscribeEmails, Testimonial
from apps.community.utils import get_space_post, get_space_post_comment, get_space_post_details, CommunityAllSpaces
from apps.community.models import CommunitySignupList
from apps.payment_gateway.models import AddJourneyToCart
from django.http import HttpResponse
from apps.users.models import User, Company
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models.query_utils import Q


class Index(View):
    def get(self, request, **kwargs):
        journey = HomepageJourneys.objects.filter(is_display=True).order_by('display_order')[:9]
        testimonial = Testimonial.objects.all()
        data = []
        for channel in journey:
            content = Content.objects.filter(Channel=channel.journey)

            data.append({
                "journey": channel.journey,
                "content": content.count(),
            })
        # print(data)
        context = {
            "journey": data,
            "testimonial": testimonial
        }

        return render(request, 'website/index.html', context)


class AboutUs(View):
    def get(self, request, **kwargs):
        team = GrowAtpaceTeam.objects.all()
        return render(request, 'website/about_us.html', {"team": team})


class ContactUs(View):
    def get(self, request, **kwargs):
        return render(request, 'website/contact.html')

    def post(self, request):
        name = request.POST['name']
        email = request.POST['subject']
        subject = request.POST['email']
        message = request.POST['message']
        profession = request.POST['profession']
        phone = request.POST['phone']
        phone = phone.replace("+","").replace(" ", "")
        is_term_apply = check_check_box(request.POST.get('is_term_apply', True))
        contact_us.objects.create(name=name, email=email, subject=subject, profession=profession, phone=phone,
                                  message=message, is_term_apply=is_term_apply)

        return render(request, 'website/contact.html')


class Resources(View):
    def get(self, request, **kwargs):
        return render(request, 'website/resources.html')


class Pricing(View):
    def get(self, request, **kwargs):
        return render(request, 'website/pricing.html')


class Program(View):
    def get(self, request, **kwargs):
        title = request.GET.get('search')
        category = request.GET.get('category')
        company = request.GET.get('company')
        tag = request.GET.get('tag')
        type = request.GET.get('type')
        price = request.GET.get('price')


        journey = Channel.objects.filter(is_active=True, is_delete=False, parent_id=None, show_on_website=True, closure_date__gt=datetime.now())
        if category_obj:= JourneyCategory.objects.filter(category=category):
            journey = journey.filter(category__in=category_obj)
        elif title:
            journey = journey.filter(Q(title__icontains=title)| Q(category__category__icontains=title, category__is_active=True) | Q(channel_type__icontains=title) | Q(company__name__icontains=title) | Q(tags__icontains=title) )
        elif company:
            journey = journey.filter(company__name=company)
        elif tag:
            journey = journey.filter(tags__icontains=tag)
        elif type:
            journey = journey.filter(channel_type=type)
        elif price:
            journey = journey.filter(is_paid=price)
        data = []
        categorys = JourneyCategory.objects.filter(is_active=True)
        companys = Company.objects.filter(is_delete=False)
        tags = Tags.objects.filter(is_active=True)
        for journey in journey:
            content = journey_content_list(journey)
            data.append({
                "journey": journey,
                "content": content.count(),
            })
        # print(data)
        paginator = Paginator(data, 6)
        page_number = request.GET.get('page', 1)
        pages = paginator.get_page(page_number)
        context = {
            "journey": pages,
            "category": categorys,
            "company": companys,
            "tag": tags
        }
        return render(request, 'website/programs.html', context)


class PublicCommunity(View):
    def get(self, request, **kwargs):
        community_id = "22900"
        space_id = "165387"
        data = get_space_post(community_id, space_id)
        all_spaces = CommunityAllSpaces(community_id)
        # print(all_spaces)
        all_post = []
        for data in data:
            all_post.append({
                "community_id": data['community_id'],
                "space_id": data['space_id'],
                "id": data['id'],
                "name": data['name'],
                "user_name": data['user_name'],
                "user_avatar_url": data['user_avatar_url'],
                "body": data['body']['body'],
                "created_at": data['created_at'],
                "user_likes_count": data['user_likes_count'],
                "user_comments_count": data['user_comments_count'],
                "comment": []
            })
        paginator = Paginator(all_post, 10)
        page_number = request.GET.get('page', 1)
        pages = paginator.get_page(page_number)
        context = {
            "data": pages,
            "all_spaces": all_spaces,
        }
        return render(request, 'website/community.html', context)


class CommunityPostDetails(View):
    def get(self, request, **kwargs):
        community_id = self.kwargs['community_id']
        # print(community_id)
        post_id = self.kwargs['post_id']
        # print(post_id)
        space_id = self.kwargs['space_id']
        # print(space_id)
        data = get_space_post_details(community_id, post_id)
        comment = get_space_post_comment(community_id, space_id, post_id)
        details = []
        all_spaces = CommunityAllSpaces(community_id)
        details.append({
            "community_id": data['community_id'],
            "space_id": data['space_id'],
            "id": data['id'],
            "name": data['name'],
            "user_name": data['user_name'],
            "user_avatar_url": data['user_avatar_url'],
            "body": data['body']['body'],
            "created_at": data['created_at'],
            "user_likes_count": data['user_likes_count'],
            "user_comments_count": data['user_comments_count'],
            "comment": comment,
        })
        context = {
            "data": details,
            "all_spaces": all_spaces
        }
        return render(request, 'website/community.html', context)


class PostComment(View):
    def post(self, request):
        post_id = request.POST['post_id']
        body = request.POST['body']
        community_id = request.POST['community_id']
        space_id = request.POST['space_id']
        public_Post_Comment(post_id, body, space_id, community_id, request.user)
        return redirect(reverse('web_app:post_details', kwargs={'post_id': post_id, "community_id": community_id, "space_id": space_id}))


class CourseDetailsView(View):
    def get(self, request, course_id):

        journey = Channel.objects.get(pk=course_id)
        is_added_to_cart = False
        is_user_added_to_journey = False
        if request.user.is_authenticated:
            if AddJourneyToCart.objects.filter(journey=journey, user=request.user, is_added=True).exists():
                is_added_to_cart = True

            if UserChannel.objects.filter(Channel=journey, user=request.user, status='Joined').exists():
                is_user_added_to_journey = True

        content = journey_content_list(journey)
        related_journey = Channel.objects.filter(category=journey.category)
        # print(related_journey)

        journey_page_content = journeyContentSetup.objects.filter(
            journey_id=course_id, is_active=True, is_delete=False)
        # print(journey_page_content, "204@@@@@@@@")
        cta_button_title = pdpa_statement  = cta_button_action = video_url = overview = learn_label = pdpa_label = ""
        if journey_page_content:
            journey_page_content = journey_page_content.first()
            pdpa_statement = journey_page_content.pdpa_description
            pdpa_label = journey_page_content.pdpa_label
            learn_label = journey_page_content.learn_label
            overview = journey_page_content.overview
            video_url = journey_page_content.video_url
            cta_button_action = journey_page_content.cta_button_action
            cta_button_title = journey_page_content.cta_button_title

        # user = User.objects.get(pk=request.user.id)
        # # print("user_type", user.userType.all())

        context = {
            "journey": journey,
            "related_journey": related_journey,
            "content": content.count(),
            "is_added_to_cart": is_added_to_cart,
            "is_user_added_to_journey": is_user_added_to_journey,
            "cta_button_title": cta_button_title, 
            "cta_button_action": cta_button_action, 
            "overview": overview,
            "pdpa_statement": pdpa_statement, 
            "pdpa_label": pdpa_label, 
            "learn_label": learn_label, 
            "video_url": video_url,
        }
        response = render(request, 'website/course_details.html', context)
        response.delete_cookie('course_detail_url')
        return response


class TransitionToSuccess(View):
    def get(self, request, **kwargs):
        journey = Channel.objects.filter(is_active=True, parent_id=None, is_delete=False).order_by('?')[:4]
        all_review = Review.objects.all()
        context = {
            "journey": journey,
            "all_review": all_review
        }
        return render(request, 'website/transition_to_success.html', context)

    def post(self, request):
        name = request.POST['name']
        title = request.POST['title']
        email = request.POST['email']
        description = request.POST['description']
        if request.user.is_authenticated:
            user_id = request.user.id
            user_type = "User"
        else:
            user_type = "Guest"
            user_id = ""
        Review.objects.create(name=name, email=email, summary=description, title=title, user_id=user_id,
                              user_type=user_type)

        return redirect(reverse_lazy('user:transition_to_success'))

@method_decorator(login_required, name='dispatch')
class GeneralSettings(View):
    def get(self, request):
        return render(request, 'web_admin/general_settings.html')


@method_decorator(login_required, name='dispatch')
class CreateHomepageJourney(CreateView, ListView):
    model = HomepageJourneys
    form_class = HomepageJourneyForm
    context_object_name = "homepagejourney"
    success_url = reverse_lazy('web_app:homepage_journey')
    template_name = "website/homepagejourney.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.display_order += 1
        f.save()
        return super().form_valid(form)

    def get_queryset(self):
        return self.model.objects.filter(is_display=True)


@login_required
def delete_HomepageJourney(request):
    if request.method == 'POST':
        journey = HomepageJourneys.objects.get(pk=request.POST['pk'])
        journey.is_display = False
        journey.display_order -= 1
        journey.save()
        return redirect(reverse('web_app:homepage_journey'))


@method_decorator(login_required, name='dispatch')
class AddTeamMembers(CreateView, ListView):
    model = GrowAtpaceTeam
    form_class = GrowAtpaceTeamForm
    context_object_name = 'Team'
    success_url = reverse_lazy('web_app:team_members')
    template_name = 'website/Team.html'

    def form_valid(self, form):
        f = form.save(commit=False)
        f.display_order += 1
        f.save()
        return super().form_valid(form)

    def get_queryset(self):
        return self.model.objects.filter(is_active=True)


@method_decorator(login_required, name='dispatch')
class EditTeamMembers(UpdateView):
    model = GrowAtpaceTeam
    form_class = GrowAtpaceTeamForm
    success_url = reverse_lazy('web_app:team_members')
    template_name = 'website/Team.html'


@login_required
def delete_TeamMembers(request):
    if request.method == 'POST':
        team = GrowAtpaceTeam.objects.get(pk=request.POST['pk'])
        team.is_active = False
        team.display_order -= 1
        team.save()
        return redirect(reverse('web_app:team_members'))


@login_required
def SubscriptionMails(request):
    response = False
    if request.method == 'POST':
        email = request.POST['email']
        mail = subscribeEmails.objects.filter(subscriber_mail__iexact=email).first()
        if not mail:
            subscribeEmails.objects.create(subscriber_mail=email)
            response = True
        return response


@method_decorator(login_required, name='dispatch')
class CreateTestimonial(CreateView, ListView):
    model = Testimonial
    form_class = TestimonialForm
    context_object_name = "testimonial"
    success_url = reverse_lazy('web_app:add_testimonial')
    template_name = "web_admin/add_testimonials.html"


@method_decorator(login_required, name='dispatch')
class ContactMessages(ListView):
    model = contact_us
    context_object_name = "contact_us"
    template_name = "web_admin/contact_us_list.html"


def timeZone(request, *args, **kwargs):
    if request.method == "POST":
        time_zone = request.POST['timezone']


class ThankYou(View):
    def get(self, request):
        return render(request, 'website/community-signup--thankyou.html')


class CommunitySignup(View):
    def get(self, request, **kwargs):
        return render(request, 'website/community-signup.html')

    def post(self, request, **kwargs):
        name = request.POST['name']
        password = request.POST['password']
        email = request.POST['email']
        community_id = "22900"
        CommunitySignupList.objects.create(name=name, email=email)
        add_user_to_sheets(name, email)
        url = f"http://app.circle.so/api/v1/community_members?email={str(email)}&name={str(name)}&password={str(password)}&community_id={community_id}&skip_invitation=false"
        # print(url)
        headers = {
            'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
        }
        response_body = requests.post(
            url=url,
            headers=headers,

        )
        data = response_body.json()

        # print(data)

        # CicleDataDump.objects.create(data=data, type="invite_member")
        if data['success']:

            return redirect(reverse_lazy("user:thank-you"))

        return redirect(reverse_lazy("user:community_signup"))


# def add_journey_to_cart(request):
#     if request.method == "POST":
#         if request.user.is_authenticated:
#             journey_id = request.POST['id']
#             user = User.objects.get(pk=request.user.id)
#             journey = Channel.objects.get(pk=journey_id)
#             if AddJourneyToCart.objects.filter(journey=journey, user=user, is_added=True).exists():
#                 return HttpResponse("Journey Already Exist")
#             else:
#                 try:
#                     AddJourneyToCart.objects.create(user=user, journey=journey, is_added=True)
#                 except:
#                     return HttpResponse("Something went wrong")

#                 return HttpResponse("Journey Added to Cart")
#         else:
#             return HttpResponse("User is not authenticated")
