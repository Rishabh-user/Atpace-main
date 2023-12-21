from django import forms
from .models import Channel, Content, ChannelGroup, journeyContentSetup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Row, Column
from apps.users.models import User, UserTypes, Company


class ChannelCreationFrom(forms.ModelForm):
    '''
         Channel Creation Form.
    '''
    closure_date = forms.DateField(widget=forms.SelectDateWidget)
    # company = forms.ModelChoiceField(queryset=None)

    class Meta:
        model = Channel
        fields = ["title", "short_description", "description", "channel_admin", "is_active", "image", "program_team_1", "program_team_2", "program_team_email",
                  "closure_date", "channel_type", "company", "is_test_required", "is_community_required", "category", "color", "what_we_learn", "tags", "amount", "is_paid",
                  "is_lite_signup_enable", "show_on_website", "whatsapp_notification_required", "telegram_notification_required"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        usertype = UserTypes.objects.filter(type__in=["ProgramManager", "Admin"])
        if self.request.session['user_type'] == 'ProgramManager':
            company = self.request.user.company.filter(pk=self.request.session['company_id'])
            self.fields['company'].queryset = company
        
        else:
            company = Company.objects.all()
            self.fields['company'].queryset = company

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['channel_admin'].queryset = User.objects.filter(userType__in=usertype, is_active=True, is_delete=False, is_archive=False).distinct()

        self.fields['title'].label = "Journey Name"
        self.fields['company'].label = "Organisation"
        self.fields['image'].label = "Cover"
        self.fields['channel_type'].label = "Journey Type"
        self.fields['channel_admin'].label = "Journey Admin"
        self.fields['is_community_required'].label = "Add to Community"
        self.fields['is_test_required'].label = "Pre Assesment/Survey"

        self.helper.layout = Layout(
            "title",
            "channel_type",
            "company",
            "program_team_1",
            "program_team_2",
            "program_team_email",
            "closure_date",
            "category",
            "short_description",
            Field("description", id="editor_description"),
            "channel_admin",
            "image",
            "what_we_learn",
            "tags",
            Row(
                Column('color',   type="color", css_class='form-group col-md-3 mb-0'),
                Column('is_lite_signup_enable', css_class='form-group col-md-3 mb-0'),
                Column('is_paid', css_class='form-group col-md-3 mb-0'),
                Column('amount', css_class='form-group col-md-3 mb-0')


            ),
            Row(
                Column('is_test_required', css_class='form-group col-md-3 mb-0'),
                Column('is_community_required', css_class='form-group col-md-3 mb-0'),
                Column('is_active', css_class='form-group col-md-3 mb-0'),
                Column('show_on_website', css_class='form-group col-md-3 mb-0'),
            ),
            # "whatsapp_notification_required",
            Row(
                Column('whatsapp_notification_required',   css_class='form-group col-md-12 mb-0'),
            ),

            Submit('submit', 'Add')
        )


class SubChannelCreationFrom(forms.ModelForm):
    '''
         Sub Channel Creation Form.
    '''
    class Meta:
        model = Channel
        fields = ["title", "description", "parent_id", "is_active", "channel_type", "is_test_required"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['parent_id'].label = "Select Journey"
        self.fields['parent_id'].queryset = Channel.objects.filter(
            parent_id=None, channel_type="SkillDevelopment",  is_active=True, is_delete=False)
        self.fields['title'].label = "Name Of Skill"
        self.fields['channel_type'].label = "Skill Type"
        self.fields['is_test_required'].label = "Pre Assesment/Survey"
        self.helper.layout = Layout(
            "parent_id",
            "title",
            "channel_type",
            "description",
            "is_test_required",
            "is_active",
            Submit('submit', 'Add')
        )


class ContentCreationFrom(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'image', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['image'].label = "Cover"
        self.helper.layout = Layout(
            "title",
            Field("description", id="editor_description"),
            "image",
            Submit('submit', 'Create')
        )


class CreateChannelGroupFrom(forms.ModelForm):
    class Meta:
        model = ChannelGroup
        fields = ['title', 'channel', 'channel_for', "start_mark", "end_marks"]

        widgets = {
            'channel': forms.Select(attrs={'is_delete': False}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['channel_for'].label = "Level"
        self.fields['channel'].label = "Journy"
        self.fields['channel'].queryset = Channel.objects.filter(is_delete=False, is_active=True)
        self.helper.layout = Layout(
            'title',
            'channel',
            'channel_for',
            Row(
                Column('start_mark', css_class='form-group col-md-6 mb-0'),
                Column('end_marks', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Add')
        )


class journeyContentCreationForm(forms.ModelForm):
    journey = forms.ModelChoiceField(queryset=Channel.objects.filter(
        channel_type="MentoringJourney", is_delete=False, is_active=True, is_lite_signup_enable=True))

    class Meta:
        model = journeyContentSetup
        fields = ['journey', 'learn_label', 'overview', 'pdpa_label',
                  'pdpa_description', 'video_url', 'cta_button_title', 'cta_button_action']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'journey',
            "learn_label",
            "overview",
            'pdpa_label',
            'video_url',
            'cta_button_title',
            'cta_button_action',
            Field("pdpa_description", id="editor_description"),
            Submit('submit', 'Add')
        )
