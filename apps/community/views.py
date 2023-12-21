from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from apps.atpace_community.models import Attachments
from apps.atpace_community.utils import community_post_Comment, create_community_post, get_community_space_post, \
    get_community_space_post_comment, get_community_space_post_details
from apps.community.forms import WeeklyjournalsTemplateFrom
from apps.community.models import CommunityPost, CommunityPostComment, LearningJournals, LearningJournalsAttachment, \
    LearningJournalsComments, WeeklyLearningJournals, WeeklyjournalsTemplate
from apps.community.utils import check_user_accept_invite, create_post, get_files, get_space_post, \
    get_space_post_comment, get_space_post_details, post_Comment, journal_push_notification
from apps.content.models import Channel, ChannelGroup, Content
from apps.content.utils import is_parent_channel
from apps.mentor.models import AssignMentorToUser, PoolMentor
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView
)
from apps.users.models import User
from django.urls import reverse_lazy
from apps.leaderboard.views import CheckEndOfJourney, send_push_notification
from apps.users.templatetags.tags import journey_by_id
from apps.content.utils import company_journeys
from django.db.models.query_utils import Q
# Create your views here.


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class AskKeyPoint(View):

    def get(self, request, **kwargs):
        get_content = Content.objects.get(pk=self.kwargs['content'])
        channel_group = ChannelGroup.objects.get(pk=self.kwargs['group'])
        channel = Channel.objects.get(pk=channel_group.channel.pk)
        parent_check = is_parent_channel(channel.pk)
        learning_journals = LearningJournals.objects.filter(
            journey_id=parent_check['channel_id'], microskill_id=self.kwargs['content'],
            email=request.user.email).first()
        context = {
            "content": get_content,
            "learning_journals": learning_journals,
            "group": channel_group
        }
        return render(request, 'community/ask_key_points.html', context)

    def post(self, request, **kwargs):
        if not request.POST['key_pont']:
            messages.error(request, "Key Points are required!")
            return redirect(
            reverse('community:ask_key_point', kwargs={'content': self.kwargs['content'], 'group': self.kwargs['group']}))
        content = Content.objects.get(pk=self.kwargs['content'])
        channel_group = ChannelGroup.objects.get(pk=self.kwargs['group'])
        channel = Channel.objects.get(pk=channel_group.channel.pk)
        channel = is_parent_channel(channel.pk)['channel']
        microskill_id = self.kwargs['content']
        title = content.title
        body = request.POST['key_pont']
        type = "KeyPoints"
        # create_post(request.user, channel, title, body, type, microskill_id)
        create_community_post(request.user, channel, title, body, type)
        return redirect(
            reverse('content:thank_you', kwargs={'content': self.kwargs['content'], 'group': self.kwargs['group']}))


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class AskQuestion(View):
    def post(self, request, **kwargs):
        channel = Channel.objects.get(pk=request.POST['journey'])
        microskill_id = request.POST['content']
        title = request.POST['title']
        body = request.POST['description']
        type = "AskQuestions"
        # print(request.user, community_id, space_id, title, body)
        # create_post(request.user, channel, title, body, type, microskill_id)
        create_community_post(request.user, channel, title, body, type)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class AddLearningJournal(View):
    def post(self, request, **kwargs):
        microskill_id = request.POST['content']
        learning_journal = request.POST['learning_journal']
        content = Content.objects.get(pk=microskill_id)
        name = f"{content.title}- Learning Journal"
        user_name = f"{request.user.first_name} {request.user.last_name}"
        files = self.request.FILES.getlist('file')

        if request.POST['learning_journal_id'] == "":

            learning_journal_create = LearningJournals.objects.create(name=name, user_name=user_name,
                                                                      user_id=request.user.pk, email=request.user.email,
                                                                      learning_journal=learning_journal,
                                                                      microskill_id=microskill_id,
                                                                      journey_id=request.POST['journey'])
            get_files(files, learning_journal_create)

            journal_push_notification(request.user, request.POST['journey'], name, 'Learning')

        else:

            learning_journals = LearningJournals.objects.filter(pk=request.POST['learning_journal_id']).update(
                learning_journal=learning_journal)
            get_files(files, learning_journals)
        messages.success(request, 'Saved')
        response = redirect(reverse('content:read_content', kwargs={
            'pk': request.POST['content'], 'group': request.POST['group']}) + "?page=" + request.POST['card_id'])

        return response


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class JourneyPost(View):
    def get(self, request, **kwargs):
        channel = Channel.objects.get(pk=self.kwargs['channel'])
        # if check_accept_status := check_user_accept_invite(request.user, channel):
        #     if channel.is_community_required:
        #         space_id = channel.journryspace.space_id
        #         community_id = channel.journryspace.community_id
        #         # data = get_space_post(community_id, space_id)
        data = get_community_space_post(channel, request.user)
        print(data)
        # else:
        #     data = CommunityPost.objects.filter(journey=channel, user_email=request.user.email)
        context = {
            "data": data,
            "channel": channel,
            "type": "community",
            "success": True
        }
        # else:
        #     context = {
        #         "message":"user Status disable",
        #         "success":False,
        #     }
        return render(request, 'community/post.html', context)


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class LearningJournal(View):
    def get(self, request, **kwargs):
        channel = Channel.objects.get(pk=self.kwargs['channel'])
        data = LearningJournals.objects.filter(
            journey_id=channel.pk, email=request.user.email)
        output_data = []
        for learning_jouranl in data:
            comments = LearningJournalsComments.objects.filter(
                learning_journal=learning_jouranl).order_by("-created_at")
            print(comments)
            output_data.append({
                "data": learning_jouranl,
                "comment": comments,
            })
        context = {
            "data": output_data,
            "channel": channel,
            "type": "learning_journal",
        }
        return render(request, 'community/all_learning_journal.html', context)


@method_decorator(login_required, name='dispatch')
class AllLearningJournal(View):
    def get(self, request, **kwargs):
        output_data = []
        if request.session['user_type'] == "Learner":
            data = LearningJournals.objects.filter(
                email=request.user.email, is_weekly_journal=False).order_by("-created_at")
            print(data)
            for learning_jouranl in data:
                comments = LearningJournalsComments.objects.filter(
                    learning_journal=learning_jouranl).order_by("-created_at")
                print(comments)
                output_data.append({
                    "data": learning_jouranl,
                    "comment": comments
                })
        else:
            user = []
            journey = []
            data = []
            user_list = AssignMentorToUser.objects.filter(mentor=request.user)
            for user_list in user_list:
                user.append(user_list.user.email)
                journey.append(str(user_list.journey.id))
            print(journey)
            print(user)
            data = LearningJournals.objects.filter(
                email__in=user, journey_id__in=journey, is_weekly_journal=False).order_by("-created_at")
            print(data)
            for learning_jouranl in data:
                comments = LearningJournalsComments.objects.filter(
                    learning_journal=learning_jouranl).order_by("-created_at")
                output_data.append({
                    "data": learning_jouranl,
                    "comment": comments
                })
        context = {
            "data": output_data,
            "type": "learning_journal"
        }
        return render(request, 'community/all_learning_journal.html', context)


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class JourneyPostDetails(View):
    def get(self, request, **kwargs):
        channel = Channel.objects.get(pk=self.kwargs['channel'])

        # if channel.is_community_required:
        #     space_id = channel.journryspace.space_id
        #     community_id = channel.journryspace.community_id
        print("post_id channel_id", self.kwargs['post_id'], self.kwargs['channel'])
        data = get_community_space_post_details(channel, self.kwargs['post_id'])
        print(data)
        # data = get_space_post_details(community_id, self.kwargs['post_id'])
        comment = get_community_space_post_comment(channel, self.kwargs['post_id'])
        # comment = get_space_post_comment(community_id, space_id, self.kwargs['post_id'])
        # else:

        #     data = CommunityPost.objects.get(id=self.kwargs['post_id'])

        #     comment = CommunityPostComment.objects.filter(community_post=data)

        context = {
            "data": data,
            "channel": channel,
            "comment": comment
        }
        return render(request, 'community/post_details.html', context)


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class PostAnswer(View):
    def post(self, request, **kwargs):
        channel = Channel.objects.get(pk=request.POST['channel'])

        post_id = request.POST['post_id']
        body = request.POST['answer']
        # post_Comment(channel, post_id, body, request.user)
        community_post_Comment(channel, post_id, body, request.user)

        return redirect(reverse('community:journey_post_details', kwargs={'channel': channel.pk, 'post_id': post_id}))


@method_decorator(login_required, name='dispatch')
class WeekelyJournals(View):
    def get(self, request, **kwargs):
        learning_journals = WeeklyLearningJournals.objects.get(pk=self.kwargs['pk'])
        context = {
            "learning_journals": learning_journals
        }
        return render(request, 'community/weekly_journals.html', context)

    def post(self, request, **kwargs):
        print(request.POST)
        template = WeeklyLearningJournals.objects.get(pk=self.kwargs['pk'])
        user_name = f"{request.user.first_name} {request.user.last_name}"
        body = request.POST['key_pont']
        files = self.request.FILES.getlist('file')
        learning_journals = LearningJournals.objects.create(name=template.name, user_name=user_name,
                                                            user_id=request.user.id, email=request.user.email,
                                                            learning_journal=body,
                                                            journey_id=template.journey_id, is_weekly_journal=True,
                                                            weekely_journal_id=self.kwargs['pk'])
        print("learning_journals_id ", learning_journals.id)
        get_files(files, learning_journals)
        CheckEndOfJourney(request.user, template.journey_id, userType=request.session['user_type'])
        # channel = Channel.objects.get(id=template.journey_id)
        # type = "WeeklyJournal"
        if "save_draft" in request.POST:
            learning_journals.is_draft = True
            learning_journals.save()
        if not learning_journals.is_draft:
            assign_user = AssignMentorToUser.objects.filter(journey__id=template.journey_id, user=request.user).first()
            if assign_user:
                context = {
                    "screen": "JournalDetail",
                    "navigationPayload":{
                        "journey_id": str(template.journey_id),
                        "journal_id": str(learning_journals.id),
                        "notification_for": ""
                    }
                }
                send_push_notification(assign_user.mentor, template.name, f"Journal submitted by {request.user.first_name} {request.user.last_name}", context)
        # create_community_post(request.user, channel, template.name, body, type)
        return redirect(reverse('content:Channel_content_v2', kwargs={'Channel': template.journey_id}))


@method_decorator(login_required, name='dispatch')
class EditWeeklyJournals(View):
    def get(self, request, **kwargs):

        learning_journals = LearningJournals.objects.get(pk=self.kwargs['id'])
        attachment = LearningJournalsAttachment.objects.filter(post=learning_journals)
        context = {
            "learning_journals": learning_journals,
            "attachments": attachment
        }
        return render(request, 'community/weekly_journals.html', context)

    def post(self, request, **kwargs):
        learning_journals = LearningJournals.objects.get(pk=self.kwargs['id'])
        learning_journals.learning_journal = request.POST['key_pont']
        files = self.request.FILES.getlist('file')
        get_files(files, learning_journals)

        if "save_draft" in request.POST:
            learning_journals.is_draft = True
        elif "submit_content" in request.POST:
            learning_journals.is_draft = False
            journal_push_notification(request.user, learning_journals.journey_id, learning_journals.name, 'Weekly')

        learning_journals.save()

        return redirect(reverse('content:Channel_content_v2', kwargs={'Channel': learning_journals.journey_id}))


@method_decorator(login_required, name='dispatch')
class AllWeeklyJournals(View):
    def get(self, request, *args, **kwargs):
        weekelyjournals = LearningJournals.objects.filter(
            email=request.user.email, is_draft=False, is_weekly_journal=True).order_by("-created_at")
        output_data = []
        if request.session['user_type'] == "Learner":
            for data in weekelyjournals:
                attachments = LearningJournalsAttachment.objects.filter(post=data)
                comments = LearningJournalsComments.objects.filter(learning_journal=data).order_by("-created_at")
                output_data.append({
                    "data": data,
                    "comment": comments,
                    "attachments": attachments
                })
        else:
            user = []
            journey = []
            data = []
            user_list = AssignMentorToUser.objects.filter(mentor=request.user)
            for user_list in user_list:
                user.append(user_list.user.email)
                journey.append(str(user_list.journey.id))
            print(journey)
            print(user)
            data = LearningJournals.objects.filter(
                email__in=user, journey_id__in=journey, is_weekly_journal=True, is_draft=False).order_by("-created_at")
            print(data)
            for learning_jouranl in data:
                attachments = LearningJournalsAttachment.objects.filter(post=learning_jouranl)
                comments = LearningJournalsComments.objects.filter(
                    learning_journal=learning_jouranl).order_by("-created_at")
                output_data.append({
                    "data": learning_jouranl,
                    "comment": comments,
                    "attachments": attachments
                })
        return render(request, "community/all_learning_journal.html", {"data": output_data})


@method_decorator(login_required, name='dispatch')
class AllWeeklyJournalsList(View):
    def get(self, request, *args, **kwargs):
        weekelyjournals = LearningJournals.objects.filter(email=request.user.email, is_weekly_journal=True,
                                                          is_draft=False).order_by(
            "-created_at")
        output_data = []
        if request.session['user_type'] == "Learner":
            for data in weekelyjournals:
                comments = LearningJournalsComments.objects.filter(learning_journal=data).order_by("-created_at")
                output_data.append({
                    "data": data,
                    "comment": comments
                })
        else:
            user = []
            journey = []
            data = []
            user_list = AssignMentorToUser.objects.filter(mentor=request.user)
            for user_list in user_list:
                user.append(user_list.user.email)
                journey.append(str(user_list.journey.id))
            print(journey)
            print(user)
            data = LearningJournals.objects.filter(
                email__in=user, journey_id__in=journey, is_weekly_journal=True, is_draft=False).order_by("-created_at")
            for learning_jouranl in data:
                comments = LearningJournalsComments.objects.filter(
                    learning_journal=learning_jouranl).order_by("-created_at")
                output_data.append({
                    "data": learning_jouranl,
                    "comment": comments
                })
        return render(request, "community/all_weekly_journal_list.html", {"data": output_data})


@method_decorator(login_required, name='dispatch')
class CreateJournalTemplates(CreateView):
    model = WeeklyjournalsTemplate
    form_class = WeeklyjournalsTemplateFrom
    success_url = reverse_lazy('community:create_journal_template')
    template_name = "community/weekly_journals_template.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user.pk
        f.save()
        return super(CreateJournalTemplates, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
class JournalTemplateslList(ListView):
    model = WeeklyjournalsTemplate
    context_object_name = "templates"
    template_name = "community/templates_list.html"


@method_decorator(login_required, name='dispatch')
class JournalTemplateslUpdate(UpdateView):
    model = WeeklyjournalsTemplate
    form_class = WeeklyjournalsTemplateFrom
    success_url = reverse_lazy('community:create_journal_template')
    template_name = "community/weekly_journals_template.html"


@login_required
def delete_attachment(request, attachment_id):
    attachment = LearningJournalsAttachment.objects.filter(id=attachment_id)
    id = attachment.first().post.id
    attachment.delete()
    return HttpResponse('Success')
    # return redirect(reverse('community:edit_weekly_journals', kwargs={"id":id}))


@method_decorator(login_required, name='dispatch')
class AllJournal(View):
    def get(self, request, pk=None, **kwargs):
        output_data = []
        learning_journal = []
        private_journal = []
        weekly_learning_journal = []
        journeys = company_journeys(request.session['user_type'], request.user, request.session['company_id'])
        journey_id_list = []
        for journey in journeys:
            journey_id_list.append(journey.id)
        if request.session['user_type'] == "Learner":
            # if request.session.get('company_id'):
            data = LearningJournals.objects.filter(Q(is_private=True) | Q(
                    journey_id__in=journey_id_list), email=request.user.email, is_draft=False).order_by("-created_at")
            # else:
            #     data = LearningJournals.objects.filter(email=request.user.email, is_draft=False).order_by("-created_at")
        else:
            data = []
            user_list = []
            journey = []
            # company_journey = company_journeys(request.session['user_type'], request.user, request.session['company_id'])
            if pk is None:
                assignee_list = AssignMentorToUser.objects.filter(mentor=request.user, journey__in=journeys)
                for assignee in assignee_list:
                    # user_list.append(assignee.user.email)
                    # journey.append(str(assignee.journey.id))
                    learning_jouranls = LearningJournals.objects.filter(
                        email=assignee.user.email, journey_id=assignee.journey.id, is_draft=False,
                        is_private=False).order_by("-created_at")
                    data.extend(list(learning_jouranls))

                    mentor_journal = LearningJournals.objects.filter(email=request.user.email, is_draft=False).order_by(
                        "-created_at")
                    data.extend(list(mentor_journal))

                private = LearningJournals.objects.filter(Q(is_private=True) | Q(
                    journey_id__in=journey_id_list),email=request.user.email, is_draft=False, is_private=True, ).order_by("-created_at")
                for private in private:
                    comments = LearningJournalsComments.objects.filter(
                        learning_journal=private).order_by("-created_at")
                    private_journal.append({
                        "data": private,
                        "comment": comments
                    })
            else:
                user = User.objects.get(id=pk)
                data = LearningJournals.objects.filter(Q(is_private=True) | Q(
                    journey_id__in=journey_id_list),email=user.email, is_draft=False).order_by("-created_at")
                # assignee_list = AssignMentorToUser.objects.filter(mentor=user)
                # for assignee in assignee_list:
                #     # user_list.append(assignee.user.email)
                #     # journey.append(str(assignee.journey.id))
                #     learning_jouranls = LearningJournals.objects.filter(
                #         email=assignee.user.email, journey_id=assignee.journey.id, is_draft=False,
                #         is_private=False).order_by("-created_at")
                #     data.extend(list(learning_jouranls))
                #
                #     mentor_journal = LearningJournals.objects.filter(email=user.email, is_draft=False).order_by(
                #         "-created_at")
                #     data.extend(list(mentor_journal))
                #
                # private = LearningJournals.objects.filter(
                #     email=user.email, is_draft=False, is_private=True).order_by("-created_at")
                # for private in private:
                #     comments = LearningJournalsComments.objects.filter(
                #         learning_journal=private).order_by("-created_at")
                #     private_journal.append({
                #         "data": private,
                #         "comment": comments
                #     })

        for learning_jouranl in data:
            comments = LearningJournalsComments.objects.filter(
                learning_journal=learning_jouranl).order_by("-created_at")
            # print(comments)
            # print("type", type(learning_jouranl.user_id), type(request.user))
            if learning_jouranl.is_private == True:
                private_journal.append({
                    "data": learning_jouranl,
                    "comment": comments
                })
            elif learning_jouranl.is_weekly_journal == False:
                learning_journal.append({
                    "data": learning_jouranl,
                    "comment": comments
                })
            else:
                attachments = LearningJournalsAttachment.objects.filter(post=learning_jouranl)
                weekly_learning_journal.append({
                    "data": learning_jouranl,
                    "comment": comments,
                    "attachments": attachments
                })
        output_data = {
            "learning_journal": learning_journal,
            "weekly_learning_journal": weekly_learning_journal,
            "private_journal": private_journal,
            "user_id": str(request.user.id)
        }

        context = {
            "journal": output_data,
            "type": "Journal"
        }
        return render(request, 'community/all_journal.html', context)


@method_decorator(login_required, name='dispatch')
class PostJournal(View):
    def get(self, request, **kwargs):
        return render(request, 'community/post_journal.html')

    def post(self, request, **kwargs):
        print("request data", request.POST)
        journal_id = request.POST.get('id', '')
        name = request.POST['title']
        user_name = f"{request.user.first_name} {request.user.last_name}"
        learning_journal = request.POST.getlist('learning_journal')[0] if request.POST.getlist('learning_journal')[0] else request.POST.getlist('learning_journal')[1]
        try:
            is_private = request.POST['is_private']
        except:
            is_private = False
        try:
            is_draft = request.POST['is_draft']
        except:
            is_draft = False
        journey_id = request.POST.get('journey', '')

        if journal_id:
            print("yes journal id")
            journal = LearningJournals.objects.filter(id=journal_id).first()
            journal.learning_journal = learning_journal
            journal.is_private = is_private
            journal.journey_id = journey_id
            journal.is_draft = is_draft
            journal.name = name
            journal.save()
            if request.session['user_type'] == "Mentor":
                return redirect(reverse('mentor:mentor_learn'))
            elif request.session['user_type'] == "Learner":
                return redirect(reverse('learner:learner_learn'))
            return redirect(reverse('community:all_journal'))
        print("no journal id")
        LearningJournals.objects.create(name=name, user_name=user_name, user_id=request.user.pk,
                                        email=request.user.email, user_type=request.session['user_type'],
                                        learning_journal=learning_journal, is_private=is_private,
                                        journey_id=journey_id, is_draft=is_draft)
        if not is_private:
            journal_push_notification(request.user, request.POST['journey'], name, 'Learning')

        if request.session['user_type'] == "Mentor":
            return redirect(reverse('mentor:mentor_learn'))
        elif request.session['user_type'] == "Learner":
            return redirect(reverse('learner:learner_learn'))

        return redirect(reverse('community:post_journal'))


@method_decorator(login_required, name='dispatch')
class EditJournal(View):
    def get(self, request, **kwargs):
        user = User.objects.get(id=self.kwargs['user_id'])
        learning_journals = LearningJournals.objects.get(pk=self.kwargs['pk'])
        print("learning_journals", learning_journals)

        context = {
            "learning_journal": learning_journals,
        }
        return render(request, 'community/edit_journal.html', context)
