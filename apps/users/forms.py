from django import forms
from django.contrib.auth.forms import UserCreationForm
from apps.content.models import Channel
from apps.mentor.models import Pool
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit, Div
import io
import csv
from datetime import datetime
from .models import Collabarate, Company, Learner, ProfileAssestQuestion, User, UserRoles, UserTypes, Coupon, \
    ContactProgramTeam
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from apps.atpace_community.models import Spaces
from django_select2.forms import Select2MultipleWidget
from .utils import convert_to_utc, convert_to_local_time

class CustomAuthenticationForm(AuthenticationForm):
    type = forms.ModelChoiceField(queryset=UserTypes.objects.filter(~Q(type="Creator")), required=True)
    username = UsernameField(
        label='Email',
        widget=forms.TextInput(attrs={'autofocus': True})
    )


class CustomUserCreationForm(UserCreationForm):
    '''
        Custom User Creation Form.
    '''

    class Meta:
        model = Learner
        fields = ['first_name', 'last_name', 'email', 'username', 'coupon_code', 'is_whatsapp_enable',
                  'phone', 'password1', 'password2', 'is_active', 'company', 'profile_assest_enable']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['email'].required = True
        self.fields['company'].label = "Select Community"
        self.fields['profile_assest_enable'].label = "Enable Profile Assessment"
        self.fields['is_whatsapp_enable'].label = "Enable WhatsApp Notification"
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),

            ),
            Row(
                Column('phone', css_class='form-group col-md-6 mb-0'),
                Column('company', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('coupon_code', css_class='form-group col-md-6 mb-0'),
                Column('is_active', css_class='form-group col-md-6 mb-0'),
            ),

            Row(
                Column('profile_assest_enable', css_class='form-group col-md-6 mb-0'),
                Column('is_whatsapp_enable', css_class='form-group col-md-6 mb-0'),
            ),
            Submit('submit', 'Sign in')
        )

    def clean(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already exist.")


class CustomUserUpdateForm(forms.ModelForm):
    '''
        Custom User Creation Form.
    '''

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'coupon_code', 'is_whatsapp_enable',
                  'phone', 'is_active', 'company', "userType", 'profile_assest_enable']
        widgets = {
            'userType': forms.CheckboxSelectMultiple()
        }

        help_texts = {
            'username': None,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['email'].required = True
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['phone'].widget.attrs['readonly'] = True
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['profile_assest_enable'].label = "Enable Profile Assessment"
        self.fields['is_whatsapp_enable'].label = "Enable WhatsApp Notification"
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row '
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'

            ),
            Row(
                Column('phone', css_class='form-group col-md-6 mb-0'),
                Column('company', css_class='form-group  col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('userType', css_class='form-group  col-md-6 mb-0'),
                Column('is_active', css_class='form-group col-md-6 mb-0 '),
                css_class='form-row'
            ),
            Row(
                Column('coupon_code', css_class='form-group  col-md-6 mb-0'),
                Column('is_whatsapp_enable', css_class='form-group  col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('profile_assest_enable', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'update')
        )


class CustomAdminCreationForm(UserCreationForm):
    '''
        Custom Admin Creation Form.
    '''

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'coupon_code',
                  'phone', 'password1', 'password2', 'is_active', 'userType', 'company', 'profile_assest_enable']
        widgets = {
            'userType': forms.CheckboxSelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        # UserTypes.objects.filter(~Q(type="Learner"))
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['userType'].queryset = UserTypes.objects.filter(~Q(type="Creator"))
        self.fields['profile_assest_enable'].label = "Enable Profile Assessment"
        self.fields['company'].label = "Select Community"
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 '),
                Column('last_name', css_class='form-group col-md-6 '),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 '),
                Column('email', css_class='form-group col-md-6 '),
                css_class='form-row'
            ),

            Row(
                Column('password1', css_class='form-group col-md-6 '),
                Column('password2', css_class='form-group col-md-6 '),
                css_class='form-row'
            ),
            Row(
                Column('phone', css_class='form-group col-md-6'),
                Column('is_active', css_class='form-group col-md-6 '),
                css_class='form-row'
            ),
            Row(
                Column('userType', css_class='form-group col-md-6'),
                Column('company', css_class='form-group col-md-6 '),
                css_class='form-row'

            ),
            Row(
                Column('coupon_code', css_class='form-group  col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('profile_assest_enable', css_class='form-group col-md-6 mb-0'),
                Column('is_whatsapp_enable', css_class='form-group col-md-6 mb-0'),
            ),
            Submit('submit', 'Sign in')
        )

    def clean(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already exist.")


class CompanyCreationFrom(forms.ModelForm):
    '''
        Custom Company Creation Form.
    '''

    class Meta:
        model = Company
        fields = ['name', 'email', 'logo', 'banner', 'address', 'state', 'city', 'zip_code', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'email',
            'logo',
            'banner',
            'address',
            'state',
            'city',
            'zip_code',
            'is_active',
            Submit('submit', 'Add')
        )


class UploadCSVForm(forms.Form):
    '''
        A Form from which user can upload csv file
        in-order to bulk creation of App-users.
    '''
    data_file = forms.FileField()
    data_company = forms.ModelChoiceField(queryset=Company.objects.all(), required=False)

    def process_data(self):
        f = io.TextIOWrapper(self.cleaned_data['data_file'].file)
        reader = csv.DictReader(f)
        company = self.cleaned_data['data_company']

        for row in reader:
            phone = str(row['country_code']) + "" + str(row['phone'])
            user_type = UserTypes.objects.get(type="Learner")
            create_user = User.objects.create_user(username=row['username'], first_name=row['first_name'],
                                                   last_name=row['last_name'],
                                                   email=row['email'], phone=phone, address=row['address'],
                                                   password="Pass@1234", company=company)
            create_user.userType.add(user_type)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'data_file',
            'data_company',
            Submit('submit', 'Add')
        )


class CreateRoleForm(forms.ModelForm):
    class Meta:
        model = UserRoles
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.fields['name'].label = "Title"
        self.helper.layout = Layout(
            'name',
            Submit('submit', 'Create')
        )


class UserProfileUpdateForm(forms.ModelForm):
    '''
        Custom User Creation Form.
    '''

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'gender', 'age', 'address', 'city', 'state',
                  'phone', 'linkedin_profile', 'company', 'current_status', 'position', 'expertize', 'industry',
                  'about_us', 'profile_heading']
        # widgets = {
        # 'industry': Select(attrs={'style': 'width: 400px;'}),
        # }
        # widgets = {
        #     'name': Select(),
        # }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        company = self.request.user.company.filter(pk=self.request.session['company_id'])
        self.helper.form_method = 'post'
        self.fields['email'].required = True
        self.fields['phone'].widget.attrs['readonly'] = True
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['company'].queryset = company
        self.fields['company'].label = "Organization"
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-0'),
                Column('phone', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('gender', css_class='form-group col-md-6 mb-0'),
                Column('age', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('current_status', css_class='form-group col-md-6 mb-0'),
                Column('company', css_class='form-group col-md-6 mb-0'),

            ),
            Row(
                Column('industry', css_class='form-group col-md-6 mb-0'),
                Column('expertize', css_class='form-group col-md-6 mb-0'),

            ),
            Row(
                Column('position', css_class='form-group col-md-6 mb-0'),
                Column('profile_heading', css_class='form-group col-md-6 mb-0'),

            ),
            Row(
                Column('about_us', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('address', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('city', css_class='form-group col-md-6 mb-0'),
                Column('state', css_class='form-group col-md-6 mb-0'),
                
            ),

            Submit('submit', 'update')
        )


class AssignMentor(forms.Form):
    journey = forms.ModelChoiceField(queryset=Channel.objects.filter(is_delete=False, is_active=True, closure_date__gt=datetime.now()), required=True)
    pool = forms.ModelChoiceField(queryset=Pool.objects.filter(is_active=True), required=True)
    match = forms.CheckboxInput()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['journey'].widget.attrs['class'] = 'form-control select2'

        self.helper.layout = Layout(
            'journey',
            'pool',
            'match',
            Submit('submit', 'Run')
        )


class DateInput(forms.DateInput):
    input_type = 'date'


class CouponCodeForm(forms.ModelForm):
    journey = forms.ModelChoiceField(queryset=Channel.objects.filter(is_delete=False, is_active=True, parent_id=None, closure_date__gt=datetime.now()),
                                     required=False)
    '''
        Custom Coupon Creation Form.
    '''

    class Meta:
        model = Coupon
        fields = ['name', 'code', 'valid_from', 'valid_to', 'type', 'is_active', "journey"]
        widgets = {
            'valid_from': DateInput(),
            'valid_to': DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['journey'].widget.attrs['class'] = 'form-control select2'
        self.helper.layout = Layout(
            'name',
            'code',
            'valid_from',
            'valid_to',
            'type',
            # Row(
            #     Column('type', css_class='form-group col-md-12 mb-0'),
            # ),
            # Row(
            #     Column('journey', css_class='form-group col-md-12 mb-0'),
            # ),
            'journey',
            'is_active',
            Submit('submit', 'Add')
        )


class ProfileAssestQuestionFrom(forms.ModelForm):
    CHOICES = (("Learner", "Learner"), ("Mentor", "Mentor"), ("ProgramManager", "ProgramManager"))
    journey = forms.ModelChoiceField(queryset=Channel.objects.filter(
        is_active=True, is_delete=False, parent_id=None, closure_date__gt=datetime.now()), required=False,)

    question_for = forms.MultipleChoiceField(choices=CHOICES, widget=Select2MultipleWidget)

    class Meta:
        model = ProfileAssestQuestion
        fields = ['journey', 'question', 'options', 'question_type', 'question_for', 'is_active', 'is_multichoice', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['journey'].widget.attrs['class'] = 'form-control select2'
        self.helper.layout = Layout(
            'journey',
            'question',
            'options',
            'question_type',
            'question_for',
            'is_active',
            'is_multichoice',
            Submit('submit', 'Add')
        )


class SetPasswordForm(forms.ModelForm):
    new_password1 = forms.CharField(
        label=("New password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        label=("New password confirmation"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'new_password1',
            'new_password2',
            Submit('submit', 'Set Password')
        )


class DateInput(forms.DateInput):
    input_type = 'datetime-local'


class CollabarateForm(forms.ModelForm):
    user_type = UserTypes.objects.filter(~Q(type="Learner"))
    speaker = forms.ModelChoiceField(queryset=None, required=True)
    company = forms.ModelChoiceField(queryset=None, required=True)
    journey = forms.ModelChoiceField(queryset=None, required=True)
    space_name = forms.ModelChoiceField(queryset=Spaces.objects.filter(
        space_type="Event", is_active=True, is_delete=False, is_hidden=False, hidden_from_non_members=False),  required=False)
    custom_url = forms.CharField(required=False)
    custom_background = forms.ImageField(required=True)

    class Meta:
        model = Collabarate
        fields = ["title", "description", "company", "speaker", 'start_time', 'end_time', 'custom_url',
                  "is_active", "journey", "add_to_community", "space_name"]
        widgets = {
            'start_time': DateInput(),
            'end_time': DateInput()
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(CollabarateForm, self).__init__(*args, **kwargs)
        user_type = UserTypes.objects.filter(~Q(type="Learner"))
        # company = Company.objects.get(name=self.request.user.company.name)
        company = self.request.user.company.filter(pk=self.request.session['company_id'])
        # company = self.request.user.company.all()
        # company_name = self.request.session['company_name']
        self.fields['company'].queryset = company
        self.fields['journey'].queryset = Channel.objects.filter(~Q(channel_type='SelfPaced'), company__in=company, closure_date__gt=datetime.now())
        # self.fields['space_name'].queryset = Spaces.objects.filter(
        #     space_type="Event", is_active=True, is_delete=False, is_hidden=False, hidden_from_non_members=False)
        self.fields['speaker'].widget.attrs['class'] = 'form-control'
        self.fields['company'].widget.attrs['class'] = 'form-control'
        self.fields['journey'].widget.attrs['class'] = 'form-control'
        self.fields['space_name'].widget.attrs['class'] = 'form-control'
        # self.initial['space_name'] = 'test event space'
        self.fields['speaker'].queryset = User.objects.filter(is_active=True, is_archive=False, is_delete=False,
                                                              userType__in=user_type, company__in=company).distinct()
        self.fields['custom_url'].label = "Custom URL (external links are excluded from analytics and reporting metrics)"
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'company',
            'journey',
            'speaker',
            Div(
                Div('start_time', css_class='col-md-6 col-xs-6 col-xl-6 col-xxl-6 col-lg-6 col-sm-6'),
                Div('end_time', css_class='col-md-6 col-xs-6 col-xl-6 col-xxl-6 col-lg-6 col-sm-6'),
                css_class='form-group row'
            ),
            'custom_url',
            'is_active',
            'add_to_community',
            'space_name',
            'custom_background',  # Include the file upload field in the form
            Submit('submit', 'Add')
        )


class EditCollabarateForm(forms.ModelForm):
    user_type = UserTypes.objects.filter(~Q(type="Learner"))
    speaker = forms.ModelChoiceField(queryset=None, required=True)
    company = forms.ModelChoiceField(queryset=None, required=True)
    journey = forms.ModelChoiceField(queryset=None, required=True)
    # start_time =forms.DateTimeField(),    
    space_name = forms.ModelChoiceField(queryset=Spaces.objects.filter(
        space_type="Event", is_active=True, is_delete=False, is_hidden=False, hidden_from_non_members=False), required=False)
    custom_url = forms.CharField(required=True)
    custom_background = forms.ImageField(required=True)

    class Meta:
        model = Collabarate
        fields = ["title", "description", "speaker", "company", 'start_time', 'end_time', "custom_url",
                  "is_active", "journey", "add_to_community", "space_name"]

        widgets = {
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(EditCollabarateForm, self).__init__(*args, **kwargs)
        user_type = UserTypes.objects.filter(~Q(type="Learner"))
        # company = self.request.user.company.all()
        company = self.request.user.company.filter(pk=self.request.session['company_id'])
        self.fields['company'].queryset = company
        self.fields['journey'].queryset = Channel.objects.filter(~Q(channel_type='SelfPaced'), company__in=company, closure_date__gt=datetime.now())
        # self.fields['space_name'].queryset = Spaces.objects.filter(
        #     space_type="Event", is_active=True, is_delete=False, is_hidden=False, hidden_from_non_members=False)
        self.fields['speaker'].widget.attrs['class'] = 'form-control'
        # self.fields['company'].widget.attrs['class'] = 'form-control select2'
        self.initial['start_time'] = convert_to_local_time(self.instance.start_time, self.request.session.get('timezone',None)).strftime("%Y-%m-%dT%H:%M")
        self.initial['end_time'] = convert_to_local_time(self.instance.end_time, self.request.session.get('timezone',None)).strftime("%Y-%m-%dT%H:%M")
        self.fields['journey'].widget.attrs['class'] = 'form-control'
        self.fields['space_name'].widget.attrs['class'] = 'form-control'
        self.fields['speaker'].queryset = User.objects.filter(is_active=True, is_archive=False, is_delete=False,
                                                              userType__in=user_type, company__in=company).distinct()
        self.fields['custom_url'].label = "Custom URL (external links are excluded from analytics and reporting metrics)"
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'company',
            'journey',
            'speaker',
            Div(
                Div('start_time', css_class='col-md-6 col-xs-6 col-xl-6 col-xxl-6 col-lg-6 col-sm-6'),
                Div('end_time', css_class='col-md-6 col-xs-6 col-xl-6 col-xxl-6 col-lg-6 col-sm-6'),
                css_class='form-group row'
            ),
            'custom_url',
            'is_active',
            'add_to_community',
            'space_name',
            'custom_background',
            Submit('submit', 'Add')
        )


class CollabarateGroupForm(forms.ModelForm):
    user_type = UserTypes.objects.filter(type="Learner")
    speaker = forms.ModelChoiceField(queryset=None, required=True)
    custom_url = forms.CharField(required=False)
    custom_background = forms.ImageField(required=True)

    class Meta:
        model = Collabarate
        fields = ["title", "description", "speaker", "participants",
                  'start_time', 'end_time', 'custom_url', "is_active", ]

        widgets = {
            'start_time': DateInput(),
            'end_time': DateInput()
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        user_type = UserTypes.objects.filter(type="Learner")
        company = self.request.user.company.filter(pk=self.request.session['company_id'])
        self.fields['speaker'].queryset = User.objects.filter(userType__type__in=["Mentor", "ProgramManager"], is_active=True, is_archive=False, is_delete=False,
                                                               company__in=company).distinct()
        self.helper = FormHelper()
        self.fields['participants'].required = True
        self.fields['speaker'].widget.attrs['class'] = 'form-control'
        self.fields['participants'].widget.attrs['class'] = 'form-control'

        self.fields['participants'].queryset = User.objects.filter(userType__type__in=["Mentor", "Learner", "ProgramManager"], is_active=True,
                                                                   is_archive=False, is_delete=False, company__in=company).distinct()
        self.fields['custom_url'].label = "Custom URL (external links are excluded from analytics and reporting metrics)"
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'speaker',
            'participants',
            Div(
                Div('start_time', css_class='col-md-6 col-xs-6 col-xl-6 col-xxl-6 col-lg-6 col-sm-6'),
                Div('end_time', css_class='col-md-6 col-xs-6 col-xl-6 col-xxl-6 col-lg-6 col-sm-6'),
                css_class='form-group row'
            ),
            'custom_url',
            'is_active',
            'custom_background',
            Submit('submit', 'Add')
        )


class EditCollabarateGroupForm(forms.ModelForm):
    user_type = UserTypes.objects.filter(type="Learner")
    speaker = forms.ModelChoiceField(queryset=None, required=True)
    custom_url = forms.CharField(required=True)
    custom_background = forms.ImageField(required=True)

    class Meta:
        model = Collabarate
        fields = ["title", "description", "speaker", "participants",
                  'start_time', 'end_time', "custom_url", "is_active", ]

        widgets = {
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        user_type = UserTypes.objects.filter(type="Learner")
        company = self.request.user.company.filter(pk=self.request.session['company_id'])
        self.fields['speaker'].queryset = User.objects.filter(userType__type__in=["Mentor", "ProgramManager"], is_active=True, is_archive=False, is_delete=False,
                                                               company__in=company).distinct()
        self.helper = FormHelper()
        self.fields['participants'].required = True
        self.fields['speaker'].widget.attrs['class'] = 'form-control'
        self.fields['participants'].widget.attrs['class'] = 'form-control'
        self.initial['start_time'] = convert_to_local_time(self.instance.start_time, self.request.session.get('timezone',None)).strftime("%Y-%m-%dT%H:%M")
        self.initial['end_time'] = convert_to_local_time(self.instance.end_time, self.request.session.get('timezone',None)).strftime("%Y-%m-%dT%H:%M")

        self.fields['participants'].queryset = User.objects.filter(userType__type__in=["Mentor", "Learner", "ProgramManager"], is_active=True,
                                                                   is_archive=False, is_delete=False, company__in=company).distinct()
        self.fields['custom_url'].label = "Custom URL (external links are excluded from analytics and reporting metrics)"
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'speaker',
            'participants',
            Div(
                Div('start_time', css_class='col-md-6 col-xs-6 col-xl-6 col-xxl-6 col-lg-6 col-sm-6'),
                Div('end_time', css_class='col-md-6 col-xs-6 col-xl-6 col-xxl-6 col-lg-6 col-sm-6'),
                css_class='form-group row'
            ),
            'custom_url',
            'is_active',
            'custom_background',
            Submit('submit', 'Save Changes')
        )


class ContactProgramTeamForm(forms.ModelForm):
    image = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))

    class Meta:
        model = ContactProgramTeam
        fields = ["subject", "issue", "image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'subject',
            'issue',
            "image",
            Submit('submit', 'Create')
        )
        # self.fields['image'].widget = forms.ClearableFileInput(attrs={"multiple": True})