from django.db import models

class Cron_Logs(models.Model):
    class Meta:
        verbose_name = "_Cron: _logs"
        verbose_name_plural = "_Cron: _logs"

    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.body or "-"
