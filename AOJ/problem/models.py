from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from time import time
from authentication.validators import validate_problem_file_extension,\
    validate_testcase_in_file_extension, validate_testcase_out_file_extension

def problem_directory_upload(instance, filename):
    problem_title = instance.title.replace(' ', '')
    filename = filename.replace(' ','')
    return 'file/problem_{0}_{1}/{2}'.format(problem_title, instance.id, filename)
    # return 'file/problem_{0}/{1}/{2}'.format(problem_title, time() , filename)


def testcase_directory_upload(instance, filename):
    problem_title = instance.problem.title.replace(' ', '')
    filename = filename.replace(' ','')
    return 'file/problem_{0}_{1}/testcase/{2}'.format(problem_title, instance.problem.id, filename)
    # return 'file/testcase_{0}/{1}'.format(problem_title+"_"+str(instance.problem.id), filename)


# Create your models here.

class Problem(models.Model):
    title = models.CharField(max_length=200, unique=True, help_text="Enter problem title")
    short_name = models.CharField(max_length=10)
    pdf = models.FileField(upload_to=problem_directory_upload, unique=True, validators=[validate_problem_file_extension])
    point = models.DecimalField(default=1.0, decimal_places=2, max_digits=10,
                                validators=[MinValueValidator(Decimal('0.01'))])
    time_limit = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.01'))],
                                     help_text='enter time limit in second')
    memory_limit = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10,
                                       validators=[MinValueValidator(Decimal('0.01'))],
                                       help_text='Enter memory limit in mega bytes')
    ballon = models.CharField(max_length=10, default="#ffffff")
    error = models.DecimalField(default=0.0, decimal_places=20, max_digits=22,
                                       validators=[MinValueValidator(Decimal('0.00'))],
                                       help_text='maximum absolute or relative error')
    is_public =models.BooleanField(default=False)

    def __str__(self):
        return self.title


class TestCase(models.Model):
    name = models.CharField(max_length=200)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    input = models.FileField(upload_to=testcase_directory_upload, validators=[validate_testcase_in_file_extension])
    output = models.FileField(upload_to=testcase_directory_upload, validators=[validate_testcase_out_file_extension])
                                                                                                    
    class Meta:
        unique_together = ('problem', 'input', 'output')

    def __str__(self):
        return self.problem.title + ' test case ' + self.name


