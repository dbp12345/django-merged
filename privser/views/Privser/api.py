from django.http import JsonResponse
from privser.models import Request_From_Privser
from core.tasks.privser_tasks import update_from_privser_task
import json

def handle_requested_data(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        all_params = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    contact_id = all_params.get("contact_id")
    contact_email = all_params.get("email")

    if contact_id:
        Request_From_Privser.objects.create(
            request=all_params,
            email=contact_email,
            status_code=Request_From_Privser.StatusCode.NEW
        )
        update_from_privser_task.apply_async(
            kwargs={
                "contact_id": contact_id,
                "ignore_diff_properties": False,
            },
            countdown=5
        )
        return JsonResponse({'status': 'ok'}, status=200)

    Request_From_Privser.objects.create(
        request=all_params,
        email=contact_email,
        errors="ID not found",
        status_code=Request_From_Privser.StatusCode.ERROR
    )
    return JsonResponse({'status': 'error', 'message': 'ID not found'}, status=400)




    #     #For standard webhook
    #     data = json.loads(request.body)
    #     contact_email = data.get("email", None)
    #     request_from_privser = Request_From_Privser.objects.create(
    #         request=data,
    #         email=contact_email,
    #         status_code=Request_From_Privser.StatusCode.NEW
    #     )
    #
    #
    #     update_from_privser_task.apply_async(
    #         kwargs={
    #             "contact_id": data.get("contact_id", None),
    #             "ignore_diff_properties": False,
    #         },
    #         countdown=5  # timeout 5 sec
    #     )
    #
    # return JsonResponse({'status': 'ok'}, status=200)
