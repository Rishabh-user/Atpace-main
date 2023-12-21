import math
import re
from django.http.response import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.http import HttpResponse
from apps.content.utils import is_parent_channel
from apps.leaderboard.views import NotificationAndPoints, SubmitPreFinalAssessment, send_push_notification
from apps.users.helper import add_user_to_company
from apps.vonage_api.utils import journey_enrolment

from .forms import CreateTestForm
from .models import TestSeries, TestQuestion, TestOptions
from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib import messages
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView
)
from django.views import View
from apps.content.models import Channel, ChannelGroup, UserChannel, SurveyLabel, TestAttempt, UserChannelLevel, \
    UserTestAnswer
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.core.mail import BadHeaderError
from ravinsight.web_constant import PROTOCOL
import random
from apps.users.models import User
from datetime import datetime

# Create your views here.


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class CreateTest(CreateView):
    '''
       Redirect to the All Test Series List Page.
    '''
    model = TestSeries
    form_class = CreateTestForm
    # success_url = reverse_lazy('program_manager:content')
    template_name = "test_series/create_test.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super(CreateTest, self).form_valid(form)

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:content')
        else:
            return reverse('test_series:add_questions', kwargs={'survey': self.object.pk})

@method_decorator(login_required, name='dispatch')
class CopyAssessment(View):
    def post(self, request, *args, **kwargs):
        try:
            assessment = TestSeries.objects.get(id=request.POST['assessment_id'])
            new_assessment = assessment
            new_assessment.pk = None
            new_assessment.name = request.POST['assessment']
            new_assessment.created_by = request.user
            new_assessment.save()
            questions = TestQuestion.objects.filter(survey=request.POST['assessment_id'], is_active=True)
            for question in questions:
                test_options = TestOptions.objects.filter(question=question, is_active=True)
                new_question = question
                new_question.pk = None
                new_question.survey = new_assessment
                new_question.save()
                if test_options:
                    for option in test_options:
                        new_option = option
                        new_option.pk = None
                        new_option.question = new_question
                        new_option.save()                
        except TestSeries.DoesNotExist:
            return JsonResponse({"message": "Assessment not found", "success": False})
        return JsonResponse({"message": "New Assessment created", "success": True})


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class EditTest(UpdateView):
    model = TestSeries
    form_class = CreateTestForm
    # success_url = reverse_lazy('test_series:test-list')
    # success_url = reverse_lazy('program_manager:content')
    template_name = "test_series/create_test.html"

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:content')
        else:
            return reverse('test_series:test-list')


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class TestList(ListView):
    '''
       Render the list of Test Series.
    '''
    model = TestSeries
    context_object_name = "survey"
    template_name = "test_series/test_list.html"

    def get_queryset(self):
        all_assessment = TestSeries.objects.filter(is_active=True, is_delete=False)
        if self.request.session['user_type'] == "ProgramManager":
            all_assessment = all_assessment.filter(created_by=self.request.user)
        return all_assessment


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class AddQuestion(View):
    model = TestQuestion
    context_object_name = "questions"
    template_name = "test_series/add_questions.html"

    def get_queryset(self):
        return TestQuestion.objects.filter(survey=self.kwargs['survey'])

    def get(self, request, survey):
        test_series = TestSeries.objects.get(pk=survey)
        return render(request, self.template_name, {"test_series": test_series, "questions": self.get_queryset})


@login_required
def update_question(request, format=None):
    if request.method == "POST":
        title = request.POST['title']
        type = request.POST['type']
        survey_id = request.POST['survey_id']
        marks = request.POST['marks']
        skill_level = request.POST['skill_level']
        try:
            is_required = request.POST['is_required']
        except Exception:
            is_required = False

        survey = TestSeries.objects.get(pk=survey_id)

        try:
            question_id = request.POST['question_id']
        except Exception:
            question_id = 0

        if question_id == 0:
            survey = TestSeries.objects.get(pk=survey_id)
            display_order = TestQuestion.objects.filter(survey=survey).count()
            question = TestQuestion.objects.create(title=title, type=type, survey=survey,
                                                   marks=marks, is_required=is_required, skill_level=skill_level,
                                                   display_order=display_order + 1)
        else:
            question = TestQuestion.objects.get(id=question_id)
            question.title = title
            question.marks = marks
            question.is_required = is_required

        if type == "DropDown" or type == "MultiChoice" or type == "Checkbox":
            options = request.POST.getlist("option[]")
            option_marks = request.POST.getlist("option_marks[]")
            option_correct = request.POST.getlist("option_correct[]")
            print("OPTION CORRECT", option_correct)
            if question_id != 0:
                TestOptions.objects.filter(question=question).delete()
            for i in range(len(options)):
                TestOptions.objects.create(question=question, option=options[i], marks=option_marks[i], correct_option=option_correct[i])
        print("image", request.FILES)
        if "ques_image" in request.FILES:
            image = request.FILES['ques_image']
            if image:
                question.image = image
        question.save()
        # messages.error(request, 'Something Went Wrong')
        return redirect('/test-series/add-question/' + survey_id + '/')


@login_required
def delete_question(request, survey_id, pk):
    if request.method == "GET":
        try:
            deleted_ques = TestQuestion.objects.get(pk=pk)
        except Exception:
            messages.error(request, 'Something Went Wrong')
            return redirect(f'/test-series/add-question/{str(survey_id)}/')
        display_order = deleted_ques.display_order
        deleted_ques.delete()
        all_ques = TestQuestion.objects.filter(survey__id=survey_id, display_order__gt=display_order)
        for ques in all_ques:
            ques.display_order = ques.display_order - 1
            ques.save()
        messages.error(request, 'Something Went Wrong')
        return redirect(f'/test-series/add-question/{str(survey_id)}/')


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class TestSeriesForm(ListView):
    template_name = "test_series/test_series_form.html"

    def get(self, request, channel, pk, **kwargs):
        type = ""
        if request.GET.get('type'):
            type = request.GET.get('type')
        question_images = [
            '/static/images/feedback/Q1.png',
            '/static/images/feedback/Q2.png',
            '/static/images/feedback/Q3.png',
            '/static/images/feedback/Q4.png',
            '/static/images/feedback/Q5.png',
        ]
        image =random.choice(question_images)

        questions = TestQuestion.objects.filter(survey=self.kwargs['pk'])
        return render(request, self.template_name, {"questions": questions, "image":image, "channel": channel, "assessment": pk, "type": type})

    # def get_queryset(self):
    #     return Question.objects.filter(survey=self.kwargs['pk'])


@method_decorator(login_required, name='dispatch')
class AssessmentInstruction(View):

    def get(self, request, channel, pk, **kwargs):
        survey = TestSeries.objects.get(id=pk)
        channel = is_parent_channel(channel)
        return render(request, "survey/survey-instruction.html", {"channel": channel, "survey": survey})


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class SubmitTest(View):
    template_name = "test_series/thank-you.html"

    def post(self, request):
        questions = request.POST.getlist("question[]")
        type = request.POST['type']
        test = TestSeries.objects.get(pk=request.POST['test'])
        Channels = Channel.objects.get(pk=self.request.POST['channel'])
        channel_group = ChannelGroup.objects.filter(channel=Channels, is_delete=False)
        test_attempt = TestAttempt.objects.create(user=request.user, channel=Channels, test=test, type=type)
        marks = 0
        op_marks = 0
        test_marks = 0
        for i in range(len(questions)):
            answers = request.POST['answer' + questions[i]]
            question_instance = TestQuestion.objects.get(pk=questions[i])
            test_marks = test_marks + question_instance.marks

            if question_instance.type == 'ShortAnswer':
                UserTestAnswer.objects.create(user=request.user, question=question_instance,
                                              question_marks=question_instance.marks, test_attempt=test_attempt, response=answers)
            else:
                marks = marks + question_instance.marks

                option_mark = TestOptions.objects.get(question=question_instance, pk=answers)
                op_marks = op_marks + option_mark.marks
                print("179 op_marks", op_marks)
                UserTestAnswer.objects.create(user=request.user, question=question_instance,
                                              question_marks=question_instance.marks,
                                              test_attempt=test_attempt, response=option_mark.option,
                                              total_marks=option_mark.marks)
        checkbox_question = request.POST.getlist("checkbox_question[]")
        opt_marks = 0
        for i in range(len(checkbox_question)):
            checkbox_answer = request.POST.getlist("checkbox_answer" + checkbox_question[i] + "[]")

            question_instance = TestQuestion.objects.get(pk=checkbox_question[i])
            test_marks = test_marks + question_instance.marks
            marks = marks + question_instance.marks
            print("191 marks", marks)
            checkbox_answer = request.POST.getlist("checkbox_answer" + checkbox_question[i] + "[]")
            for x in range(len(checkbox_answer)):
                option_mark = TestOptions.objects.get(question=question_instance, pk=checkbox_answer[x])
                opt_marks += option_mark.marks
                op_marks += option_mark.marks
                print("194 op_marks", opt_marks)
            UserTestAnswer.objects.create(user=request.user, question=question_instance,
                                          question_marks=question_instance.marks,
                                          test_attempt=test_attempt, response=checkbox_answer, total_marks=opt_marks)

        if not test.auto_check:
            op_marks = 0
            user_skill = None
        else:
            if test_attempt.channel.parent_id is None:
                channel_group = channel_group.first()
                user_skill = channel_group.channel_for
            else:
                print(op_marks)
                print(test_marks)
                assessment_attempt_marks = math.ceil((op_marks / int(test_marks)) * 100)
                print(assessment_attempt_marks)
                print(channel_group)
                channel_group = channel_group.filter(
                    start_mark__lte=assessment_attempt_marks, end_marks__gte=assessment_attempt_marks).first()
                print("216 channel_group", channel_group)
                user_skill = channel_group.channel_for
                print("216 user_skill", user_skill)
                test_attempt.is_check = True
                if user_skill:
                    UserChannelLevel.objects.create(test_attempt=test_attempt, user=test_attempt.user,
                                                    type="Assessment",
                                                    skill_level=user_skill, channel=Channels)

        SubmitPreFinalAssessment(user=request.user, test_attempt=test_attempt.type, channel=Channels.pk, userType=request.session['user_type'])
        test_attempt.total_marks = op_marks
        test_attempt.test_marks = test_marks
        test_attempt.user_skill = user_skill
        test_attempt.save()
        subject = "Thank toy For complete Assessment"
        email_template_name = "email/complete_assessment.txt"

        c = {
            "email": request.user.email,
            'domain': 'growatpace.com',
            'site_name': 'Growatpace',
            "user": request.user,
            'protocol': PROTOCOL,
        }
        email = render_to_string(email_template_name, c)
        try:
            print("Hello")
            # send_mail(subject, email, 'info@growatpace.com', [request.user.email], fail_silently=False)
        except BadHeaderError:
            return HttpResponse('Invalid header found.')

        context = {
            "auto_check": test.auto_check
        }

        if Channels.channel_type != "MentoringJourney":
            if Channels.parent_id == None:
                status = "Joined"
                try:
                    UserChannel.objects.get(user=request.user, Channel=Channels, status=status)
                except UserChannel.DoesNotExist:
                    UserChannel.objects.create(user=request.user, Channel=Channels, status=status)
                    add_user_to_company(request.user, Channels.company)
                    context = {
                        "screen":"ProgramJourney",
                        "navigationPayload": { 
                            "courseId": str(Channels.id)
                        }
                    }
                    send_push_notification(request.user, Channels.title, f"You're enrolled in {Channels.title}", context)
                    NotificationAndPoints(request.user, "joined journey")
                    if Channels.whatsapp_notification_required and (request.user.phone and request.user.is_whatsapp_enable):
                        journey_enrolment(request.user, Channels)
                    else:
                        print("phone does not exist")
            return render(request, self.template_name, context)
        else:
            return redirect(reverse_lazy('content:Channel_content_v2', kwargs={'Channel': Channels.pk, }))


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class UserAssessmentAttempt(View):
    template_name = "test_series/user_test.html"

    def get(self, request, **kwargs):
        test_attempt = TestAttempt.objects.all()
        if request.GET.get("assessment_id"):
            print("request.GET.get('assessment_id')", request.GET.get('assessment_id'))
            test_attempt = test_attempt.filter(test__id=request.GET.get('assessment_id'))
        context = {
            "test_attempt": test_attempt
        }
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class AlloteChannel(View):
    def post(self, request):
        channel = request.POST['channel']
        assessment_type = request.POST['assessment_type']
        test_series = TestSeries.objects.get(pk=request.POST['survey_id'])
        channels = Channel.objects.filter(pk=channel)

        if assessment_type == "pre":
            channels.update(test_series=test_series)

        elif assessment_type == "post":
            ChannelGroup.objects.filter(pk=request.POST['group'], is_delete=False).update(post_assessment=test_series)

        return redirect(reverse_lazy('test_series:test-list'))


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class AssessmentChannel(View):
    template_name = "test_series/assessment_channel.html"

    def get(self, request, **kwargs):
        pk = self.kwargs['pk']
        channels = Channel.objects.filter(test_series=pk)
        channel_group = ChannelGroup.objects.filter(post_assessment=pk, is_delete=False)
        return render(request, self.template_name, {"channels": channels, "channel_group": channel_group})


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class CheckAssessment(View):
    template_name = "test_series/user_assessment_response.html"

    def get(self, request, **kwargs):
        survey_attempt = TestAttempt.objects.get(pk=self.kwargs['assessment'])

        user_answers = UserTestAnswer.objects.filter(test_attempt=survey_attempt)
        user_answers_list = []
        for user_answers in user_answers:
            print(user_answers.question.type)
            if user_answers.question.type == "Checkbox":
                print(user_answers.response)
                import ast
                ids = ast.literal_eval(user_answers.response)
                print(ids)
                temp = TestOptions.objects.filter(pk__in=ids)
                responses = [temp.option for temp in temp]
                response = responses

            else:
                response = user_answers.response
            user_answers_list.append({
                "id": user_answers.id,
                "question": user_answers.question,
                "response": response,
                "question_marks": user_answers.question_marks,
                "total_marks": user_answers.total_marks
            })

        labels = SurveyLabel.objects.all()
        return render(request, self.template_name, {'survey_attempt_id': self.kwargs['assessment'],
                                                    "user_answers": user_answers_list, 'labels': labels,
                                                    'test_attempt': survey_attempt})

    def post(self, request, **kwargs):
        test_attempts = TestAttempt.objects.filter(pk=request.POST['survey_attempt'])

        response_id = request.POST.getlist('response_id[]')
        marks = request.POST.getlist('marks[]')
        test_marks = request.POST['test_marks']
        user_skill = request.POST['user_skill']
        total_marks = 0

        for i in range(len(response_id)):
            UserTestAnswer.objects.filter(pk=response_id[i]).update(total_marks=marks[i])
            total_marks = total_marks + int(marks[i])

        # test_attempts.update(user_skill=request.POST['user_skill'], total_marks=total_marks, is_check=True)
        if len(test_attempts) > 0:
            test_attempt = test_attempts.first()
            channel_group = ChannelGroup.objects.filter(channel=test_attempt.channel, is_delete=False)
            print(channel_group)
            if user_skill == "":
                if test_attempt.channel.parent_id == None:
                    channel_group = channel_group.first()
                    print(channel_group)
                    user_skill = channel_group.channel_for
                else:
                    assessment_attempt_marks = math.ceil((total_marks / int(test_marks)) * 100)
                    channel_group = channel_group.filter(
                        start_mark__lte=assessment_attempt_marks, end_marks__gte=assessment_attempt_marks).first()
                    print(channel_group)
                    user_skill = channel_group.channel_for
            checked_by = User.objects.get(pk=request.user.pk)
            test_attempts.update(user_skill=user_skill, total_marks=total_marks, is_check=True, checked_by=checked_by, checked_on=datetime.now())
            UserChannelLevel.objects.create(test_attempt=test_attempt, user=test_attempt.user, type="Assessment",
                                            skill_level=user_skill, channel=test_attempt.channel)
        if request.POST.get('survey_and_joined', None) == "joined":
            UserChannel.objects.filter(user=test_attempt.user,
                                       Channel=test_attempt.channel).update(status="Joined")

        if "ProgramManager" == request.session['user_type']:
            return reverse('program_manager:content')
        elif "Mentor" == request.session['user_type']:
            mentee_id = str(test_attempt.user.id)
            journey_id = str(test_attempt.channel.id)
            if(mentee_id and journey_id):
                return redirect('/mentee-details/'+mentee_id+"/"+journey_id)
            else:
                return reverse('mentor:mentor_mentees')
        else:
            return redirect(reverse_lazy('test_series:user_test_attempt'))


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class CopyQuestion(View):
    def post(self, request, **kwargs):
        survey = request.POST['survey_id']
        display_order = TestQuestion.objects.filter(survey__id=survey).count()
        obj = TestQuestion.objects.get(pk=request.POST['id'])
        obj2 = TestOptions.objects.filter(question=obj)
        obj.pk = None
        obj.display_order = display_order + 1
        obj.save()
        for obj2 in obj2:
            obj2.pk = None
            obj2.question = obj
            obj2.save()
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class UpdateQOrder(View):
    def post(self, request):
        order_string = request.POST['order']

        order = order_string.split(',')
        # main_content = Content.objects.get(pk=request.POST['content'])
        for i in range(len(order)):
            TestQuestion.objects.filter(id=order[i]).update(display_order=i)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class QuestionId(View):
    def post(self, request):
        questions = TestQuestion.objects.get(id=request.POST['id'])
        option_list = [{"options": option.option, "marks": option.marks} for option in questions.options.all()]

        question = {
            'id': questions.id,
            'title': questions.title,
            'type': questions.type,
            'option_list': option_list,
            'q_marks': questions.marks,
            'grid_row': questions.grid_row,
            'grid_coloum': questions.grid_coloum,
            'is_required': questions.is_required
        }
        return JsonResponse(question, safe=False)
