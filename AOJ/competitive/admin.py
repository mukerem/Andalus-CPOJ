from django.contrib import admin
from .models import Language, Submit, TestcaseOutput, RankcachePublic, RankcacheJury,\
		ScorecacheJury,ScorecachePublic
# Register your models here.

admin.site.register(Language)
admin.site.register(Submit)
admin.site.register(TestcaseOutput)
admin.site.register(RankcacheJury)
admin.site.register(RankcachePublic)
admin.site.register(ScorecacheJury)
admin.site.register(ScorecachePublic)