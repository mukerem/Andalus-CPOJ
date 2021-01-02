from django.contrib import admin
from .models import Contest
# Register your models here.


class ContestAdmins(admin.ModelAdmin):
    fields = ('title', 'short_name', 'active_time', 'start_time', 'end_time', 'frozen_time', 'unfrozen_time', 'deactivate_time',
              'problem', 'user', 'has_value', 'is_public', 'enable', 'last_update', 'register_date')
    filter_horizontal = ('problem', 'user')

admin.site.register(Contest, ContestAdmins)
# admin.site.register(ContestSession)