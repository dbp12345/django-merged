"""
Service for sending push notifications to users via webpush
"""
from typing import Optional, List, Dict, Any
from django.contrib.auth import get_user_model
from webpush import send_user_notification
from webpush.models import PushInformation

User = get_user_model()


class PushNotificationService:
    """
    Service for sending push notifications to users.
    
    Usage:
        # Send to specific user
        result = PushNotificationService.send_to_user(
            user_id=1,
            title="New notification",
            body="You have a new message",
            url="/notifications/"
        )
        
        # Send to multiple users
        result = PushNotificationService.send_to_users(
            user_ids=[1, 2, 3],
            title="New notification",
            body="You have a new message"
        )
        
        # Send to all subscribed users
        result = PushNotificationService.send_to_all(
            title="Announcement",
            body="Important update"
        )
    """
    
    DEFAULT_ICON = "/static/notifications/pwa/icon.png"
    DEFAULT_TTL = 1000
    
    @classmethod
    def _build_payload(
        cls,
        title: str,
        body: str,
        url: Optional[str] = None,
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build notification payload
        
        Args:
            title: Notification title
            body: Notification body text
            url: Optional URL to open when notification is clicked
            icon: Optional icon URL
            
        Returns:
            Dictionary with notification payload
        """
        payload = {
            "head": title,
            "body": body,
            "icon": icon or cls.DEFAULT_ICON,
        }
        
        if url:
            payload["url"] = url
            
        return payload
    
    @classmethod
    def send_to_user(
        cls,
        user_id: int,
        title: str,
        body: str,
        url: Optional[str] = None,
        icon: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send notification to a specific user
        
        Args:
            user_id: ID of the user to send notification to
            title: Notification title
            body: Notification body text
            url: Optional URL to open when notification is clicked
            icon: Optional icon URL
            ttl: Optional time to live in seconds
            
        Returns:
            Dictionary with success status and message/error
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return {
                "success": False,
                "error": f"User with id={user_id} does not exist"
            }
        
        if not PushInformation.objects.filter(user=user).exists():
            return {
                "success": False,
                "error": "User has no push subscription"
            }
        
        try:
            payload = cls._build_payload(title, body, url, icon)
            send_user_notification(
                user=user,
                payload=payload,
                ttl=ttl or cls.DEFAULT_TTL
            )
            return {
                "success": True,
                "message": f"Notification sent to user {user_id}",
                "user_id": user_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    @classmethod
    def send_to_users(
        cls,
        user_ids: List[int],
        title: str,
        body: str,
        url: Optional[str] = None,
        icon: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send notification to multiple users
        
        Args:
            user_ids: List of user IDs to send notification to
            title: Notification title
            body: Notification body text
            url: Optional URL to open when notification is clicked
            icon: Optional icon URL
            ttl: Optional time to live in seconds
            
        Returns:
            Dictionary with success status, count of sent notifications, and errors
        """
        if not user_ids:
            return {
                "success": False,
                "error": "No user IDs provided"
            }
        
        users = User.objects.filter(id__in=user_ids)
        payload = cls._build_payload(title, body, url, icon)
        
        sent = 0
        errors = []
        
        for user in users:
            if not PushInformation.objects.filter(user=user).exists():
                errors.append({
                    "user_id": user.id,
                    "error": "User has no push subscription"
                })
                continue
            
            try:
                send_user_notification(
                    user=user,
                    payload=payload,
                    ttl=ttl or cls.DEFAULT_TTL
                )
                sent += 1
            except Exception as e:
                errors.append({
                    "user_id": user.id,
                    "error": str(e)
                })
        
        return {
            "success": sent > 0,
            "sent": sent,
            "total": len(user_ids),
            "errors": errors
        }
    
    @classmethod
    def send_to_all(
        cls,
        title: str,
        body: str,
        url: Optional[str] = None,
        icon: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send notification to all users with push subscriptions
        
        Args:
            title: Notification title
            body: Notification body text
            url: Optional URL to open when notification is clicked
            icon: Optional icon URL
            ttl: Optional time to live in seconds
            
        Returns:
            Dictionary with success status, count of sent notifications, and errors
        """
        subscribed_user_ids = (
            PushInformation.objects
            .select_related("user")
            .values_list("user_id", flat=True)
            .distinct()
        )
        
        if not subscribed_user_ids:
            return {
                "success": False,
                "error": "No users with push subscription"
            }
        
        return cls.send_to_users(
            user_ids=list(subscribed_user_ids),
            title=title,
            body=body,
            url=url,
            icon=icon,
            ttl=ttl
        )

