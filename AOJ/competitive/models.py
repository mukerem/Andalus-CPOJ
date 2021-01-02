from django.db import models
from problem.models import TestCase, Problem
from contest.models import Contest
from authentication.models import User
from time import time
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
# Create your models here.

result_lists=(('Correct', 'Correct'), ('Time Limit Exceeded', 'Time Limit Exceeded'), ('Wrong Answer', 'Wrong Answer'), 
    ('Compiler Error', 'Compiler Error'), ('Memory Limit Exceeded', 'Memory Limit Exceeded'),
    ('Run Time Error', 'Run Time Error'), ('No Output', 'No Output')
)

def testcase_output_directory_upload(instance, filename):
    problem_title = instance.submit.problem.title.replace(' ', '')
    testcase_title = instance.test_case.name.replace(' ', '')
    # filename = filename.replace(' ','')
    return 'file/user_{0}/{1}/{2}/output_{3}.out'.format(instance.submit.user.id, problem_title, instance.submit.id, testcase_title)


def submit_file_directory_upload(instance, filename):
    problem_title = instance.problem.title.replace(' ', '')
    filename = filename.replace(' ','')
    return 'file/user_{0}/{1}/{2}/{3}'.format(instance.user.id, problem_title, instance.id, filename)
    # return 'file/user_{0}/{1}/{2}/{3}'.format(instance.user.id, problem_title, time() , filename)


class Language(models.Model):
    name = models.CharField(max_length=200, unique=True)
    compile_command = models.CharField(max_length=300, help_text="use @ to represent file_name with extension and # with out extension")
    run_command = models.CharField(max_length=300, help_text='use @ to represent file_name with extension and # with out extension')
    extension = models.CharField(max_length=200, blank=True)
    editor_mode = models.CharField(max_length=200, blank=True)
    # enable = 

    def __str__(self):
        return self.name


class Submit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    result = models.CharField(max_length=200, choices=result_lists)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    submit_file = models.FileField(upload_to=submit_file_directory_upload)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=True, blank=True)
    submit_time = models.DateTimeField()

    def __str__(self):
        return self.problem.title + ' by ' + self.user.username + ' for _sid '+str(self.pk)
   

class TestcaseOutput(models.Model):
    output_file = models.FileField(upload_to=testcase_output_directory_upload)
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    submit = models.ForeignKey(Submit, on_delete=models.CASCADE)
    result = models.CharField(max_length=200, choices=result_lists)                                       
    execution_time = models.DecimalField(decimal_places=8, max_digits=12, default=0.00, validators=[MinValueValidator(Decimal('0.00'))])
    memory_usage = models.DecimalField(decimal_places=8, max_digits=12, default=0.00, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        unique_together = ('test_case', 'output_file')

    def __str__(self):
        return self.submit.__str__() + ' test case ' + self.test_case.name 
    
        
class RankcacheJury(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, limit_choices_to={'enable': True})
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__short_name': "contestant"})
    point = models.DecimalField(default=0.0, decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.00'))])
    punish_time = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return self.user.username + " on " + self.contest.title
 

class RankcachePublic(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, limit_choices_to={'enable': True})
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__short_name': "contestant"})
    point = models.DecimalField(default=0.0, decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.00'))])
    punish_time = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return self.user.username + " on " + self.contest.title
 

class ScorecacheJury(models.Model):
    rank_cache = models.ForeignKey(RankcacheJury, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    submission = models.PositiveSmallIntegerField(default=0)
    punish = models.PositiveSmallIntegerField(default=0)
    # pending = models.PositiveSmallIntegerField(default=0)
    correct_submit_time = models.DateTimeField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('rank_cache', 'problem')

    def __str__(self):
        return self.rank_cache.user.username + " on " + self.rank_cache.contest.title + ' for problem ' + self.problem.title


class ScorecachePublic(models.Model):
    rank_cache = models.ForeignKey(RankcachePublic, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    submission = models.PositiveSmallIntegerField(default=0)
    punish = models.PositiveSmallIntegerField(default=0)
    pending = models.PositiveSmallIntegerField(default=0)
    correct_submit_time = models.DateTimeField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('rank_cache', 'problem')

    def __str__(self):
        return self.rank_cache.user.username + " on " + self.rank_cache.contest.title + ' for problem ' + self.problem.title


