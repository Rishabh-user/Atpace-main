from datetime import datetime
from django.http.response import Http404, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.http import HttpResponse

from apps.content.utils import is_parent_channel

from .forms import CreateSurveyForm, CreateLableForm
from .models import (Survey,
                     Question,
                     UserAnswer,
                     SurveyAttempt,
                     SurveyLabel)
from apps.content.models import Channel, SurveyAttemptChannel, SurveyChannel, UserChannelLevel, UserChannel, MentoringJourney
from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib import messages
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView
)
from django.urls import reverse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.leaderboard.views import CheckEndOfJourney
from apps.users.models import User

from django.core.mail import send_mail, BadHeaderError
from ravinsight.web_constant import SITE_NAME, DOMAIN, INFO_CONTACT_EMAIL, PROTOCOL
import random
# Create your views here.


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class CreateSurvey(CreateView):
    '''
       Redirect to the All Surveys List Page.
    '''
    model = Survey
    form_class = CreateSurveyForm
    # success_url = reverse_lazy('survey:survey-list')
    # success_url = reverse_lazy('program_manager:content')
    template_name = "survey/create_survey.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.created_by = self.request.user
        f.save()
        return super(CreateSurvey, self).form_valid(form)

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:content')
        else:
            return reverse('survey:add_survey_questions', kwargs={'survey': self.object.pk})


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class CreateLevel(CreateView, ListView):
    model = SurveyLabel
    form_class = CreateLableForm
    success_url = reverse_lazy('survey:create_label')
    template_name = "survey/add_labels.html"
    context_object_name = "levels"

    def get_queryset(self):

        return SurveyLabel.objects.filter(is_delete=False)

    # def get(self, request):
    #
    #     return render(request, self.template_name,  {'levels': self.get_queryset})


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class Updatelevel(UpdateView):
    model = SurveyLabel
    form_class = CreateLableForm
    success_url = reverse_lazy('survey:create_label')
    template_name = "survey/add_labels.html"


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class DeleteLevel(View):
    def get(self, request, **kwargs):
        role = self.kwargs['pk']
        SurveyLabel.objects.filter(pk=role).update(is_delete=True)
        return redirect(reverse_lazy('survey:create_label'))


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class EditSurvey(UpdateView):
    model = Survey
    form_class = CreateSurveyForm
    # success_url = reverse_lazy('survey:survey-list')
    # success_url = reverse_lazy('program_manager:content')
    template_name = "survey/create_survey.html"

    def get_success_url(self):
        if "ProgramManager" == self.request.session['user_type']:
            return reverse('program_manager:content')
        else:
            return reverse('survey:survey-list')


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class DeleteSurvey(View):
    def get(self, request, **kwargs):
        role = self.kwargs['pk']
        Survey.objects.filter(pk=role).update(is_delete=True)
        return redirect(reverse_lazy('survey:survey-list'))


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class SurveyList(ListView):
    '''
       Render the list of Survey.
    '''
    model = Survey
    context_object_name = "survey"
    template_name = "survey/survey_list.html"

    def get_queryset(self):
        all_survey = Survey.objects.filter(is_active=True, is_delete=False)
        if self.request.session['user_type'] == "ProgramManager":
            all_survey = all_survey.filter(created_by=self.request.user)
        return all_survey


@method_decorator(login_required, name='dispatch')
class CopySurveys(View):
    def post(self, request, *args, **kwargs):
        try:
            print(f"request.POST['survey_id']: {request.POST['survey_id']}")
            survey = Survey.objects.get(id=request.POST['survey_id'])
            print(f"survey_id: {survey}")
            new_survey = survey
            new_survey.created_by = request.user
            new_survey.pk = None
            new_survey.name = request.POST['survey']

            new_survey.save()
            print(f"new_survey: {new_survey.name}")
            questions = Question.objects.filter(survey=request.POST['survey_id'])
            for question in questions:
                new_question = question
                new_question.pk = None
                new_question.survey = new_survey
                new_question.save()
                
        except Channel.DoesNotExist:
            return JsonResponse({"message": "Survey not found", "success": False})
        return JsonResponse({"message": "New Survey created", "success": True})

@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class AddQuestion(View):
    model = Question
    context_object_name = "questions"
    template_name = "survey/add_questions.html"

    def get_queryset(self):
        return Question.objects.filter(survey=self.kwargs['survey']).order_by("display_order")

    def get(self, request, survey):
        try:
            survey = Survey.objects.get(pk=survey)
            return render(request, self.template_name, {"survey_id": survey, "questions": self.get_queryset})
        except Survey.DoesNotExist:
            raise Http404


@login_required
def update_question(request):

    if request.method == "POST":
        title = request.POST['title']
        type = request.POST['type']
        survey_id = request.POST['survey_id']
        try:
            is_required = request.POST['is_required']
        except Exception:
            is_required = False

        try:
            question_id = request.POST['question_id']
        except Exception:
            question_id = 0
        if question_id == 0:
            survey = Survey.objects.get(pk=survey_id)
            display_order = Question.objects.filter(survey=survey).count()
            question = Question.objects.create(title=title, type=type, survey=survey,
                                               is_required=is_required, display_order=display_order+1)
        else:
            question = Question.objects.get(id=question_id)
            question.title = title
            question.is_required = is_required
        if type == "DropDown" or type == "MultiChoice" or type == "Checkbox":
            options = request.POST.getlist("option[]")
            question.option_list = options

        elif type == "CheckboxGrid" or type == "MultiChoiceGrid":
            grid_row = request.POST.getlist("row[]")
            grid_coloum = request.POST.getlist("coloum[]")
            question.grid_row = grid_row
            question.grid_coloum = grid_coloum
        elif type == "LinearScale":
            question.start_rating_scale = request.POST['start_rating_scale']
            question.end_rating_scale = request.POST['end_rating_scale']
            question.start_rating_name = request.POST['start_rating_name']
            question.end_rating_name = request.POST['end_rating_name']
        print("image", request.FILES)
        if "ques_image" in request.FILES:
            image = request.FILES['ques_image']
            if image:
                question.image = image
        question.save()
        # messages.error(request, 'Something Went Wrong')
        return redirect('/survey/add-question/'+survey_id+'/')


@login_required
def delete_question(request, survey_id, pk):
    if request.method == "GET":
        deleted_ques = Question.objects.get(pk=pk)
        display_order = deleted_ques.display_order
        deleted_ques.delete()
        all_ques = Question.objects.filter(survey__id=survey_id, display_order__gt=display_order)
        for ques in all_ques:
            ques.display_order = ques.display_order - 1
            ques.save()
        
        messages.error(request, 'Something Went Wrong')
        return redirect('/survey/add-question/'+str(survey_id)+'/')


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class SurveyForm(View):
    # model = Question
    # context_object_name = "questions"
    template_name = "survey/survey_form.html"

    def get(self, request, channel, pk, **kwargs):
        questions = Question.objects.filter(survey=self.kwargs['pk']).order_by("display_order")
        survey = Survey.objects.get(id=pk)
        question_images = [
            '/static/images/feedback/Q1.png',
            '/static/images/feedback/Q2.png',
            '/static/images/feedback/Q3.png',
            '/static/images/feedback/Q4.png',
            '/static/images/feedback/Q5.png',
        ]
        image =random.choice(question_images)
        return render(request, self.template_name, {"questions": questions, "image":image, "channel": channel, "survey": survey})


@method_decorator(login_required, name='dispatch')
class SurveyInstruction(View):

    def get(self, request, channel, pk, **kwargs):
        survey = Survey.objects.get(id=pk)
        channel = is_parent_channel(channel)
        return render(request, "survey/survey-instruction.html", {"channel": channel, "survey": survey})


@method_decorator(login_required, name='dispatch')
# @method_decorator(user_only, name="dispatch")
class SubmitSurvey(View):
    template_name = "survey/thank-you.html"

    def post(self, request):
        questions = request.POST.getlist("question[]")
        print(questions, request.POST)
        survey = Survey.objects.get(pk=request.POST['survey'])
        Channels = Channel.objects.get(pk=self.request.POST['channel_id'])
        survey_attempt = SurveyAttempt.objects.create(user=request.user, survey=survey)
        SurveyAttemptChannel.objects.create(survey_attempt=survey_attempt, channel=Channels, user=request.user)
        for i in range(len(questions)):
            question_instance = Question.objects.get(pk=questions[i])

            if question_instance.type == "FileUpload":
                answers = request.FILES['answer'+questions[i]]
                UserAnswer.objects.create(user=request.user, question=question_instance,
                                          survey_attempt=survey_attempt, upload_file=answers)
            else:
                answers = request.POST['answer'+questions[i]]

                UserAnswer.objects.create(user=request.user, question=question_instance,
                                          survey_attempt=survey_attempt, response=answers)
        checkbox_question = request.POST.getlist("checkbox_question[]")

        for i in range(len(checkbox_question)):
            checkbox_answer = request.POST.getlist("checkbox_answer"+checkbox_question[i]+"[]")
            question_instance = Question.objects.get(pk=checkbox_question[i])
            UserAnswer.objects.create(user=request.user, question=question_instance,
                                      survey_attempt=survey_attempt, response=checkbox_answer)
        checkbox_grid_question = request.POST.getlist("checkbox_grid_question[]")
        for i in range(len(checkbox_grid_question)):
            question_instance = Question.objects.get(pk=checkbox_grid_question[i])
            question_answer = []
            print(len(question_instance.grid_row))
            for j in range(len(question_instance.grid_row)):

                question_answer.append(request.POST.getlist("row_"+checkbox_grid_question[i]+"_" + str(j+1)+"[]"))
            print(question_answer)
            UserAnswer.objects.create(user=request.user, question=question_instance,
                                      survey_attempt=survey_attempt, response=question_answer)

        multichoice_grid_question = request.POST.getlist("multichoice_grid_question[]")
        for i in range(len(multichoice_grid_question)):
            question_instance = Question.objects.get(pk=multichoice_grid_question[i])
            question_answer_radio = []
            print(len(question_instance.grid_row))
            for j in range(len(question_instance.grid_row)):
                question_answer_radio.append(request.POST.getlist(
                    "row_"+multichoice_grid_question[i]+"_" + str(j + 1) + "[]"))
            print("multichoice_grid_question", question_answer_radio)
            UserAnswer.objects.create(user=request.user, question=question_instance, survey_attempt=survey_attempt,
                                      response=question_answer_radio)

            # if survey_attempt:
        #     if Channels.is_global == True:
        #         status = "Joined"
        #     else:
        #         status = "Pending"
        #     UserChannel.objects.create(user=request.user, Channel=Channels, status=status)

        # Check for end of journey for assigning rewards
        CheckEndOfJourney(request.user, Channels.pk, userType=request.session['user_type'])
        subject = "Thank You, for completing the Survey"
        email_template_name = "email/complete_survey.txt"

        c = {
            "email": request.user.email,
            'domain': DOMAIN,
            'site_name': SITE_NAME,
            "user": request.user,
            'protocol': PROTOCOL,
        }
        email = render_to_string(email_template_name, c)
        try:
            # sendVerificationMail(user, user.email)
            send_mail(subject, email, INFO_CONTACT_EMAIL, [request.user.email], fail_silently=False)
        except BadHeaderError:
            return HttpResponse('Invalid header found.')

        # return render(request, self.template_name)

        # if Channels.channel_type != "MentoringJourney":
        #     if Channels.parent_id == None:
        #         status = "Joined"
        #         UserChannel.objects.create(user=request.user, Channel=Channels, status=status)

        #     return render(request, self.template_name, {'channel': Channels.pk, })
        # else:
        # if survey.feedback_required:
        #     return redirect(reverse_lazy('feedback:feedback_form', kwargs={'template_for': 'Survey', 'template_for_id':survey.pk }) + '?journey='+str(Channels.pk) )
        return redirect(reverse_lazy('content:Channel_content_v2', kwargs={'Channel': Channels.pk, }))


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class UserSurveyAttempt(ListView):
    model = SurveyAttempt
    context_object_name = "survey_attempt"
    template_name = "survey/user_surveys.html"

    def get_queryset(self):
        survey_attempt = SurveyAttempt.objects.all()
        if self.request.session['user_type'] == "ProgramManager":
            company = self.request.user.company.all()
            all_journey = Channel.objects.filter(company__in=company)
            all_survey = MentoringJourney.objects.filter(
                journey__in=all_journey, meta_key="survey", is_delete=False).values("value")
            survey_id_list = []
            for ids in all_survey:
                survey_id_list.append(ids['value'])
            survey_attempt = survey_attempt.filter(survey__in=survey_id_list)
        if self.request.GET.get("survey_id"):
            print("request.GET.get('survey_id')", self.request.GET.get('survey_id'))
            survey_attempt = survey_attempt.filter(survey__id=self.request.GET.get('survey_id'))
        return survey_attempt

@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class CheckSurvey(View):
    template_name = "survey/user_surveys_response.html"

    def get(self, request, **kwargs):
        survey_attempt = SurveyAttempt.objects.get(pk=self.kwargs['survey_attempt'])
        user_answers = UserAnswer.objects.filter(survey_attempt=survey_attempt)
        labels = SurveyLabel.objects.all()
        return render(request, self.template_name, {'survey_attempt_id': self.kwargs['survey_attempt'],
                                                    "user_answers": user_answers, 'labels': labels})

    def post(self, request, **kwargs):
        survey_attempt = SurveyAttempt.objects.filter(pk=self.kwargs['survey_attempt'])
        checked_by = User.objects.get(pk=request.user.pk)
        survey_attempt.update(
            user_skill=request.POST['user_skill'], is_check=True, checked_by=checked_by, checked_on=datetime.now())

        if survey_attempt:
            survey_attempt = survey_attempt.first()
            # survey_attempt.survey.channel_survey.first.pk
            UserChannelLevel.objects.create(survey_attempt=survey_attempt,
                                            user=survey_attempt.user, type="Survey", skill_level=request.POST['user_skill'], channel=survey_attempt.survey_attempt_channel.first().channel)

        if request.POST.get('survey_and_joined', None) == "joined":
            user_channel = UserChannel.objects.filter(user=survey_attempt.user,
                                                      Channel=survey_attempt.survey_attempt_channel.first().channel).update(status="Joined")
        if "ProgramManager" == request.session['user_type']:
            return reverse('program_manager:content')
        elif "Mentor" == request.session['user_type']:
            # print("mwntor", survey_attempt.user.id, survey_attempt.survey_attempt_channel.first().channel)
            # mentee_id = str(survey_attempt.user.id)
            # journey_id = str(survey_attempt.survey_attempt_channel.first().channel.id)
            # if(mentee_id and journey_id):
            #     return redirect('/mentee-details/'+mentee_id+"/"+journey_id)
            # else:
            return reverse('mentor:mentor_mentees')
        else:
            return redirect(reverse_lazy('survey:user_survey_attempt'))


@method_decorator(login_required, name='dispatch')
class AlloteChannel(View):
    def post(self, request):
        channel = request.POST['channel']
        channel_name = Channel.objects.get(pk=channel)
        survey = Survey.objects.get(pk=self.request.POST['survey_id'])
        Channel.objects.filter(pk=channel).update(survey=survey)
        SurveyChannel.objects.create(survey=survey, channel=channel_name)
        messages.success(request, 'Add Survey')

        if request.session['user_type'] == "ProgramManager":
            return redirect(reverse('program_manager:content'))
        return redirect(reverse('survey:survey-list'))


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class CopyQuestion(View):
    def post(self, request, **kwargs):
        survey = request.POST['survey_id']
        display_order = Question.objects.filter(survey__id=survey).count()
        obj = Question.objects.get(pk=request.POST['id'])
        obj.pk = None
        obj.display_order = display_order+1
        obj.save()
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class UpdateQOrder(View):
    def post(self, request):
        order_string = request.POST['order']
        print("update question order", order_string)
        order = order_string.split(',')

        # main_content = Content.objects.get(pk=request.POST['content'])
        for i in range(1, len(order)):
            Question.objects.filter(id=order[i]).update(display_order=i)
        return HttpResponse("Success")


@method_decorator(login_required, name='dispatch')
# @method_decorator(admin_only, name="dispatch")
class QuestionId(View):
    def post(self, request):
        questions = Question.objects.get(id=request.POST['id'])
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
            'grid_row': questions.grid_row,
            'grid_coloum': questions.grid_coloum,
        }
        return JsonResponse(question, safe=False)


@login_required
def all_survey_report(request):
    return render(request, 'assessment/Assessment-report.html')
