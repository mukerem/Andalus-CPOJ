from django.db import models
from problem.models import Problem
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Create your models here.

class Statistics(models.Model):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE)
    total_submissions = models.PositiveIntegerField(default=0)
    accurate_submissions = models.PositiveIntegerField(default=0)
    total_users = models.PositiveIntegerField(default=0)
    accurate_users = models.PositiveIntegerField(default=0)
    is_active =models.BooleanField(default=True)
    # difficulty =  models.DecimalField(default=5.5, decimal_places=1, max_digits=2,
    #                             validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('9.9'))])

    def __str__(self):
        return self.problem.title

