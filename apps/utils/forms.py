
from apps.mentor.models import Pool
from .models import Industry, JourneyCategory, Tags
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.forms.widgets import TextInput
from apps.content.models import Channel

class JourneyCategoryForm(forms.ModelForm):
    class Meta:
        model = JourneyCategory
        fields = ["category", 'color', 'icon']

        widgets = {
            "color": TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            'category',
            'color',
            'icon',
            Submit('submit', 'Create')
        )


class TagsForm(forms.ModelForm):
    class Meta:
        model = Tags
        fields = ["name", 'is_active', 'color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            'name',
            'color',
            'is_active',
            Submit('submit', 'Create')
        )


class IndustryForm(forms.ModelForm):
    class Meta:
        model = Industry
        fields = ["name", 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            'name',
            'is_active',
            Submit('submit', 'Create')
        )


class PoolForm(forms.ModelForm):
    # tags = forms.ModelMultipleChoiceField(queryset=Tags.objects.all(
    # ), widget=forms.Select(attrs={'class': 'select2', "multiple": "multiple"}))
    # industry = forms.ModelMultipleChoiceField(queryset=Industry.objects.all(
    # ), widget=forms.Select(attrs={'class': 'select2', "multiple": "multiple"}))
    journey = forms.ModelChoiceField(queryset=Channel.objects.filter(is_delete=False, is_active=True, parent_id=None, channel_type="MentoringJourney"), required=True)

    class Meta:
        model = Pool
        fields = ["name", 'journey', 'pool_by', 'is_active', 'tags', 'industry', 'company']

        # widgets = {
        #     "tags": TextInput(attrs={"class": "select2"}),
        #     "industry": TextInput(attrs={"class": "select2"}),
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(Tags.objects.filter(is_active=True))
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            'name',
            "journey",
            "company",
            "pool_by",
            'is_active',
            "tags",
            "industry",
            Submit('submit', 'Create')
        )
