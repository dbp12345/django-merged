from django.db import models

class Task_Toggle(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}: {'enabled' if self.is_enabled else 'disabled'}"
