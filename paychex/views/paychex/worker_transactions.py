from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from paychex.models import CompanyWorkers
from paychex.services.PaychexAPIService import PaychexAPI


@staff_member_required
def worker_transactions(request, pk):
    obj = get_object_or_404(CompanyWorkers, pk=pk)
    api = PaychexAPI()
    api.authenticate()
    transactions = []
    pagination = {}
    error = None

    try:
        # on-demand: невеликий лимит по умолчанию
        resp = api.get_worker_checks(worker_id=obj.worker_id, offset=0, limit=200)
        if isinstance(resp, dict):
            transactions = resp.get("content") or []
            pagination = (resp.get("metadata") or {}).get("pagination") or {}
        elif isinstance(resp, list):
            transactions = resp
    except Exception as exc:
        error = str(exc)

    context = {
        "object": obj,
        "transactions": transactions,
        "pagination": pagination,
        "api_error": error,
    }
    return render(request, "admin/paychex/companyworkers/transactions.html", context)

@staff_member_required
def worker_transactions_json(request, pk):
    obj = get_object_or_404(CompanyWorkers, pk=pk)
    cache_key = f"paychex_worker_tx_{obj.worker_id}"

    # Предположение: кеш стоит, чтобы не дергать API при каждом F5
    data = cache.get(cache_key)
    if data is None:
        api = PaychexAPI()
        api.authenticate()
        try:
            resp = api.get_worker_checks(worker_id=obj.worker_id, offset=0, limit=200)
            # ожидаем структуру {'content': [...], 'metadata': {...}}
            transactions = resp.get("content") if isinstance(resp, dict) else (resp if isinstance(resp, list) else [])
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        data = {"transactions": transactions}
        # кеш 60 секунд — настрой по вкусу
        cache.set(cache_key, data, 1) #TODO 60
    return JsonResponse(data, safe=True)