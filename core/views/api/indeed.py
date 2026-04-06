from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.models import Request_From_Indeed

@csrf_exempt
def handle_requested_data_indeed(request):
    request_data = {
        "method": request.method,
        "GET": request.GET.dict(),
        "POST": request.POST.dict(),
        "BODY": request.body.decode("utf-8") if request.body else None,
    }

    request_obj = Request_From_Indeed.objects.create(
        request=request_data,
        status_code=Request_From_Indeed.StatusCode.NEW
    )

    return JsonResponse({"status": "ok", "id": request_obj.id}, status=201)

