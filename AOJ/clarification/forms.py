from django import forms
from .models import Clarification
from authentication.models import User


class ClarificationRequest(forms.ModelForm):
    class Meta:
        model = Clarification
        fields = ['problem', 'question']


class ClarificationAnswer(forms.ModelForm):
    _pro = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': True}),
    )
    _question = forms.CharField(
        widget=forms.Textarea(attrs={'readonly': True}),
    )
    _user = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': True}),
    )

    class Meta:
        model = Clarification
        fields = ['_user', '_pro', '_question', 'answer', 'is_public']

    def clean(self):
        cleaned_data = super().clean()
        answer = cleaned_data.get('answer')

        if not(answer):
            raise forms.ValidationError(
                "Please enter answer for the question.")

        return cleaned_data


class NewClarification(forms.ModelForm):

    class Meta:
        model = Clarification
        fields = ['problem', 'answer', 'user', 'is_public']

    def clean(self):
        cleaned_data = super().clean()
        answer = cleaned_data.get('answer')
        is_public = cleaned_data.get('is_public')
        user = cleaned_data.get('user')

        if not answer:
            raise forms.ValidationError("Please correct the errors below.")

        if not(is_public or user):
            raise forms.ValidationError(
                "Select user from the list or select is_public.")

        return cleaned_data


class EditClarification(forms.ModelForm):
    _pro = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': True}),
    )
    _user = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'readonly': True}),
    )
    _question = forms.CharField(
        widget=forms.Textarea(attrs={'readonly': True}),
    )

    class Meta:
        model = Clarification
        fields = ['_pro', '_user', '_question', 'answer', 'is_public']

    def clean(self):
        cleaned_data = super().clean()
        answer = cleaned_data.get('answer')
        is_public = cleaned_data.get('is_public')
        user = cleaned_data.get('_user')

        if not(is_public or user):
            raise forms.ValidationError(
                "Select user from the list or select is_public.")

        if not answer:
            raise forms.ValidationError("Please correct the errors below.")
        return cleaned_data
