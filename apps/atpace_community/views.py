from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View
from apps.users.models import User
from apps.atpace_community.utils import random_string, send_invite_user_mail
from apps.users.views import check_check_box

from .forms import InviteForm, SpaceForm, SpaceGroupForm, SpaceMemberForm
from .models import MemberInvitation, Report, SpaceGroups, SpaceMembers, Spaces, ContentToReview
from apps.atpace_community.utils import avatar, replace_links_with_anchor_tags
import re

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class GroupSpace(CreateView, ListView):
    model = SpaceGroups
    form_class = SpaceGroupForm
    success_url = reverse_lazy('atpace_community:group_space')
    template_name = "admin/create-space-group.html"
    context_object_name = "spacegroup"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super().form_valid(form)

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_delete=False)


def delete_group_space(request):
    if request.method == "POST":
        space_id = request.POST['id']
        SpaceGroups.objects.filter(id=space_id).update(is_delete=True, is_active=False)
        return redirect(reverse('atpace_community:group_space'))

@method_decorator(login_required, name='dispatch')
class CreateSpace(CreateView):
    model = Spaces
    form_class = SpaceForm
    success_url = reverse_lazy('atpace_community:space_list')
    template_name = "admin/create-space.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        SpaceMembers.objects.create(user=self.request.user, space=f, space_group=f.space_group,
                                    is_joined=True, email=self.request.user.email, invitation_status="Accept", user_type="Admin")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class ListSpace(ListView):
    model = Spaces
    context_object_name = "spaces"
    template_name = "admin/space-list.html"

    def get_queryset(self):
        return self.model.objects.filter(is_delete=False, is_active=True)


def delete_space(request):
    if request.method == "POST":
        space_id = request.POST['id']
        Spaces.objects.filter(id=space_id).update(is_delete=True, is_active=False)
        return redirect(reverse('atpace_community:space_list'))


class EditSpace(UpdateView):
    model = Spaces
    form_class = SpaceForm
    template_name = "admin/create-space.html"

    def get_success_url(self) -> str:
        if self.request.session['user_type'] == "ProgramManager":
            return reverse_lazy('program_manager:setup')
        return reverse_lazy('atpace_community:space_list')

@method_decorator(login_required, name='dispatch')
class SpaceMemberList(ListView):
    model = SpaceMembers
    template_name = "admin/space-member.html"
    context_object_name = "spacemember"

@method_decorator(login_required, name='dispatch')
class CreateSpaceMember(View):
    model = SpaceMembers
    template_name = "admin/create-space-member.html"

    def get(self, request):
        user_list = User.objects.filter(is_active=True, is_delete=False)
        space_group_list = SpaceGroups.objects.filter(is_active=True, is_delete=False)
        return render(request, self.template_name, {"users": user_list, "space_groups": space_group_list})

    def post(self, request, *args, **kwargs):
        user_list = self.request.POST.getlist('user')
        space_list = self.request.POST.getlist('space')
        user_type = self.request.POST['user_type']
        space_group = SpaceGroups.objects.get(id=self.request.POST['space_group'])
        for id in user_list:
            user = User.objects.get(pk=id)
            for space_id in space_list:
                space = Spaces.objects.get(id=space_id)
                if not SpaceMembers.objects.filter(user=user, space=space).exists():
                    SpaceMembers.objects.create(user=user, space=space, space_group=space_group, is_joined=True,
                                                email=user.email, invitation_status="Accept", user_type=user_type)
                elif not SpaceMembers.objects.filter(user=user, space=space, is_joined=True).exists():
                    SpaceMembers.objects.filter(user=user, space=space).update(
                        is_active=True, is_delete=False, is_joined=True)
        return redirect('atpace_community:space_member_list')


def delete_space_member(request):
    if request.method == "POST":
        member_id = request.POST['id']
        SpaceMembers.objects.filter(id=member_id).update(is_delete=True, is_active=False)
        return redirect(reverse('atpace_community:space_member_list'))


def get_spacegroup_space(request):
    spaces = Spaces.objects.filter(space_group__in=[request.GET['space_group']], is_active=True, is_delete=False)
    space_list = []
    for space in spaces:
        space_list.append({
            "id": space.pk,
            "title": space.title
        })
    context = {
        "space_list": space_list
    }
    return JsonResponse(context)


class EditSpaceMember(UpdateView):
    model = SpaceMembers
    form_class = SpaceMemberForm
    success_url = reverse_lazy('atpace_community:space_member_list')
    template_name = "admin/edit-member.html"

@method_decorator(login_required, name='dispatch')
class ListReport(ListView):
    model = Report
    context_object_name = "post_reports"
    template_name = "admin/post-report-record.html"

    def get_queryset(self):
        return self.model.objects.filter(is_report=True)

@method_decorator(login_required, name='dispatch')
class EditSpaceGroup(UpdateView):
    model = SpaceGroups
    form_class = SpaceGroupForm
    success_url = reverse_lazy('atpace_community:group_space')
    template_name = "admin/create-space-group.html"

    def get_success_url(self) -> str:
        if self.request.session['user_type'] == "ProgramManager":
            return reverse_lazy('program_manager:setup')
        return reverse_lazy('atpace_community:group_space')

@method_decorator(login_required, name='dispatch')
class InvitationList(CreateView, ListView):
    model = MemberInvitation
    form_class = InviteForm
    success_url = reverse_lazy('atpace_community:invite_list')
    context_object_name = "invitation"
    template_name = "admin/member-invitation.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.invited_by = self.request.user
        f.invite_by_id = self.request.user.id
        f.string = random_string()
        # send_invite_user_mail(self.request.user, f.invite_email)
        f.status = True
        f.save()
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class ContentReviewList(ListView):
    model = ContentToReview
    context_object_name = "review_contents"
    template_name = "admin/review-content-list.html"

@method_decorator(login_required, name='dispatch')
class ContentReview(View):
    model = ContentToReview

    def get(self, request, *args, **kwargs):
        review_content = self.model.objects.get(id=self.kwargs['review_content_id'])
        content = review_content.post.Body if review_content.posted_on == "Post" else review_content.comment.Body
        content = replace_links_with_anchor_tags(content) if ('<p>http' in content) or (
            re.search("(^https?://[^\s]+)", content)) else content
        print(f"inappropriate_content: {review_content.profanity_words}")
        response = {
            "id": review_content.id,
            "title": review_content.title,
            "content": content,
            "is_reviewed": review_content.is_reviewed,
            "post_on_community": review_content.post_on_community,
            "inappropriate_content": review_content.profanity_words,
            "user_name": f"{review_content.user.get_full_name()}",
            "user_id": review_content.user.id,
            "post_title": review_content.post.title,
            "user_avatar": avatar(review_content.user),
            "post_created_at": review_content.post.created_at,
        }
        return render(request, "admin/review-content.html", response)

    def post(self, request, *args, **kwargs):
        try:
            post_on_community = check_check_box(request.POST['post_on_community'])
        except Exception:
            post_on_community = False
        review_content = self.model.objects.filter(id=self.kwargs['review_content_id'])
        review_content.update(
            post_on_community=post_on_community, is_reviewed=True, reviewed_by=self.request.user
        )
        if post_on_community:
            review_content = review_content.first()
            obj = review_content.post if review_content.posted_on == "Post" else review_content.comment
            obj.inappropriate_content = False
            obj.save()
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:manage')
        else:
            return redirect('atpace_community:content_review_list')
