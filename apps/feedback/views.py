from django.shortcuts import render, redirect
from django.http.response import Http404, JsonResponse, HttpResponse
from apps.content.models import Channel, ChannelGroup, ChannelGroupContent, Content, MentoringJourney
# from apps.feedback.forms import CreateFeedbackForm
from django.urls import reverse_lazy
from apps.feedback.models import FeedbackTemplate, FeedbackTemplateQuerstion, JourneyFeedback, feedbackAnswer, UserFeedback
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView
)
from django.urls import reverse
from django.contrib import messages
from django.views import View
from apps.users.models import Company
from apps.users.views import check_check_box
from ravinsight.decorators import admin_only
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.feedback.utils import feedbackTemplateFor, get_meeting_user
import random
from ravinsight.constants import template_choice
from apps.users.models import User
from apps.mentor.models import AllMeetingDetails, MeetingParticipants
from rest_framework.permissions import AllowAny
# Create your views here.


@method_decorator(login_required, name='dispatch')
class CreateFeedbackTemplate(View):
    '''
       Redirect to the Feedback Template Page.
    '''
    model = FeedbackTemplate
    template_name = "feedback/create-feedback-template.html"
    
    def get(self, request, *args, **kwargs):
        choices = [choice[0] for choice in template_choice]
        company_list = Company.objects.all()
        context = {
            "all_company": company_list,
            "template_choice": choices
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        journey = request.POST['journey']
        name = request.POST['name']
        company = Company.objects.get(id=request.POST['company'])
        template_for = request.POST['template_for']
        short_description = request.POST['short_description']
        try:
            is_active = check_check_box(request.POST['is_active'])
        except Exception:
            is_active = False
        try:
            is_draft = check_check_box(request.POST['is_draft'])
        except Exception:
            is_draft = False
        template = self.model.objects.create(name=name, template_for=template_for,
                            short_description=short_description, is_active=is_active, is_draft=is_draft, created_by=request.user)
        journey_feedback = JourneyFeedback.objects.create(feedback_template=template, company=company, type=template_for, created_by=request.user)
        if journey != "":
            channel = Channel.objects.get(id=journey, parent_id=None, is_active=True, is_delete=False)
            journey_feedback.journey = channel
            journey_feedback.save()

        if request.session['user_type'] == "ProgramManager":
            return redirect(reverse('program_manager:setup'))
        return redirect('feedback:feedback_template_list')


@method_decorator(login_required, name='dispatch')
class FeedbackTemplateList(ListView):
    model = JourneyFeedback
    template_name = "feedback/feedback-template-list.html"
    context_object_name = "feedback_templates"

    def get_queryset(self):
        return JourneyFeedback.objects.filter(is_active=True, is_delete=False)


@method_decorator(login_required, name='dispatch')
class EditFeedbackTemplate(View):
    '''
       Redirect to the Feedback Template List Page.
    '''
    model = FeedbackTemplate
    template_name = "feedback/edit-template.html"
    
    def get(self, request, *args, **kwargs):
        choices = [choice[0] for choice in template_choice]
        company_list = Company.objects.all()
        template = self.model.objects.get(id=self.kwargs['template_id'])
        journey_feedback = JourneyFeedback.objects.filter(feedback_template=template).first()
        journey_list = Channel.objects.filter(company__in=[journey_feedback.company])
        context = {
            "all_company": company_list,
            "template_choice": choices,
            "feedback_template": template,
            "journey_feedback": journey_feedback,
            "journey_list": journey_list
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        journey = request.POST['journey']
        name = request.POST['name']
        company = Company.objects.get(id=request.POST['company'])
        template_for = request.POST['template_for']
        short_description = request.POST['short_description']
        try:
            is_active = check_check_box(request.POST['is_active'])
        except Exception:
            is_active = False
        try:
            is_draft = check_check_box(request.POST['is_draft'])
        except Exception:
            is_draft = False
        template = self.model.objects.filter(id=self.kwargs['template_id'])
        template.update(name=name, template_for=template_for,
                            short_description=short_description, is_active=is_active, is_draft=is_draft, updated_by=request.user)
        journey_feedback = JourneyFeedback.objects.filter(feedback_template=template.first())
        journey_feedback.update(company=company, type=template_for, updated_by=request.user)
        if journey != "":
            channel = Channel.objects.get(id=journey, parent_id=None, is_active=True, is_delete=False)
            journey_feedback.update(journey=channel)

        if request.session['user_type'] == "ProgramManager":
            return redirect(reverse('program_manager:setup'))
        return redirect('feedback:feedback_template_list')

@admin_only
@login_required
def delete_feedback_template(request):
    if request.method == 'POST':
        FeedbackTemplate.objects.filter(id=request.POST['template_id']).update(is_active=False, is_delete=True)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@method_decorator(login_required, name='dispatch')
class AddTemplateQuerstion(View):
    model = FeedbackTemplateQuerstion
    context_object_name = "questions"
    template_name = "feedback/add-question.html"

    def get_queryset(self):
        return FeedbackTemplateQuerstion.objects.filter(feedback_template__id=self.kwargs['template_id'], is_active=True, is_delete=False).order_by("display_order")

    def get(self, request, template_id):
        print("Hey Shru!")
        try:
            feedback_template = FeedbackTemplate.objects.get(pk=template_id, is_active=True, is_delete=False)
            return render(request, self.template_name, {"template": feedback_template, "questions": self.get_queryset})
        except FeedbackTemplate.DoesNotExist:
            raise Http404


@login_required
def update_template_question(request):
    if request.method == "POST":
        title = request.POST['title']
        type = request.POST['type']
        template_id = request.POST['template']
        try:
            is_required = request.POST['is_required']
        except Exception:
            is_required = False

        try:
            question_id = request.POST['question_id']
        except Exception:
            question_id = None
        if not question_id:
            feedback_template = FeedbackTemplate.objects.get(id=template_id)
            display_order = FeedbackTemplateQuerstion.objects.filter(
                feedback_template=feedback_template, is_active=True, is_delete=False).count()
            question = FeedbackTemplateQuerstion.objects.create(title=title, type=type, feedback_template=feedback_template,
                                                                is_required=is_required, display_order=display_order+1, created_by=request.user)
        else:
            question = FeedbackTemplateQuerstion.objects.get(id=question_id)
            question.title = title
            question.is_required = is_required
        if type in ["DropDown", "MultiChoice", "Checkbox"]:
            options = request.POST.getlist("option[]")
            question.option_list = options
        elif type == "LinearScale":
            question.start_rating_scale = request.POST['start_rating_scale']
            question.end_rating_scale = request.POST['end_rating_scale']
            question.start_rating_name = request.POST['start_rating_name']
            question.end_rating_name = request.POST['end_rating_name']
        if "ques_image" in request.FILES:
            image = request.FILES['ques_image']
            if image:
                question.image = image
        question.save()
        return redirect(f'/feedback/add-template-question/{str(template_id)}/')


@method_decorator(login_required, name='dispatch')
class CopyTemplateQuerstion(View):
    def post(self, request, **kwargs):
        obj = FeedbackTemplateQuerstion.objects.get(id=request.POST['id'])
        obj.pk = None
        obj.display_order = obj.display_order
        obj.save()
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class UpdateQuestionOrder(View):
    def post(self, request):
        order_string = request.POST['order']
        order = order_string.split(',')
        for i in range(len(order)):
            FeedbackTemplateQuerstion.objects.filter(id=order[i]).update(display_order=i)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
class TemplateQuerstionId(View):
    def post(self, request):
        questions = FeedbackTemplateQuerstion.objects.get(id=request.POST['id'])
        question = {
            'id': questions.id,
            'title': questions.title,
            'type': questions.type,
            'option_list': questions.option_list,
            'start_rating_name': questions.start_rating_name,
            'end_rating_name': questions.end_rating_name,
            'start_rating_scale': questions.start_rating_scale,
            'end_rating_scale': questions.end_rating_scale,
            'is_required': questions.is_required,
        }
        return JsonResponse(question, safe=False)


@login_required
def delete_template_question(request, template_id, pk):
    if request.method == "GET":
        FeedbackTemplateQuerstion.objects.filter(id=pk).update(is_active=False, is_delete=True)
        return redirect('/feedback/add-template-question/'+str(template_id)+'/')


@method_decorator(login_required, name='dispatch')
class FeedbackForm(View):
    def get(self, request, **kwargs):
        if 'template_for' in self.kwargs:
            template_for = self.kwargs['template_for']
            template_for_id = self.kwargs['template_for_id']
        else:
            meet_id = self.kwargs['meet_id']
            if not meet_id:
                return redirect(reverse('user:user-dashboard'))
            template_vars, response = feedbackTemplateFor(meet_id)
            if not response:
                return redirect(reverse('user:user-dashboard'))
            template_for = template_vars[0]['template_for']
            template_for_id = template_vars[0]['template_for_id']
            call_company = template_vars[0]['company']
            call_journey = template_vars[0]['journey']
        print("vars", call_company)
        journey_feedback = JourneyFeedback.objects.filter(type=template_for, company=call_company, is_active=True, is_delete=False)
        print("journey template", journey_feedback)
        
        if template_for != 'GroupCall' and template_for != 'OneToOne':
            journey_feedback = journey_feedback.filter(journey=call_journey).first()
        else:
            journey_feedback = journey_feedback.first()

        print("journey template", journey_feedback)
        
        if not journey_feedback:
            return redirect(reverse('user:user-dashboard'))

        template = journey_feedback.feedback_template
        
        questions = FeedbackTemplateQuerstion.objects.filter(
            feedback_template=template, is_active=True, is_delete=False).order_by("display_order")

        print("journey template question", questions)

        if not questions.count() > 0:
            return redirect(reverse('user:user-dashboard'))
        question_images = [
            '/static/images/feedback/Q1.png',
            '/static/images/feedback/Q2.png',
            '/static/images/feedback/Q3.png',
            '/static/images/feedback/Q4.png',
            '/static/images/feedback/Q5.png',
        ]
        context = {
            "image": random.choice(question_images),
            'question': questions[0] if questions.count() > 1 else " ",
            'next_ques': 1,
            'has_next': True if questions.count() > 1 else False,
            'journey': request.GET['journey'] if 'journey' in request.GET else "",
            'template_for': template_for,
            'template_for_id': template_for_id,
            'ques_count': questions.count()
        }
        print("context", context)
        return render(request, 'feedback/feedback_form.html', context)
        
    def get(self, request, **kwargs):
        if 'template_for' in self.kwargs:
            template_for = self.kwargs['template_for']
            template_for_id = self.kwargs['template_for_id']
        else:
            meet_id = self.kwargs['meet_id']
            if not request.GET.get('recent-call', None):
                return redirect(reverse('user:user-dashboard'))
            template_vars, response = feedbackTemplateFor(request.GET['recent-call'])
            if not response:
                return redirect(reverse('user:user-dashboard'))
            template_for = template_vars[0]['template_for']
            template_for_id = template_vars[0]['template_for_id']
            call_company = template_vars[0]['company']
            call_journey = template_vars[0]['journey']
        print("vars", call_company)
        journey_feedback = JourneyFeedback.objects.filter(type=template_for, company=call_company, is_active=True, is_delete=False)
        print("journey template", journey_feedback)
        
        if template_for != 'GroupCall' and template_for != 'OneToOne':
            journey_feedback = journey_feedback.filter(journey=call_journey).first()
        else:
            journey_feedback = journey_feedback.first()

        print("journey template", journey_feedback)
        
        if not journey_feedback:
            return redirect(reverse('user:user-dashboard'))

        template = journey_feedback.feedback_template
        
        questions = FeedbackTemplateQuerstion.objects.filter(
            feedback_template=template, is_active=True, is_delete=False).order_by("display_order")

        print("journey template question", questions)

        if not questions.count() > 0:
            return redirect(reverse('user:user-dashboard'))
        question_images = [
            '/static/images/feedback/Q1.png',
            '/static/images/feedback/Q2.png',
            '/static/images/feedback/Q3.png',
            '/static/images/feedback/Q4.png',
            '/static/images/feedback/Q5.png',
        ]
        context = {
            "image": random.choice(question_images),
            'question': questions[0] if questions.count() > 1 else " ",
            'next_ques': 1,
            'has_next': True if questions.count() > 1 else False,
            'journey': request.GET['journey'] if 'journey' in request.GET else "",
            'template_for': template_for,
            'template_for_id': template_for_id,
            'ques_count': questions.count()
        }
        print("context", context)
        return render(request, 'feedback/feedback_form.html', context)
        

    def post(self, request, **kwargs):
        if 'template_for' in self.kwargs:
            template_for = self.kwargs['template_for']
            template_for_id = self.kwargs['template_for_id']
        else:
            if not request.GET.get('recent-call', None):
                return redirect(reverse('user:user-dashboard'))
            template_vars, response = feedbackTemplateFor(request.GET['recent-call'])
            if not response:
                return redirect(reverse('user:user-dashboard'))
            template_for = template_vars[0]['template_for']
            template_for_id = template_vars[0]['template_for_id']
            call_company = template_vars[0]['company']
            call_journey = template_vars[0]['journey']

        journey_feedback = JourneyFeedback.objects.filter(type=template_for, company=call_company, is_active=True, is_delete=False)
        if template_for != 'GroupCall' and template_for != 'OneToOne':
            journey_feedback = journey_feedback.filter(journey=call_journey).first()
        else:
            journey_feedback = journey_feedback.first()

        template = journey_feedback.feedback_template
        questions = FeedbackTemplateQuerstion.objects.filter(
            feedback_template=template, is_active=True, is_delete=False).order_by("display_order")
        print("request.POST['next']", request.POST['next'])
        page = int(request.POST['page'])
        ans = ""
        if 'ans' in request.POST:
            ans = request.POST['ans']
        question = FeedbackTemplateQuerstion.objects.get(id=request.POST['ques'])

        feedbackAnswer_obj = feedbackAnswer.objects.create(
            question=question, answer=ans, feedback_for=template_for, user=request.user, journey_template=template, feedback_for_id=template_for_id)
        journey_id = ""
        if 'journey' in request.GET:
            journey = Channel.objects.get(id=request.GET['journey'])
            journey_id = journey.id
            feedbackAnswer_obj.journey = journey

        if (request.POST['next'] == 'True'):
            question_images = [
                '/static/images/feedback/Q1.png',
                '/static/images/feedback/Q2.png',
                '/static/images/feedback/Q3.png',
                '/static/images/feedback/Q4.png',
                '/static/images/feedback/Q5.png',
            ]
            context = {
                "image": random.choice(question_images),
                'question': questions[page],
                'next_ques': page + 1,
                'has_next': True if questions.count() > page+1 else False,
                'journey': journey_id,
                'template_for': template_for,
                'template_for_id': template_for_id,
                'ques_count': questions.count()
            }
            print("context", context)
            return render(request, 'feedback/feedback_form.html', context)
        else:
            is_private = is_name_private = False
            if 'is_private' in request.POST:
                is_private = True
            if 'is_name_private' in request.POST:
                is_name_private = True

            journey_feedback = JourneyFeedback.objects.filter(feedback_template=template).first()
            feedback_obj = UserFeedback.objects.create(feedback_template=template, user=request.user, journey_feedback=journey_feedback,
                                                       is_private=is_private, is_name_private=is_name_private, template_for=template_for, template_for_id=template_for_id)
            if template_for == "OneToOne":
                feedback_obj.feedback_for_user = get_meeting_user(request.session['user_type'], template_for_id)
                feedback_obj.save()
            if template_for == 'Survey':
                return redirect(reverse('content:Channel_content_v2', kwargs={'Channel': request.GET['journey']}))
            return redirect(reverse('user:user-dashboard'))


# @method_decorator(login_required, name='dispatch')
class FeedbackFormPost(View):
    permission_classes = (AllowAny,)
    def get(self, request, **kwargs):
        print("USER TYPE",  request.user)
        if request.user == "AnonymousUser":
            if "email" in request.session.keys(): 
                print("EMAIL in request.session", request.session.keys())
                print("USER TYPE", request.user)
                email = request.session['email']
            else:
                print("Returning to dashboard as USER EMAIL was not found in session") 
                return redirect('user:user-dashboard')
        else: 
            print("USER IS NOT ANNONYMUS", request.user.email, request.user.pk)
            email = request.user.email

        user_obj = User.objects.filter(email=email).exists()
        if not user_obj: return redirect('user:user-dashboard')
        request.user = user_obj

        if 'template_for' in self.kwargs:
            template_for = self.kwargs['template_for']
            template_for_id = self.kwargs['template_for_id']
        else:
            meet_id = self.kwargs['meet_id']
            print("Got the meet id")
            if not meet_id:
                return redirect(reverse('user:user-dashboard'))
            template_vars, response = feedbackTemplateFor(meet_id)
            if not response:
                return redirect(reverse('user:user-dashboard'))
            template_for = template_vars[0]['template_for']
            template_for_id = template_vars[0]['template_for_id']
            call_company = template_vars[0]['company']
            call_journey = template_vars[0]['journey']
        # print("vars", call_company)
        print("CALL Company/Journey:->", call_company, "**", call_journey, "**", template_for)
        journey_feedback = JourneyFeedback.objects.filter(type=template_for, journey=call_journey, is_active=True, is_delete=False)
        # print("journey template", journey_feedback)
        
        if template_for != 'GroupCall' and template_for != 'OneToOne':
            journey_feedback = journey_feedback.filter(journey=call_journey).first()
            print("JOURNEY FEEDBACK if", journey_feedback)
        else:
            journey_feedback = journey_feedback.first()
            print("JOURNEY FEEDBACK else", journey_feedback)

        # print("journey template", journey_feedback)
        
        if not journey_feedback:
            return redirect(reverse('user:user-dashboard'))

        template = journey_feedback.feedback_template
        print("TEMPLATE", template)
        questions = FeedbackTemplateQuerstion.objects.filter(
            feedback_template=template, is_active=True, is_delete=False).order_by("display_order")

        for q in questions:
            print("QUESTION TITLE", q.title, q.is_required, q.is_multichoice)

        if not questions.count() > 0:
            return redirect(reverse('user:user-dashboard'))
        question_images = [
            '/static/images/feedback/Q1.png',
            '/static/images/feedback/Q2.png',
            '/static/images/feedback/Q3.png',
            '/static/images/feedback/Q4.png',                                           
            '/static/images/feedback/Q5.png',
        ]
        context = {
            "image": random.choice(question_images),
            'question': questions[0] if questions.count() > 0 else " ",
            'next_ques': 1,
            'has_next': True if questions.count() > 1 else False,
            'journey':  call_journey,
            'template_for': template_for,
            'template_for_id': template_for_id,
            'ques_count': questions.count()
        }
        print("context", context)
        print("RENDERING FEEDBACK FORM")
        return render(request, 'feedback/feedback_form.html', context)
    
    def post(self, request, **kwargs):
        if 'template_for' in self.kwargs:
            template_for = self.kwargs['template_for']
            template_for_id = self.kwargs['template_for_id']
        else:
            meet_id = self.kwargs['meet_id']
            if not meet_id:
                return redirect(reverse('user:user-dashboard'))
            template_vars, response = feedbackTemplateFor(meet_id)
            if not response:
                return redirect(reverse('user:user-dashboard'))
            template_for = template_vars[0]['template_for']
            template_for_id = template_vars[0]['template_for_id']
            call_company = template_vars[0]['company']
            call_journey = template_vars[0]['journey']

        journey_feedback = JourneyFeedback.objects.filter(type=template_for, company=call_company, is_active=True, is_delete=False)
        if template_for != 'GroupCall' and template_for != 'OneToOne':
            journey_feedback = journey_feedback.filter(journey=call_journey).first()
        else:
            journey_feedback = journey_feedback.first()

        template = journey_feedback.feedback_template
        questions = FeedbackTemplateQuerstion.objects.filter(
            feedback_template=template, is_active=True, is_delete=False).order_by("display_order")
        # print("request.POST['next']", request.POST['next'])
        page = int(request.POST['page'])
        ans = ""
        if 'ans' in request.POST:
            ans = request.POST['ans']
        question = FeedbackTemplateQuerstion.objects.get(id=request.POST['ques'])

        feedbackAnswer_obj = feedbackAnswer.objects.create(
            question=question, answer=ans, feedback_for=template_for, user=request.user, journey_template=template, feedback_for_id=template_for_id)
        journey_id = ""
        if 'journey' in request.GET:
            journey = Channel.objects.get(id=request.GET['journey'])
            journey_id = journey.id
            feedbackAnswer_obj.journey = journey

        if (request.POST['next'] == 'True'):
            question_images = [
                '/static/images/feedback/Q1.png',
                '/static/images/feedback/Q2.png',
                '/static/images/feedback/Q3.png',
                '/static/images/feedback/Q4.png',
                '/static/images/feedback/Q5.png',
            ]
            context = {
                "image": random.choice(question_images),
                'question': questions[page],
                'next_ques': page + 1,
                'has_next': True if questions.count() > page+1 else False,
                'journey': journey_id,
                'template_for': template_for,
                'template_for_id': template_for_id,
                'ques_count': questions.count()
            }
            # print("context", context)
            return render(request, 'feedback/feedback_form.html', context)
        else:
            is_private = is_name_private = False
            if 'is_private' in request.POST:
                is_private = True
            if 'is_name_private' in request.POST:
                is_name_private = True

            journey_feedback = JourneyFeedback.objects.filter(feedback_template=template).first()
            feedback_obj = UserFeedback.objects.create(feedback_template=template, user=request.user, journey_feedback=journey_feedback,
                                                       is_private=is_private, is_name_private=is_name_private, template_for=template_for, template_for_id=template_for_id)
            if template_for == "OneToOne":
                feedback_obj.feedback_for_user = get_meeting_user(request.session['user_type'], template_for_id)
                feedback_obj.save()
            if template_for == 'Survey':
                return redirect(reverse('content:Channel_content_v2', kwargs={'Channel': request.GET['journey']}))
            return redirect(reverse('user:user-dashboard'))


class AddJourneyToFeedback(View):
    template_name = "feedback/journey-feedback.html"

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        print(request.POST)
        journey = Channel.objects.get(id=request.POST['journey'])
        quest = request.POST.getlist('quest[]')
        quest_feedback = request.POST.getlist('quest_feedback[]')
        assessment = request.POST.getlist('assessment[]')
        assessment_feedback = request.POST.getlist('assessment_feedback[]')
        survey = request.POST.getlist('survey[]')
        survey_feedback = request.POST.getlist('survey_feedback[]')
        journal = request.POST.getlist('journal[]')
        feedback_journal = request.POST.getlist('feedback_journal[]')
        end_journey = request.POST['end_journey']
        group_call = request.POST['group_call']
        live_call = request.POST['live_call']
        one_to_one = request.POST['one_to_one']

        feedback_template = FeedbackTemplate.objects.filter(id=end_journey)
        JourneyFeedback.objects.create(feedback_template=feedback_template, journey=journey,
                                       type=feedback_template.template_for, created_by=request.user)

        feedback_template = FeedbackTemplate.objects.filter(id=group_call)
        JourneyFeedback.objects.create(feedback_template=feedback_template, journey=journey,
                                       type=feedback_template.template_for, created_by=request.user)

        feedback_template = FeedbackTemplate.objects.filter(id=end_journey)
        JourneyFeedback.objects.create(feedback_template=feedback_template, journey=journey,
                                       type=feedback_template.template_for, created_by=request.user)

        feedback_template = FeedbackTemplate.objects.filter(id=end_journey)
        JourneyFeedback.objects.create(feedback_template=feedback_template, journey=journey,
                                       type=feedback_template.template_for, created_by=request.user)

        return redirect('feedback:add_journey_to_feedback')


def journey_content(request):
    if request.method == 'POST':
        journey = Channel.objects.get(id=request.POST['journey'])
        channel_group = ChannelGroup.objects.filter(channel=journey, is_delete=False)
        mentoring_journey = MentoringJourney.objects.filter(journey=journey)
        # print("mentoring_journey ", mentoring_journey.values())
        content_data = []
        assessment_list = []
        survey_list = []
        journal_list = []
        for data in mentoring_journey:
            if data.meta_key == "quest":
                content_data.append({"id": data.value, "title": data.name})
            elif data.meta_key == "assessment":
                assessment_list.append({"id": data.value, "title": data.name})
            elif data.meta_key == "survey":
                survey_list.append({"id": data.value, "title": data.name})
            elif data.meta_key == "journals":
                journal_list.append({"id": data.value, "title": data.name})
        return JsonResponse({"success": False, "content_list": content_data, "assessment_list": assessment_list, "survey_list": survey_list, "journal_list": journal_list})


@method_decorator(login_required, name='dispatch')
class FeedbackResponse(ListView):
    model = UserFeedback
    template_name = "feedback/feedback_response.html"
    context_object_name = "feedback_response"

    def get_queryset(self):
        return UserFeedback.objects.filter(is_active=True, is_delete=False, feedback_template__is_active=True, feedback_template__is_delete=False).order_by("-created_at")

@method_decorator(login_required, name='dispatch')
class FeedbackResponseDetails(View):

    def get(self, request, *args, **kwargs):
        # print("template_id", self.kwargs['template_id'])
        template = FeedbackTemplate.objects.get(id=self.kwargs['template_id'])
        questions = FeedbackTemplateQuerstion.objects.filter(feedback_template=template, is_active=True, is_delete=False)
        data = []
        for ques in questions:
            ans = feedbackAnswer.objects.filter(question=ques).first()
            data.append({
                'ques': ques,
                'ans': ans
            })
        context = {
            "data":data
        }

        return render(request, "feedback/feedback_response_details.html", context)
