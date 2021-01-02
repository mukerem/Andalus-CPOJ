from django.db import models
from contest.models import Contest
from authentication.models import User
from problem.models import Problem

# Create your models here.

class Clarification(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, limit_choices_to={'role__short_name': 'contestant'})
    question = models.TextField()
    answer = models.TextField()
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, blank=True, null=True)
    send_time = models.DateTimeField()
    is_public = models.BooleanField(default=False)
    status = models.BooleanField(default=False)

    def __str__(self):
        return 'from ' + self.user.username + ' in ' + self.question[:20]
       
