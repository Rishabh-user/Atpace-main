from apps.users.forms import DateInput
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from django.db.models import Q
from apps.program_manager_panel.models import Subscription, SubscriptionOffer, MentorMenteeRatio


class SubscriptionForm(forms.ModelForm):
    '''
        Subscription Form
    '''

    class Meta:
        model = Subscription
        fields = ['title', 'description', 'terms_conditions', 'price', 'duration', 'sub_type', 'on_offer',
                  'duration_type', 'is_active', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_type'].label = "Subscription Type"
        self.fields['price'].widget.attrs['min'] = 0
        self.fields['duration'].widget.attrs['min'] = 1
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'terms_conditions',
            Row(
                Column('price', css_class='form-group col-md-6 mb-0'),
                Column('sub_type', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('duration', css_class='form-group col-md-6 mb-0'),
                Column('duration_type', css_class='form-group col-md-6 mb-0'),
            ),
            # Row(
            #     Column('is_trial', css_class='form-group col-md-4 mb-0'),
            #     Column('trial_duration', css_class='form-group col-md-4 mb-0'),
            #     Column('trial_period', css_class='form-group col-md-4 mb-0'),
            # ),
            Row(
                Column('on_offer', css_class='form-group col-md-6 mb-0'),
                Column('is_active', css_class='form-group col-md-6 mb-0'),
            ),
            Submit('submit', 'Create')
        )


class SubscriptionOfferForm(forms.ModelForm):
    '''
        Subscription offer Form
    '''

    class Meta:
        model = SubscriptionOffer
        fields = ['title', 'terms_conditions', 'discount_percentage', 'end_date',
                  'start_date', 'discount_price', 'is_active', 'subscription']
        widgets = {
            'start_date': DateInput(),
            'end_date': DateInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'terms_conditions',
            'subscription',
            Row(
                Column('discount_percentage', css_class='form-group col-md-6 mb-0'),
                Column('discount_price', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('end_date', css_class='form-group col-md-6 mb-0'),
            ),
            # Row(
            #     Column('duration', css_class='form-group col-md-6 mb-0'),
            #     Column('duration_type', css_class='form-group col-md-6 mb-0'),
            # ),
            Row(
                Column('is_active', css_class='form-group col-md-12 mb-0'),
            ),
            Submit('submit', 'Create')
        )


class UpdateSubscriptionOfferForm(forms.ModelForm):
    '''
        Subscription offer Form
    '''

    class Meta:
        model = SubscriptionOffer
        fields = ['title', 'terms_conditions', 'discount_percentage', 'end_date',
                  'start_date', 'discount_price', 'is_active', 'subscription']

        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'terms_conditions',
            'subscription',
            Row(
                Column('discount_percentage', css_class='form-group col-md-6 mb-0'),
                Column('discount_price', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('end_date', css_class='form-group col-md-6 mb-0'),
            ),
            # Row(
            #     Column('duration', css_class='form-group col-md-6 mb-0'),
            #     Column('duration_type', css_class='form-group col-md-6 mb-0'),
            # ),
            Row(
                Column('is_active', css_class='form-group col-md-12 mb-0'),
            ),
            Submit('submit', 'Create')
        )


class MentorMenteeRatioForm(forms.ModelForm):
    '''
        Mentor Mentee Ratio Form
    '''
    subscription = forms.ModelChoiceField(queryset=Subscription.objects.filter(is_active=True, is_delete=False), required=True)

    class Meta:
        model = MentorMenteeRatio
        fields = ['subscription', 'max_mentor', 'max_learner', 'learners_per_mentor', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'subscription',
            'max_mentor',
            'max_learner',
            'learners_per_mentor',
            Submit('submit', 'Create')
        )
