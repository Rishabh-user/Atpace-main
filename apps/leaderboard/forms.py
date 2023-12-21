from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

from apps.leaderboard.models import BadgeDetails, PointsTable, StreakPoints, UserDrivenGoal, SystemDrivenGoal


class BadgeCreateForm(forms.ModelForm):
    '''
        Custom Badge Creation Form.
    '''
    class Meta:
        model = BadgeDetails
        fields = ['name', 'description', 'image', 'points_required', 'badge_for', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'description',
            'image',
            'points_required',
            'badge_for',
            'is_active',
            Submit('submit', 'Add')
        )


class GoalCreateForm(forms.ModelForm):
    '''
        Custom Goal Creation Form.
    '''
    class Meta:
        model = UserDrivenGoal
        fields = ['heading', 'description', 'priority_level', 'frequency', 'complete_till']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'heading',
            'description',
            'priority_level',
            'frequency',
            'complete_till',
            Submit('submit', 'Add')
        )


class PointsCreateForm(forms.ModelForm):
    '''
        Custom Points Creation Form.
    '''
    class Meta:
        model = PointsTable
        fields = ['name', 'label', 'points', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'label',
            'points',
            'comment',
            Submit('submit', 'Add')
        )


class StreakPointsForm(forms.ModelForm):
    '''
        Custom Streak Points Creation Form.
    '''
    class Meta:
        model = StreakPoints
        fields = ['name', 'duration_in_days', 'points', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'duration_in_days',
            'points',
            'comment',
            Submit('submit', 'Add')
        )


class SystemGoalCreationFrom(forms.ModelForm):
    class Meta:
        model = SystemDrivenGoal
        fields = ['heading', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            "heading",
            "description",
            Submit('submit', 'Create')
        )
