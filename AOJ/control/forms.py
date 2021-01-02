from django import forms
from .models import Setting
from competitive.models import Language

class EditScoreValues(forms.ModelForm):

    class Meta:
        model = Setting
        fields = ['name', 'value']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        value = cleaned_data.get('value')
        if (not value) or (not name):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data



class EditLanguage(forms.ModelForm):

    class Meta:
        model = Language
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        run_command = cleaned_data.get('run_command')
        compile_command = cleaned_data.get('compile_command')
        extension = cleaned_data.get('extension')
        editor_mode = cleaned_data.get('editor_mode')
        if (not name) or (not run_command) or (not compile_command) or (not extension) or (not editor_mode):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data


class LanguageRegister(forms.ModelForm):

    class Meta:
        model = Language
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        run_command = cleaned_data.get('run_command')
        compile_command = cleaned_data.get('compile_command')
        extension = cleaned_data.get('extension')
        editor_mode = cleaned_data.get('editor_mode')
        if (not name) or (not run_command) or (not compile_command) or (not extension) or (not editor_mode):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data