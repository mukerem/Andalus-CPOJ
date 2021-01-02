from django.db import models

# Create your models here.

class Setting(models.Model):
    name = models.CharField(max_length=200, unique=True)
    value = models.IntegerField()

    def __str__(self):
        return self.name