from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core.models.HelpTicket import HelpTicket
from core.services.PushNotificationService import PushNotificationService


@staff_member_required(login_url="notifications_login")
def notifications_view(request):
    """
    Main view for notifications PWA app
    Shows Help Tickets assigned to the current user or their groups
    """
    user = request.user
    emp = getattr(user, "employee", None)
    my_groups = list(user.groups.values_list("pk", flat=True))

    # Build Q-filter to match tickets assigned to this employee, their user, or any of their groups
    mine_filter = (
        Q(assigned_to=emp) |
        Q(assigned_to__user=user) |
        Q(assigned_to_group_id__in=my_groups)
    )

    # Only show open / pending tickets
    status_filter = Q(status__in=["send", "unresolved"])

    tickets = (
        HelpTicket.objects
        .filter(mine_filter)
        .filter(status_filter)
        .distinct()
        .order_by("-priority", "-updated_at")[:25]
    )

    return render(request, "notifications/index.html", {
        "user": user,
        "tickets": tickets,
    })


@csrf_exempt
@require_http_methods(["POST"])
def send_notification_view(request):
    """
    View to send push notifications to users
    Supports both form data and JSON requests
    """
    try:
        import json

        # Try to get data from JSON first, then from POST
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                data = {}
        else:
            data = request.POST.dict()

        title = data.get("title", "")
        body = data.get("body", "")
        url = data.get("url", "/notifications/")
        user_id = data.get("user_id", None)
        user_ids = data.get("user_ids", None)  # Support for multiple users

        if not title or not body:
            return JsonResponse({"success": False, "error": "Title and body are required"})

        # Send to specific user if user_id provided
        if user_id:
            result = PushNotificationService.send_to_user(
                user_id=int(user_id),
                title=title,
                body=body,
                url=url
            )
            return JsonResponse(result)

        # Send to multiple users if user_ids provided
        if user_ids:
            if isinstance(user_ids, str):
                # If it's a string, try to parse as JSON or comma-separated
                try:
                    user_ids = json.loads(user_ids)
                except (json.JSONDecodeError, ValueError):
                    user_ids = [int(uid.strip()) for uid in user_ids.split(",") if uid.strip()]
            elif not isinstance(user_ids, list):
                user_ids = [user_ids]

            result = PushNotificationService.send_to_users(
                user_ids=[int(uid) for uid in user_ids],
                title=title,
                body=body,
                url=url
            )
            return JsonResponse(result)

        # Send to all subscribed users
        result = PushNotificationService.send_to_all(
            title=title,
            body=body,
            url=url
        )
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
