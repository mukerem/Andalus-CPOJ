from django.db import models
from problem.models import Problem
from authentication.models import User
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import date
from datetime import datetime

# Create your models here.

class Contest(models.Model):
    title = models.CharField(max_length=200)
    short_name = models.CharField(max_length=10)
    active_time = models.DateTimeField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    frozen_time = models.DateTimeField(blank=True, null=True)
    unfrozen_time = models.DateTimeField(blank=True, null=True)
    deactivate_time = models.DateTimeField()
    problem = models.ManyToManyField(Problem, blank=True)
    user = models.ManyToManyField(User, blank=True, limit_choices_to={'is_active': True, 'role__short_name': 'contestant'})
    has_value =models.BooleanField(default=False)
    is_public =models.BooleanField(default=True)
    enable = models.BooleanField(default=True)
    last_update = models.DateTimeField(default=timezone.now)
    register_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('title', 'start_time', 'end_time')
    def __str__(self):
        return self.title


# class ContestSession(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'is_active': True})
#     contest = models.ForeignKey(Contest, blank=True, on_delete=models.CASCADE)

#     def __str__(self):
#         return "%s on contest %s" %(self.user.name, self.contest.title)