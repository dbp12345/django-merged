from django.db import models
from django.contrib.auth.models import User as DjangoAdminUser

class Saved_Filter_Order(models.Model):
    user = models.OneToOneField(DjangoAdminUser, on_delete=models.CASCADE)
    order = models.JSONField()

    def __str__(self):
        return self.user.username or "-"
