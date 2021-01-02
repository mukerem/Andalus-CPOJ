from django import forms
from .models import User, Campus, Role
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import check_password
from django.contrib.admin.widgets import FilteredSelectMultiple


class PublicUserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'name', 'email', 'password1', 'password2')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        if len(password1) < 6:
            raise forms.ValidationError(
                "Passwords length must be above 6 digits")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EditMyProfile(forms.ModelForm):
    # _username = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': True}),
    # )

    # # _campus = forms.CharField(
    # #     widget=forms.TextInput(attrs={'readonly': True}),
    # # )

    # _register_date = forms.DateField(
    #     widget=forms.DateInput(attrs={'readonly': True}),
    # )

    # _rating = forms.DecimalField(
    #     widget=forms.TextInput(attrs={'readonly': True}),
    # )
    class Meta:
        model = User
        fields = ['username', 'name', 'email',
                  'campus', 'rating', 'register_date']
        widgets = {
            'username': forms.TextInput(attrs={'readonly': True}),
            'rating': forms.TextInput(attrs={'readonly': True}),
            'register_date': forms.DateInput(attrs={'readonly': True}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        campus = cleaned_data.get('campus')
        if (not name) or (not campus):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data


class EditUserProfile(forms.ModelForm):

    class Meta:
        model = User
        exclude = ['password', 'role', 'last_login', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'readonly': True}),
            'register_date': forms.DateInput(attrs={'readonly': True}),
            'rating': forms.TextInput(attrs={'readonly': True}),
        }

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        name = cleaned_data.get('name')
        campus = cleaned_data.get('campus')
        if (not username) or (not name) or (not campus):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data


class AddUser(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'name', 'email', 'role', 'campus', ]

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        name = cleaned_data.get('name')
        role = cleaned_data.get('role')
        campus = cleaned_data.get('campus')

        if (not username) or (not name) or (not role) or (not campus):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data


class CSVUserUpload(forms.Form):
    file = forms.FileField(
        label='csv',
        widget=forms.FileInput(),
        help_text='* choose csv file.'

    )


class ChangePassword(forms.Form):
    def __init__(self, *args, **kwargs):
        self.password = kwargs.pop('password', None)
        super(ChangePassword, self).__init__(*args, **kwargs)

    old_password = forms.CharField(
        max_length=1024,
        widget=forms.PasswordInput(),
    )
    password_regex = RegexValidator(
        regex=r'^\S{6,1024}',
        message='password must be at least 6 character'
    )
    new_password = forms.CharField(
        label='New password:',
        validators=[password_regex],
        max_length=1024,
        widget=forms.PasswordInput(),
        help_text='minimum 6 character'
    )
    confirm = forms.CharField(
        label='New password confirmation:',
        max_length=1024,
        widget=forms.PasswordInput(),
    )

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm')
        if (not old_password) or (not new_password) or (not confirm_password):
            raise forms.ValidationError("Please correct the errors below.")

        if check_password(old_password, self.password):
            if new_password:
                if new_password == confirm_password:
                    return
                else:
                    raise forms.ValidationError("password is not confirmed")
        else:
            raise forms.ValidationError(
                "Your old password was entered incorrectly. Please enter it again.")

        return cleaned_data


class EditCampus(forms.ModelForm):

    class Meta:
        model = Campus
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        short_name = cleaned_data.get('short_name')
        name = cleaned_data.get('name')
        logo = cleaned_data.get('logo')
        country = cleaned_data.get('country')
        if (not short_name) or (not name) or (not logo) or (not country):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data


class CampusRegister(forms.ModelForm):

    class Meta:
        model = Campus
        fields = ['name', 'short_name', 'logo', 'country']

    def clean(self):
        cleaned_data = super().clean()
        short_name = cleaned_data.get('short_name')
        name = cleaned_data.get('name')
        logo = cleaned_data.get('logo')
        country = cleaned_data.get('country')
        if (not short_name) or (not name) or (not logo) or (not country):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data
