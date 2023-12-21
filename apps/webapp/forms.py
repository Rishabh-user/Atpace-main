from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from apps.content.models import Channel

from apps.webapp.models import GrowAtpaceTeam, HomepageJourneys, Testimonial

class HomepageJourneyForm(forms.ModelForm):
    '''
        Custom Homepage Journey Form.
    '''
    journey = forms.ModelChoiceField(queryset=Channel.objects.filter(is_delete = False, parent_id = None), required=True)
    class Meta:
        model = HomepageJourneys
        fields = ['journey']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'journey',
            Submit('submit', 'Add')
        )

class GrowAtpaceTeamForm(forms.ModelForm):
    '''
        Custom Homepage Journey Form.
    '''
    class Meta:
        model = GrowAtpaceTeam
        fields = ['name', 'country', 'position', 'linkedin_url', 'facebook_url', 'instagram_url', 'about_us', 'profile', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'country',
            'position',
            'linkedin_url',
            'facebook_url',
            'instagram_url',
            'about_us',
            'profile',
            'is_active',
            Submit('submit', 'Add')
        )

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'position', 'message']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['name'].required = False
        self.helper.layout = Layout(
            'name',
            'position',
            'message',
            Submit('submit', 'Add')
        )