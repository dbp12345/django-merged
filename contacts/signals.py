from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver

from .models import Contact


@receiver(pre_save, sender=Contact)
def delete_old_profile_picture(sender, instance: Contact, **kwargs):
    if not instance.pk:
        return

    try:
        old = Contact.objects.get(pk=instance.pk)
    except Contact.DoesNotExist:
        return

    old_file = old.profile_picture
    new_file = instance.profile_picture

    if old_file and old_file != new_file:
        try:
            old_file.delete(save=False)
        except Exception:
            pass


@receiver(post_delete, sender=Contact)
def delete_profile_picture_on_contact_delete(sender, instance: Contact, **kwargs):
    if instance.profile_picture:
        try:
            instance.profile_picture.delete(save=False)
        except Exception:
            pass
