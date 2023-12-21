from django import forms
from crispy_forms.helper import FormHelper
from apps.community.models import WeeklyjournalsTemplate
from crispy_forms.layout import Layout, Submit, Field


class WeeklyjournalsTemplateFrom(forms.ModelForm):
    class Meta:
        model = WeeklyjournalsTemplate
        fields = ['title', 'learning_journal', 'is_active']

        widgets = {
            'channel': forms.Select(attrs={'is_delete': False}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            Field("learning_journal", id="editor_description"),
            'is_active',
            Submit('submit', 'Add')
        )
