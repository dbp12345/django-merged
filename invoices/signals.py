from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

from .models import Invoice

@receiver(post_save, sender=Invoice)
def set_due_date_on_create(sender, instance, created, **kwargs):
    if created and instance.due_date is None and instance.issue_date:
        instance.due_date = instance.issue_date + timedelta(days=30)
        instance.save(update_fields=['due_date'])
