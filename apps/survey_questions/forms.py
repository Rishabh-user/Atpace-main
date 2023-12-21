from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field

from .models import Survey, SurveyLabel


class CreateSurveyForm(forms.ModelForm):
    '''
        Custom Survey Creation Form.
    '''
    class Meta:
        model = Survey
        fields = ['name', 'short_description', 'cover_image', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'cover_image',
            Field('short_description', id="editor_description"),
            'is_active',
            Submit('submit', 'Create Survey ')
        )


class CreateLableForm(forms.ModelForm):
    class Meta:
        model = SurveyLabel
        fields = ["label"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.fields['label'].label = "Level"
        self.helper.layout = Layout(
            'label',
            Submit('submit', 'Create')
        )
