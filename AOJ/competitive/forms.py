from django import forms
from .models import Submit
# from django_ace import AceWidget


class SubmitAnswer(forms.ModelForm):
    class Meta:
        model = Submit
        fields = ['problem', 'language', 'submit_file']
    