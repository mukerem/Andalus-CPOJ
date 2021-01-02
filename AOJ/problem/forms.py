from django import forms
from .models import Problem, TestCase
from authentication.validators import validate_problem_file_extension
from django.forms.widgets import TextInput
class AddProblem(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['title', 'short_name', 'pdf', 'time_limit', 'memory_limit', 'point', 'ballon', 'error', 'is_public']
        help_texts = {
            'title': "* Enter title of problem",
            'short_name': "* Enter short name of problem it must be less than 11 characters",
            'pdf': "* Choose problem pdf",
            'time_limit': "*Enter time limit of the problem in second",
            'memory_limit': "Enter memory limit of the problem in megabytes",
            'point': "*Enter point for the problem",
            'ballon': "choose ballon color for the problem",
        }
        widgets = {
            'pdf': forms.FileInput,
            'ballon': TextInput(attrs={'type': 'color'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        pdf = cleaned_data.get('pdf')
        title = cleaned_data.get('title')
        short_name = cleaned_data.get('short_name')
        time_limit = cleaned_data.get('time_limit')
        point = cleaned_data.get('point')

        if (not pdf) or (not title) or (not time_limit)  or (not point) or (not short_name):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data



class EditProblem(forms.ModelForm):

    class Meta:
        model = Problem
        fields = ['title', 'short_name', 'time_limit', 'memory_limit', 'pdf', 'point', 'ballon', 'error', 'is_public']
        help_texts = {
            'title': "* Enter title of problem",
            'short_name': "* Enter short name of problem it must be less than 11 characters",
            'pdf': "* Choose problem pdf",
            'time_limit': "*Enter time limit of the problem in second",
            'memory_limit': "Enter memory limit of the problem in megabytes",
            'point': "*Enter point for the problem",
            'ballon': "choose ballon color for the problem",
        }
        widgets = {
            'pdf': forms.FileInput,
            'ballon': TextInput(attrs={'type': 'color'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        short_name = cleaned_data.get('short_name')
        time_limit = cleaned_data.get('time_limit')
        point = cleaned_data.get('point')

        if (not title) or (not time_limit)  or (not point) or (not short_name):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data


class AddProblemZIP(forms.Form):

    file = forms.FileField(
        label='ZIP file',
        help_text='* choose ZIP file.'
    )
    
class AddTestcase(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ['input', 'output']
        help_texts = {
            'input': "* Choose sample input, the file extension must be .in",
            'output': "* Choose sample output , the file extension must be .out",
        }
 