from django.core.files import File
import json
import googletrans
import os
from threading import *
from datetime import datetime
from django.template.loader import render_to_string
from apps.api.utils import assessment_attempt_channel
from apps.atpace_community.models import SpaceJourney
from apps.atpace_community.utils import add_member_to_space, create_journey_space, update_space_journey
from apps.community.models import JourneySpace, LearningJournals, WeeklyLearningJournals, WeeklyjournalsTemplate
from apps.community.utils import AddMembertoSpace, create_journey_private_space
from apps.content.time_cal import LinkTime, TextTime
from apps.content.utils import is_parent_channel, public_announcement_list, company_journeys, replicate_profile_assessment, replicate_journey_content, replicate_journey_content_setup, replicate_skill_journey_data, replicate_skill_data
from apps.leaderboard.views import CourseCompletion, NotificationAndPoints, CheckEndOfJourney, send_push_notification
from apps.users.views import check_check_box
from apps.vonage_api.models import VonageWhatsappReport
from apps.api.utils import update_boolean
from ravinsight.decorators import admin_only, allowed_users, user_only
from apps.test_series.models import TestSeries
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse, response
from django.shortcuts import redirect

from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    TemplateView
)
from ravinsight.web_constant import SITE_NAME, DOMAIN, INFO_CONTACT_EMAIL, PROTOCOL, COMMUNITY_URL
from django.urls import reverse
from django.views import View
from .models import (
    Channel, ContentChannels, ContentData, ProgramTeamAnnouncement, Content,
    VideoSubtitles, ChannelGroup, ChannelGroupContent,
    JourneyContentSetupOrdering, MentoringJourney, PublicProgramAnnouncement,
    SkillConfig, SkillConfigLevel, SurveyAttemptChannel, SurveyChannel,
    UserChannel, ContentDataOptions, ContetnOptionSubmit, TestAttempt,
    UserCourseStart, UserReadContentData, ProgramAnnouncementWhatsappReport,
    journeyContentSetup, UserActivityData, journeyContentSetup,
    CertificateTemplate, CertificateSignature, UserCertificate)
from apps.survey_questions.models import Survey, SurveyAttempt, SurveyLabel
from django.shortcuts import render
from .forms import (ChannelCreationFrom, SubChannelCreationFrom,
                    ContentCreationFrom, CreateChannelGroupFrom,
                    journeyContentCreationForm)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.utils.utils import striphtml
from apps.users.models import Company, Learner, ProficiencyLevel, ProfileAssestQuestion, User, UserRoles
from django.db.models import Q
import math
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import random
from django.core.mail import send_mail, BadHeaderError
from .utils import Journey, get_display_content, public_channel_list, change_course_status_in_group
from apps.vonage_api.utils import journey_enrolment
from apps.users.helper import add_user_to_company
from django.contrib import messages
from apps.users.utils import getJourneyUsers
# Create your views here.


@method_decorator(login_required, name='dispatch')
@method_decorator(allowed_users(allowed_roles=["Admin", "ProgramManager"]),
                  name="dispatch")
class CreateChannel(CreateView):
    model = Channel
    form_class = ChannelCreationFrom
    # success_url = reverse_lazy('content:channel_list')
    template_name = "channel/create_channel.html"

    def get_form_kwargs(self):
        """
        Passes the request object to the form class
        """
        kwargs = super(CreateChannel, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        survey_level = SurveyLabel.objects.filter(label="Default").first()
        if f.is_community_required:
            create_journey_space(f, self.request.user)
        ChannelGroup.objects.create(title="Default",
                                    channel=f,
                                    channel_for=survey_level)
        return super(CreateChannel, self).form_valid(form)

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:setup')
        else:
            return reverse('content:channel_list')


@login_required
def copy_journey_data(request):
    if request.method == "POST":
        journey_id = request.POST['pk']
        journey_name = request.POST['journey']
        try:
            channel = Channel.objects.get(pk=journey_id)
            journey = channel

            journey.pk = None
            journey.title = journey_name
            journey.whatsapp_notification_required = update_boolean(
                request.POST['is_wp_required'])
            journey.show_on_website = update_boolean(
                request.POST['show_on_website'])
            journey.is_lite_signup_enable = update_boolean(
                request.POST['is_lite_signup_enable'])
            journey.created_by = request.user
            journey.save()
            survey_level = SurveyLabel.objects.filter(label="Default").first()
            channel_group = ChannelGroup.objects.create(
                title="Default", channel=journey, channel_for=survey_level)

            if update_boolean(request.POST['profile_assessment']) == True:
                replicate_profile_assessment(journey_id, channel.pk)

            if update_boolean(request.POST['add_to_community']) == True:
                create_journey_space(channel, request.user)

            if update_boolean(request.POST['replicate_content']) == True:
                replicate_journey_content(journey_id, journey, channel_group,
                                          request.user)

            replicate_journey_content_setup(journey_id, channel, request.user)
        except Channel.DoesNotExist:
            return JsonResponse({
                "message": "channel not found",
                "success": False
            })
        return JsonResponse({
            "message": "New Journey created",
            "success": True
        })


@login_required
def copy_skill_journey_data(request):
    if request.method == "POST":
        journey_id = request.POST['pk']
        journey_name = request.POST['journey']
        try:
            channel = Channel.objects.get(pk=journey_id)
        except Channel.DoesNotExist:
            return JsonResponse({
                "message": "channel not found",
                "success": False
            })

        skill_channel = Channel.objects.filter(parent_id=channel)
        skill_config = SkillConfig.objects.filter(channel=channel)
        journey, channel_group = replicate_skill_journey_data(
            channel, journey_name, request.user)

        for skill in skill_channel:
            replicate_skill_data(skill, journey, channel_group, skill_config,
                                 request.user)

        return JsonResponse({
            "message": "New Journey created",
            "success": True
        })


@login_required
def load_program_team(request):
    company_id = request.GET.get('company')
    company = Company.objects.get(id=company_id)
    user_list = User.objects.filter(userType__type="ProgramManager",
                                    company=company).order_by('email')
    response = {'user-list': user_list}
    return render(request, 'channel/create_channel.html', response)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class SubChannel(CreateView):
    model = Channel
    form_class = SubChannelCreationFrom
    success_url = reverse_lazy('content:sub_channel_list')
    template_name = "channel/create_channel.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        for i in ProficiencyLevel.objects.all():
            survey_level = SurveyLabel.objects.filter(label=i.level).first()
            ChannelGroup.objects.create(title=i.level,
                                        start_mark=i.start,
                                        end_marks=i.end,
                                        channel=f,
                                        channel_for=survey_level)

        return super(SubChannel, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(allowed_users(allowed_roles=["Admin", "ProgramManager"]),
                  name="dispatch")
class UpdateChannel(UpdateView):
    model = Channel
    form_class = ChannelCreationFrom
    # success_url = reverse_lazy('content:channel_list')
    template_name = "channel/create_channel.html"

    def get_form_kwargs(self):
        """
        Passes the request object to the form class
        """
        kwargs = super(UpdateChannel, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        f = form.save()
        f.save()
        update_space_journey(self.request.user, f, f.is_community_required)

        # if f.is_community_required:
        #     try:
        #         print(f)
        #         journey_space = SpaceJourney.objects.get(journey=f)
        #     except SpaceJourney.DoesNotExist:
        #         # create_journey_private_space(f, f.title)
        #         create_journey_space(f, self.request.user)
        return super(UpdateChannel, self).form_valid(form)

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:setup')
        else:
            return reverse('content:channel_list')


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class UpdateSubChannel(UpdateView):
    model = Channel
    form_class = SubChannelCreationFrom
    success_url = reverse_lazy('content:sub_channel_list')
    template_name = "channel/create_channel.html"


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class ChannelList(ListView):
    model = Channel
    context_object_name = "channels"
    template_name = "channel/channel_list.html"

    def get_queryset(self):
        return Channel.objects.filter(parent_id=None, is_delete=False)


@method_decorator(login_required, name='dispatch')
class MentoringJourneyList(ListView):
    model = Channel
    context_object_name = "channels"
    template_name = "channel/channel_list.html"

    def get_queryset(self):
        return Channel.objects.filter(channel_type="MentoringJourney",
                                      parent_id=None,
                                      is_delete=False)
    
@method_decorator(login_required, name='dispatch')
class SelfPacedJourneyList(ListView):
    model = Channel
    context_object_name = "channels"
    template_name = "channel/channel_list.html"

    def get_queryset(self):
        return Channel.objects.filter(channel_type="SelfPaced",
                                      parent_id=None,
                                      is_delete=False)


@method_decorator(login_required, name='dispatch')
class SetupJourneyContent(View):
    template_name = "channel/setup_content.html"

    def get(self, request, journey_id):
        content = Content.objects.filter(status="Live", is_delete=False)
        content_ids = [str(data.id) for data in content]
        survey = Survey.objects.filter(is_active=True, is_delete=False)
        survey_ids = [str(data.id) for data in survey]
        test_series = TestSeries.objects.filter(is_active=True, is_delete=False)
        test_series_ids = [str(data.id) for data in test_series]
        journals_templates = WeeklyjournalsTemplate.objects.filter(
            is_active=True)
        journals_templates_ids = [str(data.id) for data in journals_templates]
        journey = Channel.objects.get(pk=journey_id)
        all_value = content_ids + survey_ids + test_series_ids + journals_templates_ids
        mentoring_journay_data = MentoringJourney.objects.filter(Q(value__in=all_value),
            journey=journey, is_delete=False).order_by('display_order')
        context = {
            "content": content,
            "survey": survey,
            "test_series": test_series,
            "journals_templates": journals_templates,
            "journey_id": journey_id,
            "mentoring_journay_data": mentoring_journay_data,
            "journey": journey
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class FilterSetupJourneyContent(View):

    def post(self, request):
        journey_id = request.POST['journey_id']
        title = request.POST['title']
        content = Content.objects.filter(title__contains=title,
                                         is_delete=False)
        survey = Survey.objects.filter(name__contains=title)
        test_series = TestSeries.objects.filter(name__contains=title)
        journals_templates = WeeklyjournalsTemplate.objects.filter(
            is_active=True, title__contains=title)
        journey = Channel.objects.get(pk=journey_id)
        mentoring_journay_data = MentoringJourney.objects.filter(
            journey=journey, is_delete=False).order_by('display_order')
        context = {
            "content": content,
            "survey": survey,
            "test_series": test_series,
            "journals_templates": journals_templates,
            "journey_id": journey_id,
            "mentoring_journay_data": mentoring_journay_data
        }
        return render(request, "channel/setup_content.html", context)


@method_decorator(login_required, name='dispatch')
class DeleteJourneyContent(View):

    def post(self, request):
        id = request.POST['id']
        print(id)
        try:
            mentoring_journey = MentoringJourney.objects.get(pk=id)
        except MentoringJourney.DoesNotExist:
            return HttpResponse("Invalid Data")

        if mentoring_journey.meta_key == "quest":
            content_id = mentoring_journey.value
            print(content_id)
            content = Content.objects.get(pk=content_id)
            delete_content = ChannelGroupContent.objects.filter(
                channel_group=mentoring_journey.journey_group,
                content=content).update(is_delete=True)
            if delete_content:
                mentoring_journey.is_delete = True
                mentoring_journey.save()
                return HttpResponse("Delete Successfully")
        else:
            mentoring_journey.is_delete = True
            mentoring_journey.save()
        return HttpResponse("Delete Successfully")


@method_decorator(login_required, name='dispatch')
class UpdatesetupJournetData(View):

    def post(self, request):
        journey = Channel.objects.get(pk=request.POST['journey_id'])
        journey_gorup = ChannelGroup.objects.filter(channel=journey,
                                                    is_delete=False).first()
        type = request.POST['type']
        name = request.POST['title']
        id = request.POST['id']
        mentoring_journey = MentoringJourney.objects.filter(journey=journey,
                                                            is_delete=False)
        if type == "quest":
            content = Content.objects.get(pk=request.POST['id'])
            channel_group_content = ChannelGroupContent.objects.filter(
                channel_group=journey_gorup, is_delete=False)
            check_content = channel_group_content.filter(content=content)
            if check_content.count() == 0:
                order = channel_group_content.count()
                ChannelGroupContent.objects.create(channel_group=journey_gorup,
                                                   display_order=order + 1,
                                                   content=content,
                                                   status="Live")

            systemKey = "Content"
        elif type == "survey":
            systemKey = "Survey"

        elif type == "assessment":
            systemKey = "TestSeries"
        elif type == "journals":
            journel_count = mentoring_journey.filter(
                meta_key=request.POST['type']).count()
            systemKey = "LearningJournal"
            weekely_template = WeeklyjournalsTemplate.objects.get(pk=id)
            name = "Week {0} Journal".format(journel_count + 1)
            learning_journal = WeeklyLearningJournals.objects.create(
                name=name,
                learning_journal=weekely_template.learning_journal,
                journey_id=journey.pk)
            id = learning_journal.pk

        else:
            systemKey = ""

        total_row = mentoring_journey.count()
        check = mentoring_journey.filter(journey_group=journey_gorup,
                                         meta_key=request.POST['type'],
                                         value=id,
                                         name=name,
                                         is_delete=False)
        if check.count() == 0:

            create_mentoring = MentoringJourney.objects.create(
                systemKey=systemKey,
                journey=journey,
                journey_group=journey_gorup,
                meta_key=request.POST['type'],
                value=id,
                name=name,
                created_by=request.user.pk,
                display_order=total_row + 1)

            journey_users = getJourneyUsers(journey)

            if systemKey == 'TestSeries':
                for user in journey_users:
                    description = f"""Hi {user.first_name} {user.last_name}!
                    There is a new assessment to be filled out for {journey.title} """

                    context = {
                        "screen": "Journey",
                    }
                    send_push_notification(user, 'New Assessment Added',
                                           description, context)

            if systemKey == 'Survey':
                for user in journey_users:
                    description = f"""Hi {user.first_name} {user.last_name}!
                    There is a new survey to be filled out for {journey.title}.
                    Go fill out the survey now! """

                    context = {
                        "screen": "Journey",
                    }
                    send_push_notification(user, 'New Survey Added',
                                           description, context)

            if systemKey == 'Content':
                for user in journey_users:
                    description = f"""Hi {user.first_name} {user.last_name}!
                    A new Microskill Learning is live in your journey!
                    Go check out {content.title} now!"""

                    context = {
                        "screen": "Journey",
                    }
                    send_push_notification(user, 'New Content Added',
                                           description, context)

            return HttpResponse("Success")
        else:
            return HttpResponse("Already Exixt")


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class SubChannelList(ListView):
    model = Channel
    context_object_name = "channels"
    template_name = "channel/sub_channel_list.html"

    def get_queryset(self):
        return Channel.objects.filter(~Q(parent_id=None),
                                      is_delete=False,
                                      is_active=True)


@method_decorator(login_required, name='dispatch')
class CourseContent(TemplateView):
    content_type = 'text/html'
    template_name = "channel/course_content.html"


@method_decorator(login_required, name='dispatch')
class CreateContent(CreateView):
    model = Content
    form_class = ContentCreationFrom
    # success_url = reverse_lazy('program_manager:content')
    template_name = "channel/create_content.html"

    def form_valid(self, form):
        count = Content.objects.all().count()

        f = form.save(commit=False)
        f.user = self.request.user
        f.display_order = count + 1
        f.save()

        return super(CreateContent, self).form_valid(form)

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:content')
        else:
            return reverse('content:edit_content',
                           kwargs={'pk': self.object.pk})


@method_decorator(login_required, name='dispatch')
class EditContentData(View):
    template_name = "channel/content_create.html"

    def get(self, request, **kwargs):
        try:
            content = Content.objects.get(pk=self.kwargs['pk'])
            data = ContentData.objects.filter(
                content=self.kwargs['pk']).order_by("display_order")
            channel = Channel.objects.filter(parent_id=None,
                                             is_delete=False,
                                             is_active=True,
                                             closure_date__gt=datetime.now())
            if request.session['user_type'] == 'ProgramManager':
                channel = channel.filter(
                    company__id=request.session['company_id'])
            return render(request, self.template_name, {
                "data": data,
                "channel": channel,
                "content": content
            })
        except Content.DoesNotExist:
            raise response.Http404


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class ChannelGroupView(ListView):
    model = ChannelGroup
    context_object_name = "channel_group"
    template_name = "channel/channel_group.html"

    def get_queryset(self):
        try:
            return ChannelGroup.objects.filter(
                channel=self.kwargs['channel_id'], is_delete=False)
        except:
            return ChannelGroup.objects.filter(is_delete=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CreateChannelGroup(CreateView):
    model = ChannelGroup
    form_class = CreateChannelGroupFrom
    success_url = reverse_lazy('content:channel_group')
    template_name = "channel/create_content.html"


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class EditChannelGroup(UpdateView):
    model = ChannelGroup
    form_class = CreateChannelGroupFrom
    success_url = reverse_lazy('content:channel_group')
    template_name = "channel/create_content.html"


@method_decorator(login_required, name='dispatch')
class AdminReadContent(View):
    template_name = "channel/new_read_content.html"

    def get(self, request, **kwargs):

        content = Content.objects.get(pk=self.kwargs['pk'])
        result = []
        data = ContentData.objects.filter(
            content=self.kwargs['pk']).order_by("display_order")

        for data in data:
            content_data_option = ContentDataOptions.objects.filter(
                content_data=data)
            response = []
            print("datatype", data.type, data.title)
            if data.type == "Poll":
                for cd_option in content_data_option:
                    check_user = ContetnOptionSubmit.objects.filter(
                        user=self.request.user, content_data=data)
                    if check_user.count() > 0:
                        get_user_result = ContetnOptionSubmit.objects.filter(
                            content_data=data)
                        total_answer = get_user_result.count()
                        count = get_user_result.filter(
                            option=cd_option.option).count()

                        avg_count = 0 if count == 0 else (count /
                                                          total_answer) * 100

                        response.append({
                            "id": cd_option.id,
                            "option": cd_option.option,
                            "count": avg_count,
                            "my_response": True
                        })
            elif data.type == "Quiz":
                get_user_result = ContetnOptionSubmit.objects.filter(
                    content_data=data, user=self.request.user)
                if get_user_result.count() > 0:
                    get_user_result = get_user_result.first()
                    content_data_options = ContentDataOptions.objects.filter(
                        content_data=data, correct_answer=True)
                    for cd_option in content_data_options:
                        response = {
                            "option":
                            cd_option.option,
                            "my_answer":
                            get_user_result.option,
                            "is_true":
                            True if cd_option.option == get_user_result.option
                            else False
                        }
            result.append({
                "id": data.id,
                "content": data.content,
                "title": data.title,
                "type": data.type,
                "data": data.data,
                "file": data.file,
                "video": data.video,
                "url": data.url,
                "display_order": data.display_order,
                "content_data_option": content_data_option,
                "poll_response": response,
                "activity_type": data.activity_type,
            })
        # channel = Channel.objects.filter(parent_id=None)

        return render(request, self.template_name, {
            "data": result,
            "content": content
        })


@method_decorator(login_required, name='dispatch')
class ReadContent(View):
    template_name = "channel/user_read_content.html"

    def get(self, request, **kwargs):

        content = Content.objects.get(pk=self.kwargs['pk'])
        # channel = Channel.objects.get(pk=self.kwargs['Channel'])

        channel_group = ChannelGroup.objects.get(pk=self.kwargs['group'])
        channel = Channel.objects.get(pk=channel_group.channel.pk)
        parent_check = is_parent_channel(channel_group.channel.pk)

        learning_journals = LearningJournals.objects.filter(
            journey_id=parent_check['channel_id'],
            microskill_id=self.kwargs['pk'],
            email=request.user.email).first()
        print(learning_journals)
        if channel.channel_type == "SkillDevelopment":
            if channel_group.post_assessment is None:
                go_next = "None"
            else:
                go_next = reverse_lazy('test_series:test_series_form',
                                       kwargs={
                                           'pk':
                                           channel_group.post_assessment.pk,
                                           'channel': channel.pk,
                                       })
        else:

            try:
                display_contents = ChannelGroupContent.objects.get(
                    status="Live",
                    channel_group=channel_group,
                    content=content,
                    is_delete=False)
                order = display_contents.display_order + 1
                channel_content = ChannelGroupContent.objects.get(
                    status="Live",
                    channel_group=channel_group,
                    display_order=order)

                go_next = reverse_lazy('content:read_content',
                                       kwargs={
                                           'pk': channel_content.content.pk,
                                           'group': channel_group.pk
                                       })
            except:
                go_next = "None"

        if channel.channel_type == "SkillDevelopment":
            go_previous = None
        else:

            try:
                display_contents = ChannelGroupContent.objects.get(
                    status="Live",
                    channel_group=channel_group,
                    content=content,
                    is_delete=False)
                order = display_contents.display_order - 1
                channel_content = ChannelGroupContent.objects.get(
                    status="Live",
                    channel_group=channel_group,
                    display_order=order)

                go_previous = reverse_lazy('content:read_content',
                                           kwargs={
                                               'pk':
                                               channel_content.content.pk,
                                               'group': channel_group.pk
                                           })
            except:
                go_previous = None
        result = []
        content_data = ContentData.objects.filter(
            content=self.kwargs['pk']).order_by("display_order")
        data = Paginator(content_data, 1)

        page_number = request.GET.get('page')

        try:
            page_obj = data.get_page(
                page_number)  # returns the desired page object
        except PageNotAnInteger:
            # if page_number is not an integer then assign the first page
            page_obj = data.page(1)
        except EmptyPage:
            page_obj = data.page(data.num_pages)
        user_course = UserCourseStart.objects.filter(
            user=request.user,
            content=self.kwargs['pk'],
            channel=channel,
            channel_group=channel_group)

        if user_course.count() == 0:
            UserCourseStart.objects.create(user=request.user,
                                           content=content,
                                           channel=channel,
                                           channel_group=channel_group,
                                           status="InProgress")

        data = page_obj[0]
        if data.display_order == 0:
            previous_order = data.display_order
        else:
            previous_order = data.display_order - 1

        try:
            UserReadContentData.objects.create(channel=channel,
                                               content=content,
                                               content_data=data,
                                               user=request.user)
        except:
            pass

        if previous_order != 0:
            get_previous_content = ContentData.objects.get(
                content=content, display_order=previous_order)
            UserReadContentData.objects.filter(
                user=request.user,
                channel=channel,
                content=content,
                content_data=get_previous_content).update(status="Complete")

        content_data_option = ContentDataOptions.objects.filter(
            content_data=data)
        response = []
        if data.type == "Poll":
            for cd_option in content_data_option:
                check_user = ContetnOptionSubmit.objects.filter(
                    user=self.request.user, content_data=data)
                if check_user.count() > 0:
                    get_user_result = ContetnOptionSubmit.objects.filter(
                        content_data=data)
                    total_answer = get_user_result.count()
                    count = get_user_result.filter(
                        option=cd_option.option).count()

                    avg_count = 0 if count == 0 else (count /
                                                      total_answer) * 100
                    response.append({
                        "id": cd_option.id,
                        "option": cd_option.option,
                        "count": avg_count,
                        "my_response": True
                    })
        elif data.type == "Quiz":
            get_user_result = ContetnOptionSubmit.objects.filter(
                content_data=data, user=self.request.user)
            if get_user_result.count() > 0:
                get_user_result = get_user_result.first()
                content_data_options = ContentDataOptions.objects.filter(
                    content_data=data, correct_answer=True)
                for cd_option in content_data_options:
                    response = {
                        "option": cd_option.option,
                        "my_answer": get_user_result.option,
                        "is_true": cd_option.option == get_user_result.option
                    }

        user_activity_data = UserActivityData.objects.filter(
            journey=channel,
            content_data=data,
            submitted_by=request.user,
            is_draft=False,
            is_active=True,
            is_delete=False)
        result = {
            "id":
            data.id,
            "content":
            data.content,
            "title":
            data.title,
            "type":
            data.type,
            "link_data":
            data.link_data,
            "data":
            data.data,
            "file":
            data.file,
            "video":
            data.video,
            "url":
            data.url,
            "display_order":
            data.display_order,
            "content_data_option":
            content_data_option,
            "poll_response":
            response,
            "learning_journals":
            learning_journals,
            "activity_type":
            data.activity_type,
            "is_submitted":
            True if user_activity_data.exists() else False,
            "activity_file":
            user_activity_data.first().upload_file
            if user_activity_data.exists() else ""
        }
        # channel = Channel.objects.filter(parent_id=None)

        response = render(
            request, self.template_name, {
                "data": result,
                "channel": channel,
                "group": channel_group,
                "content": content,
                "go_next": go_next,
                "page_obj": page_obj,
                "page_no": page_number,
                "go_previous": go_previous,
                "content_data": content_data,
                "mode": "Learn",
                "parent_check": parent_check,
                "learning_journals": learning_journals
            })
        response.set_cookie(
            'last_course_url',
            reverse("content:read_content",
                    kwargs={
                        'pk': content.pk,
                        'group': channel_group.pk
                    }))
        return response


@method_decorator(login_required, name='dispatch')
class AddField(View):

    def post(self, request):
        type = request.POST['type']

        main_content = Content.objects.get(pk=request.POST['content'])
        print(change_course_status_in_group(main_content),
              "change_course_status_in_group(main_content)")

        display_order = ContentData.objects.filter(
            content=main_content).count()
        content_data = ContentData.objects.create(type=type,
                                                  content=main_content,
                                                  display_order=display_order +
                                                  1)

        main_content.status = "Pending"
        main_content.save()
        if type == "Text":
            time = 3
        elif type == "Quiz":
            time = 2
        elif type == "Poll":
            time = 1
        elif type == "YtVideo":
            time = 5
        elif type == "Activity":
            time = 10
        content_data.time = time
        if type == "Quiz" or type == "Poll":
            ContentDataOptions.objects.create(content_data=content_data)
        elif type == "Text":
            content_data.data = "Start Writing"
        content_data.save()
        return HttpResponse('Success')


@method_decorator(login_required, name='dispatch')
class UpdateOption(View):

    def post(self, request):
        id = request.POST['id']
        value = request.POST['value']
        print(id)
        if id == "0":
            content_data = ContentData.objects.get(
                id=request.POST['content_id'])
            contentoption = ContentDataOptions.objects.create(
                option=value, content_data=content_data)

        else:
            contentoption = ContentDataOptions.objects.get(id=id)
            contentoption.option = value
            contentoption.save()

        response = {"id": contentoption.pk}
        return JsonResponse(response)


@method_decorator(login_required, name='dispatch')
class EditChannel(View):

    def post(self, request):
        channel = request.POST['channel']

        # channel = Channel.objects.get(id=channel)

        sub_channel = request.POST['sub_channel']

        if sub_channel != "":
            channel = sub_channel

        channel = Channel.objects.get(id=channel)
        content_id = request.POST['content_id']
        content = Content.objects.get(pk=content_id)
        # ContentData.objects.filter(content=content, title="").delete()

        if ContentData.objects.filter(content=content, title="").delete():
            i = 1
            for content_list in ContentData.objects.filter(
                    content=content).order_by('display_order'):
                print(content.display_order)
                content_list.display_order = i
                content_list.save()
                i = i + 1
        group = request.POST.getlist('group[]', False)

        for group in group:

            channel_group = ChannelGroup.objects.get(pk=group)
            group_content = ChannelGroupContent.objects.filter(
                channel_group=channel_group, content=content, is_delete=False)

            if group_content.count() == 0:
                order = ChannelGroupContent.objects.filter(
                    channel_group=channel_group, is_delete=False).count()
                ChannelGroupContent.objects.create(channel_group=channel_group,
                                                   content=content,
                                                   display_order=order + 1)
                content_id = Content.objects.filter(pk=content_id).update(
                    Channel=channel, status="Pending")
                getcontent = Content.objects.filter(pk=content_id).update(
                    Channel=channel, status="Pending")
                order = ContentChannels.objects.filter(
                    content=content, Channel=channel).count()
                ContentChannels.objects.create(content=content,
                                               Channel=channel,
                                               display_order=order + 1)
                message = "Content Alloted"
            else:
                message = "Content Already Alloted on this Journey"

        return HttpResponse(message)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class CourseList(ListView):

    def get(self, request, *args, **kwargs):
        channel_content = ChannelGroupContent.objects.filter(
            channel_group=self.kwargs['channel_group'],
            is_delete=False).values('content_id', 'id')
        content_id_list = [
            content['content_id'] for content in channel_content
        ]
        content_list = Content.objects.filter(pk__in=content_id_list,
                                              is_delete=False)
        context = {"content": content_list, "channel_content": channel_content}
        return render(request, "channel/user_content.html", context)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class JourneyContentList(ListView):
    model = Content
    context_object_name = "content"
    template_name = "channel/journey_content_list.html"

    def get_queryset(self, **kwargs):
        journey = Channel.objects.get(id=self.kwargs['channel_id'])
        if journey.channel_type == "SkillDevelopment":
            skills = Channel.objects.filter(parent_id=journey)
            channel_group = ChannelGroup.objects.filter(channel__in=skills,
                                                        is_delete=False)
        else:
            channel_group = ChannelGroup.objects.filter(channel=journey,
                                                        is_delete=False)
        channel_content = ChannelGroupContent.objects.filter(
            channel_group__in=channel_group, is_delete=False).values('content')
        return Content.objects.filter(pk__in=channel_content, is_delete=False)


@method_decorator(login_required, name='dispatch')
class CopyContent(View):

    def post(self, request, **kwargs):
        obj = Content.objects.get(pk=request.POST['id'])
        obj2 = ContentData.objects.filter(content=obj)
        obj.pk = None
        obj.save()
        for obj2 in obj2:
            obj3 = ContentDataOptions.objects.filter(content_data=obj2)
            obj2.pk = None
            obj2.content = obj
            obj2.save()
            for obj3 in obj3:
                obj3.pk = None
                obj3.content_data = obj2
                obj3.save()

        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class SelectChannelGroup(View):

    def post(self, request):
        channel = request.POST['channel']

        channel_group = ChannelGroup.objects.filter(channel=channel,
                                                    is_delete=False)
        channel = Channel.objects.get(pk=channel)
        data = [{
            'title': channel_group.title,
            'id': channel_group.pk
        } for channel_group in channel_group]

        response = {"data": data, "is_test_required": channel.is_test_required}

        return JsonResponse(response, safe=False)


@method_decorator(login_required, name='dispatch')
class UpdateChannelStatus(View):

    def post(self, request):
        status = request.POST['status']
        content_id = request.POST['content_id']
        Content.objects.filter(pk=content_id).update(status=status)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
@method_decorator(allowed_users(allowed_roles=["Admin", "ProgramManager"]),
                  name="dispatch")
class UserContent(ListView):
    model = Content
    context_object_name = "content"
    template_name = "channel/my_content.html"

    def get_queryset(self):
        return Content.objects.filter(user=self.request.user, is_delete=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class AllAdminContent(ListView):
    model = Content
    context_object_name = "content"
    template_name = "channel/my_content.html"

    def get_queryset(self):
        return Content.objects.filter(is_delete=False)


@method_decorator(login_required, name='dispatch')
class PendingContent(View):
    template_name = "channel/course_approval.html"

    def get(self, request):
        content = ChannelGroupContent.objects.filter(
            status="Pending", is_delete=False).order_by('-created_at')
        if self.request.session['user_type'] == "ProgramManager":
            company = self.request.user.company.all()
            print(company, "Line 715")
            all_journeys = Channel.objects.filter(company__in=company)
            channel_group = ChannelGroup.objects.filter(
                channel__in=all_journeys, is_delete=False)
            content = ChannelGroupContent.objects.filter(
                status="Pending",
                channel_group__in=channel_group,
                is_delete=False).order_by('-created_at')

        return render(request, self.template_name, {"content": content})


@method_decorator(login_required, name='dispatch')
class ChannelContent(View):
    '''
        Render Channel Content.
    '''
    template_name = "channel/course_content.html"

    def get(self, request, **kwargs):
        channel = Channel.objects.filter(pk=self.kwargs['Channel'],
                                         is_delete=False,
                                         is_active=True)
        channel = channel.first()
        parent_check = is_parent_channel(channel.pk)

        if channel.channel_type == "SkillDevelopment":
            channel = Channel.objects.get(pk=self.kwargs['Channel'])

        channel_group = ChannelGroup.objects.filter(channel=channel,
                                                    is_delete=False)
        if parent_check['is_community_required']:
            if JourneySpace.objects.filter(
                    journey=parent_check['channel']).count() > 0:
                AddMembertoSpace(request.user, parent_check['channel'])

        if channel.channel_type == "SurveyCourse":
            survey_attempt = SurveyAttempt.objects.filter(
                user=request.user, survey=channel.survey)
            if len(survey_attempt) > 0:
                survey_attempt = survey_attempt.last()
                channel_group = channel_group.filter(
                    channel_for=survey_attempt.user_skill)
                channel = []
            else:
                channel_group = []
        elif channel.channel_type == "SkillDevelopment":
            if channel.is_test_required:
                assessment_attempt = TestAttempt.objects.filter(
                    user=request.user,
                    channel=channel,
                    test=channel.test_series)
                if len(assessment_attempt) > 0:
                    assessment_attempt = assessment_attempt.first()

                    try:
                        assessment_attempt_marks = math.ceil(
                            (assessment_attempt.total_marks /
                             assessment_attempt.test_marks) * 100)
                    except:
                        assessment_attempt_marks = assessment_attempt.total_marks

                    channel_group = channel_group.filter(
                        start_mark__lte=assessment_attempt_marks,
                        end_marks__gte=assessment_attempt_marks)
                    marks = assessment_attempt.total_marks
                    if channel.parent_id is not None:
                        channel = []
                else:
                    channel_group = []
            else:
                assessment_attempt = TestAttempt.objects.filter(
                    user=request.user,
                    channel=channel,
                    test=channel.test_series)

                level = "Level 1"
                if len(assessment_attempt) > 0:
                    assessment_attempt = assessment_attempt.first()
                    level = assessment_attempt.user_skill

                level = SurveyLabel.objects.get(label=level)

                channel_group = channel_group.filter(channel_for=level)
        print("demo")
        return render(
            request, self.template_name, {
                "channel": channel,
                "channel_group": channel_group,
                "parent_check": parent_check
            })


@method_decorator(login_required, name='dispatch')
class ChannelContent_V2(View):
    '''
        Render Channel Content.
    '''
    template_name = "channel/course_content_v2.html"

    def get(self, request, **kwargs):
        channel = Channel.objects.filter(pk=self.kwargs['Channel'],
                                         is_delete=False,
                                         is_active=True)
        # print("channel",channel)
        channel = channel.first()
        try:
            space_journey = SpaceJourney.objects.get(journey=channel)
            space_id = space_journey.space.id
        except:
            space_id = ""
            
        print("channel", channel)
        parent_check = is_parent_channel(channel.pk)
        print("channel.channel_type", channel.channel_type)
        if channel.channel_type == "SkillDevelopment":
            if channel.channel_type == "SkillDevelopment":
                channel = Channel.objects.get(pk=self.kwargs['Channel'])

            channel_group = ChannelGroup.objects.filter(channel=channel,
                                                        is_delete=False)
            # try:
            #     user_channel = UserChannel.objects.get(Channel=channel, user=request.user)
            # except:
            #     user_channel = UserChannel.objects.get(Channel=channel.parent_id, user=request.user)
            # if user_channel.is_removed:
            #     return redirect('user:user-dashboard')

            if parent_check['is_community_required']:
                if JourneySpace.objects.filter(
                        journey=parent_check['channel']).count() > 0:
                    AddMembertoSpace(request.user, parent_check['channel'])

            if channel.channel_type == "SurveyCourse":
                user_channel = UserChannel.objects.get(
                    Channel_id=self.kwargs['Channel'], user=request.user)
                if user_channel.is_removed:
                    return redirect('user:user-dashboard')
                survey_attempt = SurveyAttempt.objects.filter(
                    user=request.user, survey=channel.survey)
                if len(survey_attempt) > 0:
                    survey_attempt = survey_attempt.last()
                    channel_group = channel_group.filter(
                        channel_for=survey_attempt.user_skill)
                    channel = []
                else:
                    channel_group = []
            elif channel.channel_type == "SkillDevelopment":
                if channel.is_test_required:
                    # print(channel.test_series)
                    assessment_attempt = TestAttempt.objects.filter(
                        user=request.user,
                        channel=channel,
                        test=channel.test_series)
                    if len(assessment_attempt) > 0:
                        assessment_attempt = assessment_attempt.first()

                        try:
                            assessment_attempt_marks = math.ceil(
                                (assessment_attempt.total_marks /
                                 assessment_attempt.test_marks) * 100)

                        except:
                            assessment_attempt_marks = assessment_attempt.total_marks

                        channel_group = channel_group.filter(
                            start_mark__lte=assessment_attempt_marks,
                            end_marks__gte=assessment_attempt_marks)
                        marks = assessment_attempt.total_marks
                        if channel.parent_id is not None:
                            channel = []
                    else:
                        channel_group = []
                else:
                    assessment_attempt = TestAttempt.objects.filter(
                        user=request.user,
                        channel=channel,
                        test=channel.test_series)

                    level = "Level 1"
                    if len(assessment_attempt) > 0:
                        assessment_attempt = assessment_attempt.first()
                        level = assessment_attempt.user_skill

                    level = SurveyLabel.objects.get(label=level)

                    channel_group = channel_group.filter(channel_for=level)

            return render(
                request, "channel/course_content.html", {
                    "channel": channel,
                    "channel_group": channel_group,
                    "parent_check": parent_check
                })
        else:
            # print("request.user.userType.all():",request.user.userType.all())
            if "Learner" in request.user.userType.all():

                if Journey(parent_check['channel'], request.user) is False:
                    return redirect(reverse('content:browse_channel'))

            display_content = []

            # channel = parent_check['channel']
            channel_group = ChannelGroup.objects.filter(channel=channel,
                                                        is_delete=False)

            if channel.channel_type == "SkillDevelopment":
                channel = Channel.objects.get(pk=self.kwargs['Channel'])
            if parent_check['is_community_required']:
                if JourneySpace.objects.filter(
                        journey=parent_check['channel']).count() > 0:
                    AddMembertoSpace(request.user, parent_check['channel'])

            if parent_check['channel'].channel_type == "onlyCommunity":

                display_content = get_display_content(channel, channel_group,
                                                      request.user)
                # print(display_content)
            elif parent_check['channel'].channel_type == "MentoringJourney" or parent_check['channel'].channel_type == "SelfPaced":

                mentoring_journey = MentoringJourney.objects.filter(
                    journey=parent_check['channel'],
                    is_delete=False).order_by('display_order')
                for mentoring_journey in mentoring_journey:

                    type = mentoring_journey.meta_key
                    # print("type",type)
                    read_status = ""
                    content_image = ""
                    output_key = ""
                    if type == "quest":
                        content = Content.objects.filter(status="Live",
                            pk=mentoring_journey.value).first()
                        # print(content)
                        if content:
                            content_image = content.image
                            try:
                                user_read_status = UserCourseStart.objects.get(
                                    user=request.user,
                                    content=content,
                                    channel_group=mentoring_journey.journey_group,
                                    channel=channel.pk)
                                # print(user_read_status)
                                read_status = user_read_status.status
                            except UserCourseStart.DoesNotExist:
                                read_status = ""
                    elif type == "assessment":
                        test_series = TestSeries.objects.get(
                            pk=mentoring_journey.value)
                        test_attempt = TestAttempt.objects.filter(
                            test=test_series,
                            user=request.user,
                            channel=mentoring_journey.journey)
                        if test_attempt.count() > 0:
                            read_status = "Complete"
                    elif type == "survey":
                        survey = Survey.objects.get(pk=mentoring_journey.value)
                        survey_attempt = SurveyAttempt.objects.filter(
                            survey=survey, user=request.user)
                        if survey_attempt.count() > 0:
                            read_status = "Complete"

                    elif type == "journals":
                        weekely_journals = WeeklyLearningJournals.objects.get(
                            pk=mentoring_journey.value, journey_id=channel.pk)
                        learning_journals = LearningJournals.objects.filter(
                            weekely_journal_id=weekely_journals.pk,
                            journey_id=channel.pk,
                            email=self.request.user.email)
                        if learning_journals.count() > 0:
                            if learning_journals.first().is_draft:
                                read_status = "InProgress"
                            else:
                                read_status = "Complete"
                        data = weekely_journals
                        output_key = learning_journals.first()
                    else:
                        content_image = ""

                    # print("read_status", read_status)

                    display_content.append({
                        "type":type,
                        "title":mentoring_journey.name,
                        "image":content_image,
                        "id":mentoring_journey.value,
                        "channel_group":mentoring_journey.journey_group.pk,
                        "journey_id":mentoring_journey.journey.pk,
                        "read_status":read_status,
                        "read_data":output_key,
                        "is_checked":mentoring_journey.is_checked
                    })
                print("display_content", display_content)

            elif parent_check['channel'].channel_type == "SkillDevelopment":
                # try:
                #     user_channel = UserChannel.objects.get(Channel=channel, user=request.user)
                # except:
                #     user_channel = UserChannel.objects.get(Channel=channel.parent_id, user=request.user)
                # if user_channel.is_removed:
                #     return redirect('user:user-dashboard')

                if channel.parent_id is None:
                    skill = Channel.objects.filter(parent_id=channel)
                    for skill in skill:
                        display_content.append({
                            "type": "skills",
                            "title": skill.title,
                            "image": skill.image,
                            "id": "",
                            "channel_group": "",
                            "journey_id": skill.id,
                            "read_status": ""
                        })

                else:
                    if parent_check['channel'].is_test_required:
                        test_series = TestSeries.objects.filter(
                            pk=channel.test_series.pk)
                        for test_series in test_series:
                            display_content.append({
                                "type":
                                "assessment",
                                "title":
                                test_series.name,
                                "image":
                                "",
                                "id":
                                test_series.pk,
                                "channel_group":
                                "",
                                "journey_id":
                                parent_check['channel'].pk,
                                "read_status":
                                ""
                            })

                        assessment_attempt = TestAttempt.objects.filter(
                            user=request.user,
                            channel=channel,
                            test=channel.test_series)
                        if len(assessment_attempt) > 0:
                            # print(assessment_attempt)
                            assessment_attempt = assessment_attempt.first()

                            try:
                                assessment_attempt_marks = math.ceil(
                                    (assessment_attempt.total_marks /
                                     assessment_attempt.test_marks) * 100)

                            except:
                                assessment_attempt_marks = assessment_attempt.total_marks

                            channel_group = channel_group.filter(
                                start_mark__lte=assessment_attempt_marks,
                                end_marks__gte=assessment_attempt_marks)
                            marks = assessment_attempt.total_marks
                            display_content = get_display_content(
                                channel, channel_group, request.user)
                            if channel.parent_id is not None:
                                channel = []
                        else:

                            channel_group = []

                        # print("display_content", display_content)

                    else:
                        assessment_attempt = TestAttempt.objects.filter(
                            user=request.user,
                            channel=channel,
                            test=channel.test_series)

                        level = "Level 1"
                        if len(assessment_attempt) > 0:
                            assessment_attempt = assessment_attempt.first()
                            level = assessment_attempt.user_skill

                        level = SurveyLabel.objects.get(label=level)

                        channel_group = channel_group.filter(channel_for=level)
                        # print(channel_group)
                        display_content = get_display_content(
                            channel, channel_group, request.user)
            # channel.channel_group_content.all()
                        # print("display_content", display_content)
            return render(request, self.template_name,
                          {"display_content": display_content, "parent_check": parent_check, "channel": channel, "space_id": space_id, "community_url": COMMUNITY_URL})


@method_decorator(login_required, name='dispatch')
class DeleteContentData(View):

    def get(self, request, **kwargs):
        content_data_id = self.kwargs['pk']
        content = Content.objects.get(pk=self.kwargs['content'])
        content_data = ContentData.objects.get(pk=content_data_id)
        if content_data.delete():
            i = 1
            for content in ContentData.objects.filter(
                    content=content).order_by('display_order'):
                print(content.display_order)
                content.display_order = i
                content.save()
                i = i + 1
        return redirect(
            reverse('content:edit_content',
                    kwargs={'pk': self.kwargs['content']}))


@method_decorator(login_required, name='dispatch')
class DeleteCourse(View):

    def post(self, request, **kwargs):
        course_id = self.request.POST['pk']

        Content.objects.filter(pk=course_id).update(is_delete=True,
                                                    status="Pending")
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class DeleteChannel(View):

    def post(self, request, **kwargs):
        channel_id = self.request.POST['pk']
        channel = Channel.objects.filter(id=channel_id)
        channel.update(is_active=False, is_delete=True)
        update_space_journey(user=self.request.user,
                             journey=channel.first(),
                             community_required=False)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class DeleteChannelGroup(View):

    def post(self, request, **kwargs):
        channel_group_id = self.request.POST['pk']
        ChannelGroup.objects.filter(id=channel_group_id).update(is_delete=True)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class UpdateOrder(View):

    def post(self, request):
        order_string = request.POST['order']
        order = order_string.split(',')
        # main_content = Content.objects.get(pk=request.POST['content'])
        for i in range(len(order)):
            display_order = i + 1

            ContentData.objects.filter(pk=order[i]).update(
                display_order=display_order)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class UpdateContentOrder(View):

    def post(self, request):
        order_string = request.POST['order']
        print("order", order_string)
        order = order_string.split(',')
        checked_string = request.POST['checked']
        print("checked", checked_string)
        checked = checked_string.split(',')
        for i in range(len(order)):
            display_order = i + 1
            MentoringJourney.objects.filter(pk=order[i]).update(
                display_order=display_order,
                is_checked=update_boolean(checked[i]))
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class UpdateContentChecked(View):

    def post(self, request):
        checked = request.POST['checked']
        id = request.POST['id']

        MentoringJourney.objects.filter(pk=id).update(
            is_checked=update_boolean(checked))
        return HttpResponse("Success")


@login_required
def upload_video(request):
    type = request.POST['type']
    main_content = Content.objects.get(pk=request.POST['content'])
    change_course_status_in_group(main_content)
    display_order = ContentData.objects.filter(content=main_content).count()
    content_create = ContentData.objects.create(type=type,
                                                content=main_content,
                                                display_order=display_order +
                                                1)
    main_content.status = "Pending"
    main_content.save()
    if type == "Video":
        content_create.time = 5
        video = request.FILES['file']
        content_create.video = video
        content_create.title = "Video Card"
    elif type == "Image":
        content_create.time = 1
        image = request.FILES['file']
        content_create.file = image
        content_create.title = "Caption"
    elif type == "Pdf":
        content_create.time = 2
        image = request.FILES['file']
        content_create.file = image
        content_create.title = "Caption"
    content_create.save()
    return HttpResponse('Success')


@login_required
def upload_subtitle(request):
    print("Request", request.POST)
    video_id = request.POST['id']
    lang_type = request.POST['lang_type']
    subtitle_file = request.FILES['subtitle_file']
    print("Filename", subtitle_file.name)

    video_file = ContentData.objects.get(id=video_id)
    # print("Checking if the record exists")
    # if VideoSubtitles.objects.filter(lang_type=lang_type, video_id=video_id).exists:
    #     existing_record = VideoSubtitles.objects.get(lang_type=lang_type, video_id=video_id)
    #     existing_record.subtitle_file = subtitle_file
    #     existing_record.lang_type = lang_type
    #     existing_record.video_file = video_file
    #     existing_record.save()
    #     print("record updated")
    # else:
    subtitle_content = VideoSubtitles.objects.create(
        video_id=video_id,
        lang_type=lang_type,
        subtitle_file=subtitle_file,
        video_file=video_file)
    print("new record created")
    subtitle_content.save()
    return HttpResponse('Success')


@login_required
def update_subtitle(request):
    video_id = request.POST['id']
    lang_type = request.POST['lang_type']
    subtitle_file = request.FILES['subtitle_file']
    print("Filename", subtitle_file.name)
    video_file = ContentData.objects.get(id=video_id)
    subtitle_content = VideoSubtitles.objects.create(
        video_id=video_id,
        lang_type=lang_type,
        subtitle_file=subtitle_file,
        video_file=video_file)
    subtitle_content.save()
    return HttpResponse('Success')


def translate_files(video_id, file_text, lang_type, thread):
    video_file = ContentData.objects.get(id=video_id)

    translator = googletrans.Translator()

    print("Lang Type", lang_type)
    with open(f'static/subtitle_{thread}_{lang_type}_{video_id}.vtt',
              'w',
              encoding="utf-8") as f:
        f.write(translator.translate(file_text.decode(), dest=lang_type).text)
        print("Wrote the file", lang_type)

    with open(f'static/subtitle_{thread}_{lang_type}_{video_id}.vtt',
              'rb') as fi:
        subtitle_file = File(fi, name=f'{video_id}_{lang_type}.vtt')
        subtitle_content = VideoSubtitles.objects.create(
            video_id=video_id,
            lang_type=lang_type,
            subtitle_file=subtitle_file,
            video_file=video_file)
        subtitle_content.save()

    try:
        os.remove(f'static/subtitle_{thread}_{lang_type}_{video_id}.vtt')
        print("File deleted")
    except:
        print("File not deleted")
        pass

    print("File saved")


@login_required
def translate_subtitles(request):
    video_id = request.POST['id']
    subtitle_file = request.FILES['subtitle_file']
    file_text = subtitle_file.read()
    languages_list = [
        'en', 'fr', 'th', 'vi', 'zh-CN', 'zh-TW', 'id', 'tl', 'ms', 'mn', 'ja',
        'ko', 'nl', 'de', 'pl', 'pt', 'es'
    ]
    for i in range(len(languages_list)):
        Thread(target=translate_files,
               args=[video_id, file_text, languages_list[i], i],
               daemon=True).start()
    print("Execution completed")

    return HttpResponse('success')


@login_required
def update_data(request):
    id = request.POST['id']
    data = request.POST['data']
    key = request.POST['key']
    type = request.POST['type']
    if key == "data":
        if type == "Text":

            dataset = {
                key: data,
                "title": striphtml(data)[:15],
                "time": TextTime(data)
            }
        elif type == "YtVideo":
            dataset = {key: data, "time": LinkTime(data)}
        else:
            dataset = {key: data}
    else:

        dataset = {
            key: data,
        }
    content = ContentData.objects.filter(pk=id)
    change_course_status_in_group(content[0].content)
    content.update(**dataset)
    return HttpResponse('Success')


@login_required
def upload_activity_file(request):

    journey = Channel.objects.get(pk=request.POST['journey'])
    content_data = ContentData.objects.get(pk=request.POST['content_data'])
    if UserActivityData.objects.filter(journey=journey,
                                       content_data=content_data,
                                       submitted_by=request.user,
                                       is_draft=False,
                                       is_active=True,
                                       is_delete=False).exists():
        return HttpResponse('Activity File already exist!')
    else:
        UserActivityData.objects.create(
            journey=journey,
            content_data=content_data,
            submitted_by=request.user,
            is_draft=False,
            upload_file=request.FILES['activity_file'],
            reviewed_by=request.user)

    return HttpResponse('Success')


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class BrowseChannel(View):
    template_name = "channel/browse_channel.html"

    def get(self, request, pk=None):
        user = None
        if pk is None:
            if request.session.get('company_id'):
                channel = public_channel_list(request.user,
                                              request.session['company_id'])
            else:
                channel = public_channel_list(request.user)
        else:
            user = User.objects.get(id=pk)
            if request.session.get('company_id'):
                channel = public_channel_list(user,
                                              request.session['company_id'])
            else:
                channel = public_channel_list(user)
        print(channel)

        return render(request, self.template_name, {
            "channels": channel,
            "user": user
        })


@method_decorator(login_required, name='dispatch')
class JoinRequest(View):
    template_name = "channel/pending_list.html"

    def get(self, request):
        pending_request = UserChannel.objects.filter(status="Pending")
        return render(request, self.template_name,
                      {"pending_request": pending_request})


@method_decorator(login_required, name='dispatch')
class ApproveRequest(View):

    def get(self, request, pk):
        UserChannel.objects.filter(pk=pk).update(status="Joined")
        return redirect(reverse('content:join_request'))


@method_decorator(login_required, name='dispatch')
class RejectContent(View):

    def get(self, request, pk):
        channel_group = ChannelGroupContent.objects.filter(pk=pk,
                                                           is_delete=False)
        channel_group.update(status="Reject")
        channel_group = channel_group.first()

        return redirect(reverse('content:pending_content'))


@method_decorator(login_required, name='dispatch')
class ApproveContent(View):

    def get(self, request, pk):
        channel_group = ChannelGroupContent.objects.filter(pk=pk,
                                                           is_delete=False)
        channel_group.update(status="Live")
        channel_group = channel_group.first()
        Content.objects.filter(pk=channel_group.content.pk).update(
            status="Live")

        return redirect(reverse('content:pending_content'))


@method_decorator(login_required, name='dispatch')
class JoinChannel(View):

    def post(self, request):
        Channels = Channel.objects.get(pk=request.POST['id'])

        if user_channel := UserChannel.objects.filter(user=request.user,
                                                      Channel=Channels):
            if user_channel.first().status == "removed":
                user_channel = user_channel.first()
                context = {
                    "message":
                    f"You're removed from this journey, Please contact to {user_channel.program_team_email} for re-enrollment",
                    "class": "danger"
                }
                return reverse('content:browse_channel')
        else:
            UserChannel.objects.create(user=request.user,
                                       Channel=Channels,
                                       status="Joined")
            # if Channels.channel_type in ["onlyCommunity", "Course"]:
            #     status = "Joined"
            # else:
            #     status = "Pending" if Channels.is_test_required else "Joined"
            # if status == "Joined":
            #     form_reverse = reverse('content:Channel_content', kwargs={'Channel': Channels.pk})
            # else:
            #     form_reverse = reverse('content:browse_channel')
            add_user_to_company(request.user, Channels.company)
            context = {
                "screen": "ProgramJourney",
                "navigationPayload": {
                    "courseId": str(Channels.id)
                }
            }
            send_push_notification(request.user, Channels.title,
                                   f"You're enrolled in {Channels.title}",
                                   context)
            NotificationAndPoints(request.user, "joined journey")
            subject = f"{request.user.username} Welcome to {Channels.title}"
            email_template_name = "email/join_journey.txt"
            if Channels.whatsapp_notification_required and (
                    request.user.phone and request.user.is_whatsapp_enable):
                journey_enrolment(request.user, Channels)
            else:
                print("phone does not exist")
            c = {
                "email": request.user.email,
                'domain': DOMAIN,
                'site_name': SITE_NAME,
                "user": request.user,
                'protocol': PROTOCOL,
            }
            email = render_to_string(email_template_name, c)
            try:
                send_mail(subject,
                          email,
                          INFO_CONTACT_EMAIL, [request.user.email],
                          fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            if Channels.is_community_required:
                add_member_to_space(Channels, request.user)
        return redirect(reverse('content:browse_channel'))


@method_decorator(login_required, name='dispatch')
class UpdateContentTitle(View):

    def post(self, request):
        id = request.POST['id']
        title = request.POST['title']
        Content.objects.filter(pk=id).update(title=title)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class ChannelUserList(View):
    template_name = "channel/channel_user_list.html"

    def get(self, request, **kwargs):
        channel_id = self.kwargs['channel_id']
        user_list = UserChannel.objects.filter(Channel=channel_id)
        return render(request, self.template_name, {"user_list": user_list})


@method_decorator(login_required, name='dispatch')
class DeleteOption(View):

    def post(self, request, **kwargs):
        id = self.request.POST['id']
        c_option = ContentDataOptions.objects.filter(pk=id)
        if c_option.delete():
            return HttpResponse()
        else:
            return HttpResponse("Something Went Wrong")


@method_decorator(login_required, name='dispatch')
class DeleteSubtitleOption(View):

    def post(self, request, **kwargs):
        id = self.request.POST['id']
        c_option = VideoSubtitles.objects.filter(pk=id)
        if c_option.delete():
            return HttpResponse()
        else:
            return HttpResponse("Something Went Wrong")


@method_decorator(login_required, name="dispatch")
class CorrectAnswer(View):

    def post(self, request, **kwargs):
        id = self.request.POST['id']

        c_option = ContentDataOptions.objects.filter(pk=id).update(
            correct_answer=True)
        if c_option:
            return HttpResponse("Success")
        else:
            return HttpResponse("Something Went Wrong")


@method_decorator(login_required, name="dispatch")
class ContentQuizAsnwer(View):

    def post(self, request, **kwargs):
        id = self.request.POST['id']
        option = self.request.POST['option']
        get_cd = ContentData.objects.get(id=id)
        cd_option = ContentDataOptions.objects.filter(content_data=get_cd)
        ContetnOptionSubmit.objects.create(content_data=get_cd,
                                           option=option,
                                           user=self.request.user)
        ca = cd_option.filter(correct_answer=True)[0]
        cd_option = cd_option.filter(option=option)[0]
        response = {
            "correct_answer": cd_option.correct_answer,
            "answer": ca.option
        }
        return JsonResponse(response)


@method_decorator(login_required, name="dispatch")
class ContentPollAnswer(View):

    def post(self, request, **kwargs):
        id = self.request.POST['id']
        option = self.request.POST['option']
        get_cd = ContentData.objects.get(id=id)
        ContetnOptionSubmit.objects.create(content_data=get_cd,
                                           option=option,
                                           user=self.request.user)
        cd_option = ContentDataOptions.objects.filter(content_data=get_cd)

        response = []
        for cd_option in cd_option:
            get_user_result = ContetnOptionSubmit.objects.filter(
                content_data=get_cd)
            total_answer = get_user_result.count()
            count = get_user_result.filter(option=cd_option.option).count()

            if count == 0:
                avg_count = 0
            else:
                avg_count = (count / total_answer) * 100

            response.append({
                "id": cd_option.id,
                "option": cd_option.option,
                "count": avg_count
            })
        return JsonResponse(response, safe=False)


@method_decorator(login_required, name='dispatch')
class UploadContentBanner(View):

    def post(self, request):
        id = request.POST["id"]
        get_content = Content.objects.get(id=id)
        get_content.image = request.FILES['file']
        get_content.save()
        return redirect(reverse('content:all-content'))


@method_decorator(login_required, name='dispatch')
class CheckSubChannel(View):

    def post(self, request):
        id = request.POST['channel']
        get_channel = Channel.objects.get(pk=id)
        if get_channel.channel_type == "SkillDevelopment":
            channels = Channel.objects.filter(parent_id=id,
                                              is_delete=False,
                                              is_active=True)
            data = []
            for channel in channels:
                data.append({'title': channel.title, 'id': channel.pk})

            response = {
                "SkillDevelopment": True,
                "data": data,
                "is_test_required": get_channel.is_test_required
            }
        else:
            response = {"SkillDevelopment": False}
        return JsonResponse(response, safe=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(allowed_users(allowed_roles=["Admin", "ProgramManager"]),
                  name="dispatch")
class ConfigCourse(View):
    template_name = 'channel/config-course.html'

    def get(self, request):

        return render(request, self.template_name)

    def post(self, request):
        # post_assessment = TestSeries.objects.get(id=request.POST['post_assessment'])
        try:
            pre_assessment = TestSeries.objects.get(
                id=request.POST['pre_assessment'])
        except:
            pre_assessment = None

        try:
            journey_pre_assessment = TestSeries.objects.get(
                id=request.POST['journey_pre_assessment'])
        except:
            journey_pre_assessment = None
        role = UserRoles.objects.get(pk=request.POST['role'])
        group = request.POST.getlist('group[]')
        post_assessment_list = request.POST.getlist('post_assessment[]')

        Channels = Channel.objects.get(pk=request.POST['channel'])
        if Channels.channel_type == "SkillDevelopment":
            SubChannel_id = request.POST['sub_channel']
            sub_channel = Channel.objects.get(pk=SubChannel_id)
            sub_channel.test_series = pre_assessment
            sub_channel.save()
        skill_config = SkillConfig.objects.create(
            role=role,
            channel=Channels,
            journey_pre_assessment=journey_pre_assessment,
            sub_channel=sub_channel,
            pre_assessment=pre_assessment)
        for x in range(len(post_assessment_list)):
            channel_group = ChannelGroup.objects.get(pk=group[x])
            post_assessment = TestSeries.objects.get(
                id=post_assessment_list[x])

            SkillConfigLevel.objects.create(skill_config=skill_config,
                                            channel_group=channel_group,
                                            assessment=post_assessment)
            ChannelGroup.objects.filter(
                pk=group[x],
                is_delete=False).update(post_assessment=post_assessment)
        Channels.test_series = journey_pre_assessment
        Channels.save()

        if "ProgramManager" == self.request.session['user_type']:
            return redirect(reverse('program_manager:manage'))
        else:
            return redirect(reverse('content:config_course_list'))
        # return redirect(reverse('content:config_course_list'))


@method_decorator(login_required, name='dispatch')
@method_decorator(allowed_users(allowed_roles=["Admin", "ProgramManager"]),
                  name="dispatch")
class ConfigCourseList(ListView):
    model = SkillConfig
    context_object_name = "config_lists"
    template_name = "channel/course_config_list.html"

    def get_queryset(self):
        company = company_journeys(self.request.session['user_type'],
                                   self.request.user,
                                   self.request.session.get('company_id'))
        return SkillConfig.objects.filter(channel__in=company)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class DeleteConfigRecord(View):

    def post(self, request, **kwargs):
        channel_id = self.request.POST['pk']
        SkillConfig.objects.filter(id=channel_id).delete()

        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
@method_decorator(allowed_users(allowed_roles=["Admin", "ProgramManager"]),
                  name="dispatch")
class ConfigCourseEdit(View):

    def get(self, request, **kwargs):

        id = self.kwargs['pk']
        skill_config = SkillConfig.objects.get(id=id)

        return render(request, "channel/edit-config-course.html",
                      {"skill_config": skill_config})

    def post(self, request, **kwargs):
        pre_assessment = TestSeries.objects.get(
            id=request.POST['pre_assessment'])
        journey_pre_assessment = TestSeries.objects.get(
            id=request.POST['journey_pre_assessment'])
        role = UserRoles.objects.get(pk=request.POST['role'])
        Channels = Channel.objects.get(pk=request.POST['channel'])
        skill_config = SkillConfig.objects.get(id=request.POST['id'])
        skill_config.role = role
        skill_config.channel = Channels
        skill_config.pre_assessment = pre_assessment
        skill_config.journey_pre_assessment = journey_pre_assessment
        skill_level = request.POST.getlist('skill_level_id[]')
        group = request.POST.getlist('group[]')
        post_assessment_list = request.POST.getlist('post_assessment[]')

        for x in range(len(skill_level)):
            channel_group = ChannelGroup.objects.get(pk=group[x])
            post_assessment = TestSeries.objects.get(
                id=post_assessment_list[x])
            SkillConfigLevel.objects.filter(
                pk=skill_level[x],
                channel_group=channel_group).update(assessment=post_assessment)
            ChannelGroup.objects.filter(
                pk=group[x],
                is_delete=False).update(post_assessment=post_assessment)

        if Channels.channel_type == "SkillDevelopment":
            SubChannel_id = request.POST['sub_channel']
            sub_channel = Channel.objects.get(pk=SubChannel_id)
            skill_config.sub_channel = sub_channel
            sub_channel.test_series = pre_assessment
            sub_channel.save()
        Channels.test_series = journey_pre_assessment
        Channels.save()
        skill_config.save()
        if "ProgramManager" == self.request.session['user_type']:
            return redirect(reverse('program_manager:manage'))
        else:
            return redirect(reverse('content:config_course_list'))
        # return redirect(reverse_lazy('content:config_course_list'))


@method_decorator(login_required, name='dispatch')
class UserJourney(View):

    def get(self, request, pk):
        import json
        user = Learner.objects.get(pk=pk)
        user_channels = UserChannel.objects.filter(user=user)
        user_channel_data = []
        user_channel_content = []
        user_channel_survey = []
        user_skill = []
        skill_group = []
        skill_assessment = []
        skill_pre_assessment = []
        skill_user_channel_content = []
        user_channel_pre_assessmnet = []
        for user_channel in user_channels:
            channel_group = ChannelGroup.objects.filter(
                channel=user_channel.Channel, is_delete=False).first()
            user_channel_data.append({
                'key': user_channel.Channel.title,
            })
            if user_channel.Channel.survey is not None:
                user_channel_survey.append({
                    'key': user_channel.Channel.survey.name,
                    'parent': user_channel.Channel.title,
                    'color': 'redgrad'
                })
            if user_channel.Channel.test_series is not None:
                user_channel_pre_assessmnet.append({
                    'key':
                    user_channel.Channel.test_series.name + "(Pre Assessment)",
                    'parent':
                    user_channel.Channel.title,
                    'color':
                    'redgrad'
                })

            for skill in Channel.objects.filter(
                    parent_id=user_channel.Channel):

                for skill_groups in ChannelGroup.objects.filter(
                        channel=skill, is_delete=False):
                    for content in ChannelGroupContent.objects.filter(
                            channel_group=skill_groups, is_delete=False):
                        user_course_count = UserCourseStart.objects.filter(
                            content=content.content,
                            channel=skill_groups.channel,
                            channel_group=skill_group,
                            user=user,
                            status="Complete").count()

                        if user_course_count > 0:
                            color = "green"
                        else:
                            color = "coursegrad"

                        skill_user_channel_content.append({
                            'key':
                            content.content.title,
                            'parent':
                            skill_groups.title + " " +
                            skill_groups.channel.title,
                            'color':
                            color
                        })

                        skill_assessment.append({
                            'key':
                            skill_groups.post_assessment.name
                            if skill_groups.post_assessment else "Dummy",
                            'parent':
                            content.content.title,
                            'color':
                            'redgrad'
                        })
                    if skill.test_series is not None:
                        skill_group.append({
                            'key':
                            skill_groups.title + " " +
                            skill_groups.channel.title,
                            'parent':
                            skill.test_series.name + "(Skill Pre Assessment)",
                            'color':
                            'redgrad'
                        })
                if skill.test_series is not None:
                    user_skill.append({
                        'key':
                        skill.title,
                        'parent':
                        user_channel.Channel.test_series.name +
                        "(Pre Assessment)",
                        'color':
                        'redgrad'
                    })
                if skill.test_series is not None:
                    skill_pre_assessment.append({
                        'key':
                        skill.test_series.name + "(Skill Pre Assessment)",
                        'parent':
                        skill.title,
                        'color':
                        'redgrad'
                    })

            if user_channel.Channel.parent_id != "SkillDevelopment":
                for content in ChannelGroupContent.objects.filter(
                        channel_group=channel_group, is_delete=False):
                    user_course_count = UserCourseStart.objects.filter(
                        content=content.content,
                        channel=user_channel.Channel,
                        user=user,
                        status="Complete").count()
                    if user_course_count > 0:
                        color = "green"
                    else:
                        color = "coursegrad"
                    user_channel_content.append({
                        'key':
                        content.content.title,
                        'parent':
                        user_channel.Channel.title,
                        'color':
                        color,
                    })

        user_channel_data = json.dumps(user_channel_data)
        user_channel_content = json.dumps(user_channel_content)
        user_skill = json.dumps(user_skill)
        skill_assessment = json.dumps(skill_assessment)
        skill_group = json.dumps(skill_group)
        skill_user_channel_content = json.dumps(skill_user_channel_content)
        user_channel_survey = json.dumps(user_channel_survey)
        user_channel_pre_assessmnet = json.dumps(user_channel_pre_assessmnet)
        skill_pre_assessment = json.dumps(skill_pre_assessment)
        context = {
            'user': user,
            "user_channel_data": user_channel_data,
            'user_channel_content': user_channel_content,
            'user_skill': user_skill,
            "skill_group": skill_group,
            "skill_assessment": skill_assessment,
            "skill_user_channel_content": skill_user_channel_content,
            "user_channel_survey": user_channel_survey,
            "user_channel_pre_assessmnet": user_channel_pre_assessmnet,
            "skill_pre_assessment": skill_pre_assessment,
        }
        return render(request, 'users/report.html', context)


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class CompleteSkill(View):

    def get(self, request, **kwargs):
        content = Content.objects.get(pk=self.kwargs['content'])
        channel_group = ChannelGroup.objects.get(pk=self.kwargs['group'])
        channel = Channel.objects.get(pk=channel_group.channel.pk)
        user_course = UserCourseStart.objects.filter(
            user=request.user,
            content=content,
            channel_group=channel_group,
            channel=channel).update(status="Complete")
        # CourseCompletion(request.user, channel)
        # print("before")
        CheckEndOfJourney(request.user, channel.pk, userType=request.session['user_type'])
        UserReadContentData.objects.filter(
            user=request.user,
            content=content,
            channel_group=channel_group,
            channel=channel).update(status='Complete')
        return redirect(
            reverse('content:Channel_content', kwargs={'Channel': channel.pk}))


@method_decorator(login_required, name='dispatch')
class JourneyReport(View):

    def get(self, request, pk):
        user = Learner.objects.get(pk=pk)

        context = {'user': user}
        return render(request, 'users/journey_report.html', context)

    def post(self, request, pk):
        user = Learner.objects.get(pk=pk)
        get_channel = Channel.objects.get(pk=request.POST['channel'])
        Channel_list = []
        course_start = []
        Channel_list.append(get_channel)
        if get_channel.channel_type == "SkillDevelopment":
            get_channel = Channel.objects.filter(parent_id=get_channel)
            for get_channel in get_channel:
                Channel_list.append(get_channel)
        channel_group = ChannelGroup.objects.filter(channel__in=Channel_list,
                                                    is_delete=False)
        group_content = ChannelGroupContent.objects.filter(
            channel_group__in=channel_group, is_delete=False)
        course_starts = UserCourseStart.objects.filter(
            user=user, channel__in=Channel_list)
        for course_starts in course_starts:
            course_start.append(course_starts.content)
        test_attempt = TestAttempt.objects.filter(user=user,
                                                  channel__in=Channel_list)
        survey_attempt = SurveyAttemptChannel.objects.filter(
            user=user, channel__in=Channel_list)

        context = {
            'user': user,
            "course_start": course_start,
            "test_attempt": test_attempt,
            "survey_attempt": survey_attempt,
            "group_content": group_content
        }
        return render(request, 'users/journey_report.html', context)


@method_decorator(login_required, name='dispatch')
class JourneyAllReport(View):

    def get(self, request, channel):
        get_channels = Channel.objects.get(pk=channel)
        Channel_list = []
        users_list = []
        user_courses = []
        test_attempts = []
        group_content = []
        survey_attempts = []
        Channel_list.append(get_channels)
        print("get_channels ", get_channels)
        if get_channels.channel_type == "SkillDevelopment":
            get_channel = Channel.objects.filter(parent_id=get_channels)
            for get_channel in get_channel:
                Channel_list.append(get_channel)
        channel_group = ChannelGroup.objects.filter(channel__in=Channel_list,
                                                    is_delete=False)
        group_contents = ChannelGroupContent.objects.filter(
            channel_group__in=channel_group, is_delete=False)

        user_channel = UserChannel.objects.filter(Channel=get_channels)
        for user_channel in user_channel:
            print("user_channel ", user_channel)
            user = User.objects.get(pk=user_channel.user.id)

            for group_content in group_contents:

                course_starts = UserCourseStart.objects.filter(
                    user=user,
                    channel__in=Channel_list,
                    content=group_content.content)

                if course_starts.count() > 0:
                    status = course_starts.first().status
                else:
                    status = "Pending"

                if group_content.channel_group.channel.parent_id == None:
                    journey = group_content.channel_group.channel
                    skill = "-"
                else:
                    journey = group_content.channel_group.channel.parent_id
                    skill = group_content.channel_group.channel

                users_list.append({
                    "user": user.username,
                    "journey": journey,
                    "skill": skill,
                    "content": group_content.content,
                    "status": status
                })
            test_attempt = TestAttempt.objects.filter(user=user,
                                                      channel__in=Channel_list)
            for test_attempt in test_attempt:
                test_attempts.append(test_attempt)
            survey_attempt = SurveyAttemptChannel.objects.filter(
                user=user, channel__in=Channel_list)
            for survey_attempt in survey_attempt:
                survey_attempts.append(survey_attempt)
        context = {
            "group_content": group_content,
            "users_list": users_list,
            "test_attempt": test_attempts,
            "survey_attempt": survey_attempts
        }
        return render(request, 'users/journey_all_report.html', context)


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class CourseSummary(View):
    template_name = "channel/course_summary.html"

    def get(self, request, **kwargs):
        try: content = Content.objects.get(pk=self.kwargs['pk'])
        except: return render(request, '404.html')
        try: channel_group = ChannelGroup.objects.get(pk=self.kwargs['group'])

        except: return render(request, '404.html')
        try: channel = Channel.objects.get(pk=channel_group.channel.pk)

        except: return render(request, '404.html')
        parent_check = is_parent_channel(channel_group.channel.pk)
        
        print(parent_check, "parent_check")
        result = []
        content_data = ContentData.objects.filter(
            content=self.kwargs['pk']).order_by("display_order")
        user_course = UserCourseStart.objects.filter(
            user=request.user,
            content=self.kwargs['pk'],
            channel_group=channel_group,
            channel=channel)

        time = 0
        total_time = 0
        total_content = content_data.count()
        complete = 0
        progress = 0
        for content_data in content_data:
            try:
                read_content = UserReadContentData.objects.get(
                    user=request.user, content_data=content_data)
                status = read_content.status
            except:
                status = "Start"
            if status == "Complete":
                complete = complete + 1

            result.append({
                'title': content_data.title,
                'status': status,
                'type': content_data.type,
                'display_order': content_data.display_order
            })
            if content_data.type == "Text":
                time = 3
                total_time = total_time + time
            elif content_data.type == "Image":
                time = 1
                total_time = total_time + time
            elif content_data.type == "Video":
                time = 5
                total_time = total_time + time
            elif content_data.type == "YtVideo":
                time = 5
                total_time = total_time + time
            elif content_data.type == "Quiz":
                time = 2
                total_time = total_time + time
            elif content_data.type == "Poll":
                time = 1
                total_time = total_time + time
            elif content_data.type == "Pdf":
                time = 2
                total_time = total_time + time
            elif content_data.type == "Activity":
                time = 10
                total_time = total_time + time

            try:
                progress = math.ceil((complete / total_content) * 100)

            except:
                progress = 0
        try:
            space_journey = SpaceJourney.objects.get(journey=channel)
            space_id = space_journey.space.id
        except:
            space_id = ""

        context = {
            "content_data": result,
            "channel": channel,
            "content": content,
            'group': channel_group,
            "total_time": total_time,
            'progress': progress,
            "parent_check": parent_check,
            "space_id": space_id,
            "community_url": COMMUNITY_URL
        }
        response = render(request, self.template_name, context)
        response.set_cookie(
            'last_course_url',
            reverse("content:course_summary",
                    kwargs={
                        'pk': content.pk,
                        'group': channel_group.pk
                    }))
        return response


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class ThankYou(View):
    template_name = "channel/thank-you.html"

    def get(self, request, **kwargs):
        content = Content.objects.get(pk=self.kwargs['content'])
        channel_group = ChannelGroup.objects.get(pk=self.kwargs['group'])
        channel = Channel.objects.get(pk=channel_group.channel.pk)
        parent_check = is_parent_channel(channel_group.channel.pk)
        if channel.channel_type == "SkillDevelopment":
            if channel_group.post_assessment is None:
                go_next = "None"
            else:
                go_next = reverse_lazy('test_series:test_series_form',
                                       kwargs={
                                           'pk':
                                           channel_group.post_assessment.pk,
                                           'channel': channel.pk,
                                       })
        else:
            try:

                display_content = ChannelGroupContent.objects.get(
                    channel_group=channel_group, content=content, is_delete=False)
                order = display_content.display_order + 1
                channel_content = ChannelGroupContent.objects.get(
                    channel_group=channel_group, display_order=order)

                go_next = reverse_lazy('content:read_content',
                                       kwargs={
                                           'pk': channel_content.content.pk,
                                           'group': channel_group.pk
                                       })
            except:
                go_next = "None"
        if channel.channel_type == "SkillDevelopment":
            go_previous = None
        else:
            try:
                display_content = ChannelGroupContent.objects.get(
                    channel_group=channel_group, content=content, is_delete=False)
                order = display_content.display_order - 1
                channel_content = ChannelGroupContent.objects.get(
                    channel_group=channel_group, display_order=order)

                go_previous = reverse_lazy('content:read_content',
                                           kwargs={
                                               'pk':
                                               channel_content.content.pk,
                                               'group': channel_group.pk
                                           })
            except:
                go_previous = None
        content_data = ContentData.objects.filter(
            content=content).order_by("display_order")
        congrates = [
            'https://media3.giphy.com/media/xUOrwiqZxXUiJewDrq/giphy.gif',
            'https://media2.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif',
            'https://media0.giphy.com/media/3o6Mbnll2gudglC3HG/giphy.gif',
            'https://media3.giphy.com/media/YP258EkezKv5RSPGRI/giphy.gif',
            'https://media1.giphy.com/media/puLcabEWerzmSJnPj3/giphy.gif',
            'https://media2.giphy.com/media/l3ZgKEvYiwSPXu1ic7/giphy.gif',
            'https://media2.giphy.com/media/H7YO03BHmBMWuWUkez/giphy.gif'
        ]
        context = {
            "channel": channel,
            "content": content,
            "go_next": go_next,
            "group": channel_group,
            "content_data": content_data,
            "mode": "Learn",
            "image": random.choice(congrates),
            "go_previous": go_previous,
            "parent_check": parent_check
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class ReviceMode(View):
    template_name = "channel/read_content.html"

    def get(self, request, **kwargs):
        content = Content.objects.get(pk=self.kwargs['pk'])
        channel_group = ChannelGroup.objects.get(pk=self.kwargs['group'])
        channel = Channel.objects.get(pk=channel_group.channel.pk)
        parent_check = is_parent_channel(channel_group.channel.pk)
        if channel.channel_type == "SkillDevelopment":
            go_next = "None"
        else:

            display_content = ChannelGroupContent.objects.get(
                channel_group=channel_group, content=content, is_delete=False)
            order = display_content.display_order + 1
            try:
                channel_content = ChannelGroupContent.objects.get(
                    channel_group=channel_group, display_order=order)

                go_next = reverse_lazy('content:read_content',
                                       kwargs={
                                           'pk': channel_content.content.pk,
                                           'group': channel_group.pk
                                       })
            except:
                go_next = "None"

        if channel.channel_type == "SkillDevelopment":
            go_previous = None
        else:

            display_content = ChannelGroupContent.objects.get(
                channel_group=channel_group, content=content, is_delete=False)
            order = display_content.display_order - 1
            try:
                channel_content = ChannelGroupContent.objects.get(
                    channel_group=channel_group, display_order=order)

                go_previous = reverse_lazy('content:read_content',
                                           kwargs={
                                               'pk':
                                               channel_content.content.pk,
                                               'group': channel_group.pk
                                           })
            except:
                go_previous = None

        result = []
        data = ContentData.objects.filter(
            content=self.kwargs['pk']).order_by("display_order")
        user_course = UserCourseStart.objects.filter(
            user=request.user,
            content=self.kwargs['pk'],
            channel_group=channel_group,
            channel=channel)
        for data in data:
            content_data_option = ContentDataOptions.objects.filter(
                content_data=data)
            response = []
            if data.type == "Poll":
                for cd_option in content_data_option:
                    check_user = ContetnOptionSubmit.objects.filter(
                        user=self.request.user, content_data=data)
                    if check_user.count() > 0:
                        get_user_result = ContetnOptionSubmit.objects.filter(
                            content_data=data)
                        total_answer = get_user_result.count()
                        count = get_user_result.filter(
                            option=cd_option.option).count()

                        if count == 0:
                            avg_count = 0
                        else:
                            avg_count = (count / total_answer) * 100

                        response.append({
                            "id": cd_option.id,
                            "option": cd_option.option,
                            "count": avg_count,
                            "my_response": True
                        })
            elif data.type == "Quiz":
                get_user_result = ContetnOptionSubmit.objects.filter(
                    content_data=data, user=self.request.user)
                if get_user_result.count() > 0:
                    get_user_result = get_user_result.first()
                    content_data_options = ContentDataOptions.objects.filter(
                        content_data=data, correct_answer=True)
                    for cd_option in content_data_options:
                        response = {
                            "option":
                            cd_option.option,
                            "my_answer":
                            get_user_result.option,
                            "is_true":
                            True if cd_option.option == get_user_result.option
                            else False
                        }

            result.append({
                "id": data.id,
                "content": data.content,
                "title": data.title,
                "type": data.type,
                "data": data.data,
                "link_data": data.link_data,
                "file": data.file,
                "video": data.video,
                "url": data.url,
                "display_order": data.display_order,
                "content_data_option": content_data_option,
                "poll_response": response,
                "parent_check": parent_check,
                "activity_type": data.activity_type,
            })
        # channel = Channel.objects.filter(parent_id=None)

        response = render(
            request, self.template_name, {
                "data": result,
                "channel": channel,
                "content": content,
                "group": channel_group,
                "go_next": go_next,
                "go_previous": go_previous,
                "mode": "revise",
                "parent_check": parent_check
            })
        response.set_cookie(
            'last_course_url',
            reverse("content:revice_mode",
                    kwargs={
                        'pk': content.pk,
                        'group': channel_group.pk
                    }))
        return response


@method_decorator(login_required, name='dispatch')
class add_link_type_content(View):

    def post(self, request):
        type = "Link"
        link_type = request.POST['link_type']
        redirection = request.POST['redirection']
        new_tab_open = request.POST['new_tab_open']
        data = {
            "link_type": link_type,
            "redirection": redirection,
            "new_tab_open": new_tab_open,
            "external_redirection_page":
            request.POST['external_redirection_page']
        }
        main_content = Content.objects.get(pk=request.POST['content_id'])
        display_order = ContentData.objects.filter(
            content=main_content).count()
        content_data = ContentData.objects.create(type=type,
                                                  link_data=data,
                                                  content=main_content,
                                                  display_order=display_order +
                                                  1)
        main_content.status = "Pending"
        main_content.save()

        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class program_announce_wp_report(View):

    def get(self, request):
        data = VonageWhatsappReport.objects.all()
        context = {"data": data}
        return render(request, "program_announce_wp_report.html", context)


@login_required
def journey_list(request):
    if request.method == "POST":
        company_id = request.POST['company_id']
        company = Company.objects.get(pk=company_id)
        journey = Channel.objects.filter(company=company,
                                         parent_id=None,
                                         is_active=True,
                                         is_delete=False)
        journey_list = [{
            "pk": journey.pk,
            "name": journey.title
        } for journey in journey]
        response = {"success": True, "journey_list": journey_list}
        return JsonResponse(response, safe=False)


@login_required
def journey_all_content(request):
    if request.method == 'POST':
        journey = Channel.objects.get(id=request.POST['journey_id'])
        content_data = []
        survey_list = []
        assessment_list = []
        journal_list = []
        profile_assest = ProfileAssestQuestion.objects.filter(
            journey=journey.pk, is_active=True, is_delete=False)
        assessment_list = [{
            "id": data.pk,
            "title": data.question
        } for data in profile_assest]
        if journey.channel_type == "MentoringJourney" or journey.channel_type == "SelfPaced":
            mentoring_journey = MentoringJourney.objects.filter(
                journey=journey, is_delete=False)
            for data in mentoring_journey:
                if data.meta_key == "quest":
                    content_data.append({"id": data.value, "title": data.name})
                elif data.meta_key == "survey":
                    survey_list.append({"id": data.value, "title": data.name})
                elif data.meta_key == "journals":
                    journal_list.append({"id": data.value, "title": data.name})
        else:
            if journey.channel_type == "SkillDevelopment":
                skills = Channel.objects.filter(parent_id=journey,
                                                is_active=True,
                                                is_delete=False)
                channel_group = ChannelGroup.objects.filter(channel__in=skills,
                                                            is_delete=False)
            else:
                channel_group = ChannelGroup.objects.filter(channel=journey,
                                                            is_delete=False)
            channel_content = ChannelGroupContent.objects.filter(
                channel_group__in=channel_group,
                is_delete=False).values('content')
            contents = Content.objects.filter(pk__in=channel_content,
                                              is_delete=False)
            content_data = [{
                "id": data.id,
                "title": data.title
            } for data in contents]

            surveys = SurveyChannel.objects.filter(channel=journey)
            survey_list = [{
                "id": survey.survey.id,
                "title": survey.survey.name
            } for survey in surveys]

        return JsonResponse({
            "success": False,
            "content_list": content_data,
            "assessment_list": assessment_list,
            "survey_list": survey_list,
            "journal_list": journal_list
        })


@method_decorator(login_required, name='dispatch')
class CreateJourneyContentPageSetup(CreateView):
    template_name = "channel/journey-content-order-setup.html"
    model = journeyContentSetup

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        print("data ", request.POST)
        channel = Channel.objects.filter(id=request.POST['channel'],
                                         parent_id=None)
        overview = request.POST['overview']
        learn_label = request.POST['learn_label']
        pdpa_label = request.POST['pdpa_label']
        video_url = request.POST['video_url']
        pdpa_description = request.POST['pdpa_description']
        cta_button_title = request.POST['cta_button_title']
        cta_button_action = request.POST['cta_button_action']
        short_description = request.POST['short_description']
        description = request.POST['description']
        what_we_learn = request.POST['what_we_learn']
        tags = request.POST['tags']
        try:
            profle_assest_enable = check_check_box(
                request.POST['profle_assest_enable'])
        except:
            profle_assest_enable = False
        print("profle_assest_enable ", profle_assest_enable)
        channel.update(short_description=short_description,
                       description=description,
                       what_we_learn=what_we_learn,
                       tags=tags,
                       profle_assest_enable=profle_assest_enable)
        channel = channel.first()
        try:
            is_draft = check_check_box(request.POST['is_draft'])
        except:
            is_draft = False
        content_setup = self.model.objects.create(
            journey=channel,
            overview=overview,
            learn_label=learn_label,
            cta_button_title=cta_button_title,
            cta_button_action=cta_button_action,
            pdpa_description=pdpa_description,
            pdpa_label=pdpa_label,
            video_url=video_url,
            created_by=self.request.user,
            is_draft=is_draft)
        for key in request.POST:
            if key in [
                    "overview", "learn_label", "pdpa_description",
                    "pdpa_label", "video_url", "cta_button_title"
            ]:
                value = request.POST[key]
                display_order = request.POST[f"{key}_order"] or 1
                button_action = cta_button_action if key == "cta_button_title" else ''
                JourneyContentSetupOrdering.objects.create(
                    content_setup=content_setup,
                    journey=channel,
                    type=key,
                    data=value,
                    display_order=display_order,
                    cta_button_action=button_action,
                    default_order=display_order)
        if "ProgramManager" == self.request.session['user_type']:
            return redirect('program_manager:setup')
        return redirect('content:list_journey_page_setup')


@method_decorator(login_required, name='dispatch')
class JourneyContentPageSetup(ListView):
    model = journeyContentSetup
    context_object_name = "journey_content_data"
    template_name = "channel/journey-content-setup-list.html.html"

    def get_queryset(self):
        return journeyContentSetup.objects.filter(is_active=True,
                                                  is_delete=False)


@method_decorator(login_required, name='dispatch')
class DeletePageSetup(View):

    def post(self, request):
        setup_id = request.POST['pk']
        journeyContentSetup.objects.filter(id=setup_id).update(is_active=False,
                                                               is_delete=True)
        JourneyContentSetupOrdering.objects.filter(
            content_setup__id=setup_id).update(is_active=False)
        return JsonResponse({"success": True})


@method_decorator(login_required, name='dispatch')
class EditPageSetup(View):
    template_name = "channel/edit-journey-content-order-setup.html"
    model = journeyContentSetup

    def get(self, request, *args, **kwargs):
        content_setup = self.model.objects.get(id=self.kwargs['pk'])
        ordering = JourneyContentSetupOrdering.objects.filter(
            content_setup=content_setup, is_active=True)
        return render(request, self.template_name, {
            "ordering": ordering,
            "content_setup": content_setup
        })

    def post(self, request, *args, **kwargs):
        print(request.POST)
        journey_setup = self.model.objects.filter(id=self.kwargs['pk']).first()
        try:
            request.POST['channel']
            channel = Channel.objects.get(id=request.POST['channel'],
                                          parent_id=None)
        except Exception:
            channel = journey_setup.journey
        short_description = request.POST.get('short_description',
                                             channel.short_description)
        description = request.POST.get('description', channel.description)
        what_we_learn = request.POST.get('what_we_learn',
                                         channel.what_we_learn)
        tags = request.POST.get('tags')
        profle_assest_enable = check_check_box(
            request.POST.get('profle_assest_enable',
                             channel.profle_assest_enable))
        Channel.objects.filter(id=channel.id).update(
            short_description=short_description,
            tags=tags,
            description=description,
            what_we_learn=what_we_learn,
            profle_assest_enable=profle_assest_enable)
        overview = request.POST.get('overview', '')
        learn_label = request.POST.get('learn_label', '')
        pdpa_label = request.POST.get('pdpa_label', '')
        video_url = request.POST.get('video_url', '')
        pdpa_description = request.POST.get('pdpa_description', '')
        cta_button_title = request.POST.get('cta_button_title', '')
        cta_button_action = request.POST.get('cta_button_action', '')
        is_draft = check_check_box(
            request.POST.get('is_draft', journey_setup.is_draft))
        self.model.objects.filter(id=self.kwargs['pk']).update(
            journey=channel,
            overview=overview,
            learn_label=learn_label,
            cta_button_title=cta_button_title,
            cta_button_action=cta_button_action,
            pdpa_description=pdpa_description,
            pdpa_label=pdpa_label,
            video_url=video_url,
            created_by=self.request.user,
            is_draft=is_draft)
        for key in request.POST:
            if key in [
                    "overview", "learn_label", "pdpa_description",
                    "pdpa_label", "video_url", "cta_button_title"
            ]:
                value = request.POST[key]
                display_order = request.POST[f"{key}_order"] or 1
                button_action = cta_button_action if key == "cta_button_title" else ''
                journey_content_ordering = JourneyContentSetupOrdering.objects.filter(
                    journey=channel,
                    type=key,
                    content_setup__id=self.kwargs['pk'],
                    is_active=True)
                journey_content_ordering.update(
                    data=value,
                    display_order=display_order,
                    cta_button_action=button_action)
                if not is_draft:
                    journey_content_ordering.update(
                        default_order=display_order)
        if self.request.session['user_type'] == "ProgramManager":
            return redirect('program_manager:setup')
        return redirect('content:list_journey_page_setup')


@method_decorator(login_required, name='dispatch')
class ShowJourneyConfigPage(View):

    def get(self, request, *args, **kwargs):
        content_setup = journeyContentSetup.objects.get(id=self.kwargs['pk'])
        ordering = JourneyContentSetupOrdering.objects.filter(
            content_setup=content_setup, is_active=True)
        return render(request, "channel/course-details-preview-page.html", {
            "ordering": ordering,
            "content_setup": content_setup
        })


@method_decorator(login_required, name='dispatch')
class ShowJourneyConfigSignupPage(View):

    def get(self, request, *args, **kwargs):
        content_setup = journeyContentSetup.objects.get(id=self.kwargs['pk'])
        ordering = JourneyContentSetupOrdering.objects.filter(
            content_setup=content_setup, is_active=True)
        return render(request, "channel/sign-lite-preview-page.html", {
            "ordering": ordering,
            "content_setup": content_setup
        })


@login_required
def check_journey_exist(request):
    if request.method == "POST":
        journey = journeyContentSetup.objects.filter(
            journey__id=request.POST['journey_id'],
            is_active=True,
            is_delete=False)
        if journey:
            return JsonResponse({
                "message": "Setup of this journey is already exist",
                "success": False
            })
        journey = Channel.objects.get(pk=request.POST['journey_id'])
        return JsonResponse({
            "success":
            True,
            "journey_id":
            journey.pk,
            "name":
            journey.title,
            "short_description":
            journey.short_description,
            "description":
            journey.description,
            "what_we_learn":
            journey.what_we_learn,
            "tag":
            journey.tags.split(","),
            "profle_assest_enable":
            journey.profle_assest_enable
        })


@method_decorator(login_required, name='dispatch')
class PublicAnnouncement(View):
    model = PublicProgramAnnouncement
    template_name = "channel/create-public-announcement.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        journey = Channel.objects.get(pk=request.POST['journey'])
        company = Company.objects.get(pk=request.POST['company'])
        journey_group = None
        skill_id = None
        topic_id = request.POST.get('topic_id', '')
        cover_image = request.FILES['cover_image']
        type = request.POST['type']
        topic = request.POST['topic']
        summary = request.POST['summary']
        if type == "MicroSkill":
            if journey.channel_type == "MentoringJourney" or journey.channel_type == "SelfPaced":
                mentoring_journey = MentoringJourney.objects.get(
                    journey=journey,
                    meta_key="quest",
                    value=topic_id,
                    is_delete=False)
                journey_group = mentoring_journey.journey_group.pk
            elif journey.channel_type == "SkillDevelopment":
                channel_content = ChannelGroupContent.objects.filter(
                    content__id=topic_id, is_delete=False).first()
                if channel_content:
                    journey_group = channel_content.channel_group.pk
                    skill_id = channel_content.channel_group.channel.pk
            else:
                channel_content = ChannelGroupContent.objects.filter(
                    content__id=topic_id, is_delete=False).first()
                if channel_content:
                    journey_group = channel_content.channel_group.pk
        self.model.objects.create(company=company,
                                  journey=journey,
                                  topic=topic,
                                  topic_id=topic_id,
                                  cover_image=cover_image,
                                  channel_group=journey_group,
                                  skill_id=skill_id,
                                  summary=summary,
                                  type=type,
                                  created_by=self.request.user,
                                  announce_date=datetime.now())

        journey_users = UserChannel.objects.filter(Channel=journey,
                                                   status='Joined',
                                                   is_removed=False,
                                                   is_alloted=True)
        for joureny_user in journey_users:
            description = f"""Hi {joureny_user.user.first_name} {joureny_user.user.last_name}!
                            There has been a new item added in the carousel of {journey.title} Go check out what's new!"""

            context = {
                "screen": "Carousell",
            }
            send_push_notification(joureny_user.user, 'Carousell', description,
                                   context)
        return redirect('content:public_announcement_list')


@method_decorator(login_required, name='dispatch')
class PublicAnnouncementList(ListView):
    model = PublicProgramAnnouncement
    context_object_name = 'announcements'
    template_name = 'channel/public-announcement-list.html'

    def get_queryset(self):
        return public_announcement_list()


@method_decorator(login_required, name='dispatch')
class EditPublicAnnouncement(View):
    model = PublicProgramAnnouncement
    template_name = "channel/create-public-announcement.html"

    def get(self, request, *args, **kwargs):
        announcement = self.model.objects.get(pk=self.kwargs['pk'])
        return render(request, self.template_name,
                      {"announcement": announcement})

    def post(self, request, *args, **kwargs):
        journey = Channel.objects.get(pk=request.POST['journey'])
        company = Company.objects.get(pk=request.POST['company'])
        topic_id = request.POST.get('topic_id', '')
        type = request.POST['type']
        topic = request.POST['topic']
        summary = request.POST['summary']
        self.model.objects.filter(pk=self.kwargs['pk']).update(
            company=company,
            journey=journey,
            topic=topic,
            topic_id=topic_id,
            summary=summary,
            type=type,
            announce_date=datetime.now())
        return redirect('content:public_announcement_list')


@login_required
def update_public_announcement(request, pk):
    if request.method == 'GET':
        try:
            public_announcement = PublicProgramAnnouncement.objects.get(id=pk)
        except PublicProgramAnnouncement.DoesNotExist:
            return JsonResponse({"success": False})
        public_announcement.is_active = not public_announcement.is_active
        public_announcement.save()
        print(public_announcement.is_active)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@method_decorator(login_required, name='dispatch')
class UserActivityDetail(View):

    def get(self, request, activity_id, user_type):
        context = {"activity_id": activity_id, "user_type": user_type}
        return render(request, 'channel/user_activity_detail.html', context)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name="dispatch")
class AllActivity(View):

    def get(self, request):
        return render(request, 'channel/all_activity_list.html')

@method_decorator(login_required, name='dispatch')
@method_decorator(admin_only, name='dispatch')
class AddCertificate(View):
    model = CertificateTemplate
    template_name = "channel/create-certificate.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        print("request.POST: ", request.POST)
        title = request.POST['title']
        journey = Channel.objects.get(pk=request.POST['journey'])
        company = Company.objects.get(pk=request.POST['company'])
        if not self.model.objects.filter(journey=journey).exists():
            Certificate_for = request.POST['Certificate_for']
            file = request.FILES['file']
            # role = request.POST['role']
            from_date = request.POST['from_date']
            till_date = request.POST['till_date']
            manager = request.POST['manager']
            mentee = request.POST['mentee']
            mentor = request.POST['mentor']
            role = {
                "Learner": mentee,
                "Mentor": mentor,
                "ProgramManager": manager
            }

            # print("ROLE:", role)

            certificate = self.model.objects.create(
                title=title,
                journey=journey,
                Certificate_for=Certificate_for,
                company=company,
                file=file,
                role=role,
                journey_title=journey.title,
                from_till_date=f"{from_date} - {till_date}")

            authorizer = [
                request.POST.getlist('authorizer_name[]'),
                request.POST.getlist('authorizer_headline[]'),
                request.FILES.getlist('authorizer_sign[]')
            ]

            # print(f"name: {authorizer[0]}, headline: {authorizer[1]}, signature: {authorizer[2]}")

            for i in range(len(authorizer[2])):
                print(
                    f"name: {authorizer[0][i]}, headline: {authorizer[1][i]}, signature: {authorizer[2][i]}"
                )
                authorizer_name = authorizer[0][i]
                authorizer_headline = authorizer[1][i]
                authorizer_sign = authorizer[2][i]
                CertificateSignature.objects.create(
                    sign=authorizer_sign,
                    name=authorizer_name,
                    headline=authorizer_headline,
                    certificate_template=certificate)
            return redirect('content:certificate_list')
        else:
            messages.error(request,
                           f"Certificate for {journey.title} already exixts!")
            return redirect('content:create_certificate')


@method_decorator(login_required, name='dispatch')
class CertificateList(ListView):
    model = CertificateTemplate
    context_object_name = "certificate_templates"
    success_url = reverse_lazy('content:certificate_list')
    template_name = "channel/certificate-template-list.html"

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_delete=False)


class UpdateCertificate(View):
    model = CertificateTemplate
    template_name = "channel/update-certificate-details.html"

    def get(self, request, *args, **kwargs):
        certificate_data = self.model.objects.get(
            id=self.kwargs['certificate_id'])
        from_date = certificate_data.from_till_date.split(" ")[0]
        till_date = certificate_data.from_till_date.split(" ")[2]
        authorizers_data = CertificateSignature.objects.filter(
            certificate_template=certificate_data)
        return render(
            request, self.template_name, {
                "certificate_data": certificate_data,
                "authorizers_data": authorizers_data,
                "from_date": from_date,
                "till_date": till_date
            })

    def post(self, request, *args, **kwargs):
        title = request.POST['title']
        journey = Channel.objects.get(pk=request.POST['journey'])
        company = Company.objects.get(pk=request.POST['company'])
        Certificate_for = request.POST['Certificate_for']
        file = request.FILES.get('file', '')
        role = request.POST['role']
        from_date = request.POST['from_date']
        till_date = request.POST['till_date']

        certificate = self.model.objects.filter(
            id=self.kwargs['certificate_id'])
        certificate.update(title=title,
                           journey=journey,
                           Certificate_for=Certificate_for,
                           company=company,
                           role=role,
                           journey_title=journey.title,
                           from_till_date=f"{from_date} - {till_date}")
        if file:
            certificate.update(file=file)
        authorizer = [
            request.POST.getlist('authorizer_name[]'),
            request.POST.getlist('authorizer_headline[]'),
            request.FILES.getlist('authorizer_sign[]')
        ]
        for i in range(len(authorizer[0])):
            authorizer_name = authorizer[0][i]
            authorizer_headline = authorizer[1][i]
            authorizer_sign = authorizer[2][i]
            CertificateSignature.objects.filter(
                certificate_template=certificate.first()).update(
                    sign=authorizer_sign,
                    name=authorizer_name,
                    headline=authorizer_headline)
        return redirect('content:certificate_list')
