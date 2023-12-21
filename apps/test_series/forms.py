from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

from .models import TestSeries


class CreateTestForm(forms.ModelForm):
    '''
        Custom Survey Creation Form.
    '''
    class Meta:
        model = TestSeries
        fields = ['name', 'auto_check', 'cover_image', 'short_description', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'auto_check',
            'cover_image',
            'short_description',
            'is_active',
            Submit('submit', 'Create')
        )
