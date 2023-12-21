from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from .models import MentoringTypes, TargetAudience
from django.db.models import Q

class CreateMentoringTypeForm(forms.ModelForm):
    class Meta:
        model = MentoringTypes
        fields = ["name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.fields['name'].label = "Title"
        self.fields['description'].label = "Description"
        self.helper.layout = Layout(
            'name',
            'description',
            Submit('submit', 'Create')
        )

class CreateTargetAudienceForm(forms.ModelForm):
    class Meta:
        model = TargetAudience
        fields = ["name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.fields['name'].label = "Title"
        self.fields['description'].label = "Description"
        self.helper.layout = Layout(
            'name',
            'description',
            Submit('submit', 'Create')
        )

