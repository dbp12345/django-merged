# integrations/signals.py
from __future__ import annotations

import logging
from typing import Optional, Set

from django.db.models.signals import post_save
from django.dispatch import receiver

from contacts.models import Contact

logger = logging.getLogger(__name__)

SYNCED_FIELDS: Set[str] = {"first_name", "last_name", "email", "phone", "company", "role"}


@receiver(post_save, sender=Contact)
def contact_post_save_push_to_ghl(sender, instance: Contact, created: bool, **kwargs):
    try:
        from integrations.ghl_sync import is_sync_disabled, push_django_to_ghl
    except Exception:
        logger.exception("Could not import sync engine; skipping push.")
        return

    try:
        if is_sync_disabled():
            return

        if not instance.email:
            return

        uf = kwargs.get("update_fields")
        if uf:
            update_fields = set(uf)
            if update_fields.isdisjoint(SYNCED_FIELDS):
                return

        push_django_to_ghl(queryset=Contact.objects.filter(pk=instance.pk))

    except Exception:
        logger.exception("Immediate push failed for contact=%s", instance.pk)
