from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls.base import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from apps.utils.forms import IndustryForm, JourneyCategoryForm, PoolForm, TagsForm

from apps.utils.models import EmailStatusList, JourneyCategory, Tags, Industry
from apps.mentor.models import Pool, PoolMentor
from apps.users.models import Mentor
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.views import View
from apps.utils.utils import url_shortner
import os
from ravinsight.settings.base import BASE_DIR
from django.http import HttpResponse
from django.views.generic import TemplateView
import mimetypes


# Create your views here.
@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class Category(CreateView, ListView):
    model = JourneyCategory
    form_class = JourneyCategoryForm
    success_url = reverse_lazy('utils:category')
    template_name = "config/category.html"
    context_object_name = "categorys"

    def get_queryset(self):
        return JourneyCategory.objects.all()


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class TagsView(CreateView, ListView):
    model = Tags
    form_class = TagsForm
    success_url = reverse_lazy('utils:tags')
    template_name = "config/tags.html"
    context_object_name = "tags"

    def get_queryset(self):
        return Tags.objects.all()


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class IndustryView(CreateView, ListView):
    model = Industry
    form_class = IndustryForm
    success_url = reverse_lazy('utils:industry')
    template_name = "config/industry.html"
    context_object_name = "industry"

    def get_queryset(self):
        return Industry.objects.all()


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class PoolView(CreateView, ListView):
    model = Pool
    form_class = PoolForm
    success_url = reverse_lazy('utils:pool')
    template_name = "config/pool.html"
    context_object_name = "pool"

    def get_queryset(self):
        return Pool.objects.filter(is_active=True)

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user.pk
        f.save()
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class UpdatePool(UpdateView):
    '''
        Update Pool to database.
    '''
    model = Pool
    form_class = PoolForm
    template_name = "config/edit_pool.html"

    def get_success_url(self):
        if self.request.session['user_type'] == "ProgramManager":
            return reverse_lazy('program_manager:setup')
        return reverse_lazy('utils:pool')


def DeletePool(request, *args, **kwargs):
    if request.method == 'POST':
        Pool.objects.filter(id=request.POST['pk']).update(is_active=False)
        return redirect(reverse('utils:pool'))


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class Matching(ListView):
    model = Mentor
    # form_class = PoolForm
    success_url = reverse_lazy('utils:matching')
    template_name = "config/matching.html"
    context_object_name = "users"

    def get_queryset(self):
        pools = Pool.objects.filter(is_active=True)
        mentors = Mentor.objects.filter(is_active=True, is_delete=False)
        mentors_with_pool = []
        for mentor in mentors:
            # print(PoolMentor.objects.filter(mentor=mentor).values('pool__name').first()['pool__name'])
            mentors_with_pool.append([mentor, PoolMentor.objects.filter(mentor=mentor)])
        # print(mentors_with_pool, pools)
        for pool in pools:
            print(pool.id, type(pool.id))

        return mentors_with_pool, pools

    def post(self, request):
        # print("Matching post")
        # import pdb; pdb.set_trace()
        pools = Pool.objects.all()
        pool_id = request.POST['pool_select']
        pool_id = Pool.objects.get(id=pool_id)
        poolmentors = PoolMentor.objects.filter(pool_id=pool_id.id)
        # print(poolmentors)

        mentors_with_pool = []
        for poolmentor in poolmentors:
            # mentor = Mentor.objects.filter(id=poolmentor.mentor.id).first()
            mentors_with_pool.append([poolmentor.mentor, PoolMentor.objects.filter(mentor=poolmentor.mentor)])

        return render(request, 'config/matchingdelete.html', {
            "users": (mentors_with_pool, pools, pool_id)})

# @method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")'


@login_required
def add_mentor_pool(request):
    # print("add_mentor_pool")
    if request.method == 'POST':
        pool_id = request.POST['pool_name']
        action_type = request.POST['action_type']
        pool = Pool.objects.filter(id=pool_id).first()
        for id in request.POST.getlist('id'):
            # import pdb; pdb.set_trace()
            mentor = Mentor.objects.filter(username=id).first()
            if action_type == 'add':
                poolmentorr = PoolMentor.objects.filter(pool=pool, mentor=mentor).first()
                if not poolmentorr:
                    p = PoolMentor(pool=pool, mentor=mentor)
                    p.save()
                else:
                    print('already exist')
            else:
                p = PoolMentor.objects.filter(pool=pool, mentor=mentor)
                p.delete()
    else:
        print('try again')

    return HttpResponseRedirect(reverse('utils:matching'))

# @method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")


@login_required
def update_mentor_pool(request):
    if request.method == 'POST':
        username = request.POST['username']
        mentor = Mentor.objects.filter(username=username).first()
        if mentor:
            PoolMentor.objects.filter(mentor=mentor).delete()
            for id in request.POST.getlist('pool_records'):
                pool = Pool.objects.filter(id=id).first()
                p = PoolMentor(pool=pool, mentor=mentor)
                p.save()
        else:
            print('no record found')
    else:
        print('try again')
    return HttpResponseRedirect(reverse('utils:matching'))


@method_decorator(login_required, name='dispatch')
class UserEmailStatus(ListView):
    model = EmailStatusList
    context_object_name = "all_mail"
    template_name = "config/email_list.html"
    success_url = reverse_lazy('utils:email_list')


# @method_decorator(login_required, name='dispatch')
class UrlShortnerView(View):
    def get(self, request):
        return render(request, "config/url_shortner.html")

    def post(self, request):
        print("Full Url", request.POST['long_url'])
        short_url = url_shortner(request.POST['long_url'], request.build_absolute_uri('/')[:-1])
        # short_url = url_shortner(request.POST['long_url'])
        print("Short Url", short_url)
        context = {
            "short_url" : short_url
        }
        return render(request, "config/url_shortner.html", context)
    
# @method_decorator(login_required, name='dispatch')
class LogFileView(View):
    def get(self, request):
        logs_folder = f"{str(BASE_DIR)}/logs/web/"
        log_files = [f for f in os.listdir(logs_folder) if os.path.isdir(os.path.join(logs_folder, f))]
        return render(request, "config/log_file.html", {'log_files': log_files})
    
def logs_view(request, folder_name):
    file_path = f"{str(BASE_DIR)}/logs/web/{folder_name}/debug.log"
    print("file_path",file_path)

    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'inline; filename="debug.log"'
        return response

class FileView(TemplateView):
    template_name = 'config/log_file_detail.html'

    def get_context_data(self, **kwargs):
        folder_name = kwargs.get('folder_name')
        file_path = f"{str(BASE_DIR)}/logs/web/{folder_name}/debug.log"

        with open(file_path, 'r') as file:
            file_content = file.read()

        content_type, encoding = mimetypes.guess_type(file_path)
        return {'file_content': file_content, 'content_type': content_type or 'text/plain'}
