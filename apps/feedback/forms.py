from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field

from .models import FeedbackTemplate


# class CreateFeedbackForm(forms.ModelForm):
#     '''
#         Custom Feedback Creation Form.
#     '''
#     class Meta:
#         model = FeedbackTemplate
#         fields = ['name', 'short_description', 'template_for', 'company', 'journey', 'is_draft', 'is_active']

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_method = 'post'
#         self.helper.layout = Layout(
#             'name',
#             Field('short_description', id="editor_description"),
#             'template_for',
#             'company',
#             'journey',
#             'is_draft',
#             'is_active',
#             Submit('submit', 'Create Template')
#         )