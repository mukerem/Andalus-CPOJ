from django import forms
from django.forms import ChoiceField
from .models import Contest
from problem.models import Problem
from django.utils import timezone
from datetime import datetime
from django.contrib.admin.widgets import FilteredSelectMultiple
from datetimewidget.widgets import DateTimeWidget
from authentication.models import User
class AddContest(forms.ModelForm):
    
    class Meta:
        model = Contest
        fields = ['title', 'short_name', 'active_time', 'start_time', 'end_time', 'frozen_time', 'unfrozen_time', 'deactivate_time',
                  'problem', 'user', 'has_value', 'is_public', 'enable']
        date_time_options = {
            'format': 'yyyy-mm-dd hh:ii',
            'todayBtn': 'true',
            'autoclose': 'true',
            'todayHighlight': 'true',
            'pickerPosition': 'bottom-right',
            }

        widgets = {
            'problem': FilteredSelectMultiple(('tags'), is_stacked=True,),
            'user': FilteredSelectMultiple(('tags'), is_stacked=True),
            'active_time': DateTimeWidget(attrs={'id': '1'},options=date_time_options,),
            'start_time': DateTimeWidget(attrs={'id': '2'},options=date_time_options,),
            'end_time': DateTimeWidget(attrs={'id': '3'},options=date_time_options,),
            'frozen_time': DateTimeWidget(attrs={'id': '4'},options=date_time_options,),
            'unfrozen_time': DateTimeWidget(attrs={'id': '5'},options=date_time_options,),
            'deactivate_time': DateTimeWidget(attrs={'id': '6'},options=date_time_options,),
        
        }

        
    # class Media:
    #     # css = {'all': ('/static/files/admin/css/widget.css', ),}
    #     js = ('/admin/jsi18n',)

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        short_name = cleaned_data.get('short_name')
        active_time = cleaned_data.get('active_time')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        frozen_time = cleaned_data.get('frozen_time')
        unfrozen_time = cleaned_data.get('unfrozen_time')
        deactivate_time = cleaned_data.get('deactivate_time')
        # user = cleaned_data.get('user')

        if (not title) or(not short_name) or (not active_time) or (not start_time) or (not end_time):
            raise forms.ValidationError("Please correct the errors below.")

        now = timezone.now()
        # if start_time < now:
        #     raise forms.ValidationError("start time must be after now( " + str(datetime.now())+' )')
        if active_time > start_time:
            raise forms.ValidationError("Active time must be before start time.")
        if end_time < start_time:
            raise forms.ValidationError("Start time must be before end time.")
        if frozen_time and frozen_time > end_time:
            raise forms.ValidationError("Frozen time must be before end time.")
        if unfrozen_time and unfrozen_time < end_time:
            raise forms.ValidationError("Unfrozen time must be after end time.")
        if deactivate_time < end_time:
            raise forms.ValidationError("Deactivate time must be after end time.")

        # for i in user:
        #     try:
        #         cont = ContestSession.objects.get(user=i)
        #         activate = cont.contest.active_time
        #         deactivate = cont.contest.deactivate_time
        #         if activate < active_time and active_time < deactivate or activate < deactivate_time and deactivate_time < deactivate :
        #             raise forms.ValidationError("user %s is active on contest %s" %(i, cont.contest))
        #     except ContestSession.DoesNotExist:
        #         pass

        return cleaned_data


class EditContest(forms.ModelForm):

    class Meta:
        model = Contest
        fields = ['title', 'short_name', 'active_time', 'start_time', 'end_time', 'frozen_time', 'unfrozen_time', 'deactivate_time',
                  'problem', 'user', 'has_value', 'is_public', 'enable']
        date_time_options = {
            'format': 'yyyy-mm-dd hh:ii',
            'todayBtn': 'true',
            'autoclose': 'true',
            'todayHighlight': 'true',
            'pickerPosition': 'bottom-right',
            }

    
        widgets = {
            'problem': FilteredSelectMultiple(('tags'), is_stacked=True),
            'user': FilteredSelectMultiple(('tags'), is_stacked=True),
            'active_time': DateTimeWidget(attrs={'id': '1'},options=date_time_options,),
            'start_time': DateTimeWidget(attrs={'id': '2'},options=date_time_options,),
            'end_time': DateTimeWidget(attrs={'id': '3'},options=date_time_options,),
            'frozen_time': DateTimeWidget(attrs={'id': '4'},options=date_time_options,),
            'unfrozen_time': DateTimeWidget(attrs={'id': '5'},options=date_time_options,),
            'deactivate_time': DateTimeWidget(attrs={'id': '6'},options=date_time_options,),
        
        }

    # class Media:
    #     js = ('/admin/jsi18n',)

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        short_name = cleaned_data.get('short_name')
        active_time = cleaned_data.get('active_time')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        frozen_time = cleaned_data.get('frozen_time')
        unfrozen_time = cleaned_data.get('unfrozen_time')
        deactivate_time = cleaned_data.get('deactivate_time')
        # user = cleaned_data.get('user')

        if (not title) or(not short_name) or (not active_time) or (not start_time) or (not end_time):
            raise forms.ValidationError("Please correct the errors below.")

        if active_time > start_time:
            raise forms.ValidationError("Active time must be before start time.")
        if end_time < start_time:
            raise forms.ValidationError("Start time must be before end time.")
        if frozen_time and frozen_time > end_time:
            raise forms.ValidationError("Frozen time must be before end time.")
        if unfrozen_time and unfrozen_time < end_time:
            raise forms.ValidationError("Unfrozen time must be after end time.")
        if deactivate_time < end_time:
            raise forms.ValidationError("Deactivate time must be after end time.")
            
        
        # for i in user:
        #     try:
        #         cont = ContestSession.objects.get(user=i)
        #         activate = cont.contest.active_time
        #         deactivate = cont.contest.deactivate_time
        #         if activate < active_time and active_time < deactivate or activate < deactivate_time and deactivate_time < deactivate :
        #             raise forms.ValidationError("user %s is active on contest %s" %(i, cont.contest))
        #     except ContestSession.DoesNotExist:
        #         pass
        return cleaned_data
