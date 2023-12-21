from django import forms
from django.db.models import Q
from apps.content.models import Channel
from apps.users.models import User
from .models import MemberInvitation, SpaceGroups, SpaceMembers, Spaces
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit


class SpaceGroupForm(forms.ModelForm):
    '''
        Space Group Creation Form.
    '''
    class Meta:
        model = SpaceGroups
        fields = ['title', 'description', 'cover_image', 'privacy',
                  'is_hidden', 'hidden_from_non_members', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'cover_image',
            'privacy',
            'is_hidden',
            'hidden_from_non_members',
            'is_active',
            Submit('submit', 'Add')
        )


class SpaceForm(forms.ModelForm):
    '''
        Space Creation Form.
    '''
    space_group = forms.ModelChoiceField(queryset=SpaceGroups.objects.filter(
        is_active=True, is_delete=False), required=True)

    class Meta:
        model = Spaces
        fields = ['title', 'description', 'space_group', 'space_type', 'cover_image',
                  'privacy', 'is_hidden', 'hidden_from_non_members', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'space_group',
            'space_type',
            'cover_image',
            'privacy',
            'is_hidden',
            'hidden_from_non_members',
            'is_active',
            Submit('submit', 'Add')
        )


class SpaceMemberForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True, is_delete=False), required=True)
    space_group = forms.ModelChoiceField(queryset=SpaceGroups.objects.filter(
        is_active=True, is_delete=False), required=True)
    # space = forms.ModelChoiceField(queryset=, required=True)

    class Meta:
        model = SpaceMembers
        fields = ['user', 'space_group', 'space', 'user_type', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        # self.fields['space'].queryset = Spaces.objects.filter(space_group__in=self.fields['space_group'].queryset, is_active=True, is_delete=False)
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'user',
            'space_group',
            'space',
            'user_type',
            'is_active',
            Submit('submit', 'Add')
        )


class InviteForm(forms.ModelForm):

    class Meta:
        model = MemberInvitation
        fields = ['invite_email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'invite_email',
            Submit('submit', 'Add')
        )
