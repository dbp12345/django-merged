"""
Signals for HelpTicket model to send push notifications
when tickets are created or updated
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from core.models.HelpTicket import HelpTicket
from core.services.PushNotificationService import PushNotificationService


@receiver(post_save, sender=HelpTicket)
def send_helpticket_notification(sender, instance, created, **kwargs):
    """
    Send push notification when HelpTicket is created or updated
    
    Sends notification to:
    - User assigned to ticket (assigned_to.user) if assigned_to exists
    - All users in assigned_to_group if assigned_to_group exists
    """
    # Only send notifications for open/pending tickets
    if instance.status not in ["send", "unresolved"]:
        return
    
    # Build notification message
    if created:
        title = "New Help Ticket"
        body = instance.title
    else:
        title = "Help Ticket Updated"
        body = instance.title
    
    # Add priority info if available
    if instance.priority and instance.priority != "-":
        priority_display = instance.get_priority_display()
        body += f" (Priority: {priority_display})"
    
    # Build URL to ticket in admin
    # ticket_url = reverse("admin:core_helpticket_change", args=[instance.pk])
    ticket_url = reverse("notifications_index")
    
    user_ids_to_notify = []
    
    # Get user from assigned_to if exists
    if instance.assigned_to and instance.assigned_to.user:
        user_ids_to_notify.append(instance.assigned_to.user.id)
    
    # Get all users from assigned_to_group if exists
    if instance.assigned_to_group:
        group_users = instance.assigned_to_group.user_set.all()
        group_user_ids = [user.id for user in group_users]
        user_ids_to_notify.extend(group_user_ids)
    
    # Remove duplicates
    user_ids_to_notify = list(set(user_ids_to_notify))
    
    # Send notifications if we have users to notify
    if user_ids_to_notify:
        PushNotificationService.send_to_users(
            user_ids=user_ids_to_notify,
            title=title,
            body=body,
            url=ticket_url
        )

