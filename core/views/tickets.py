from django.apps import apps
from django.contrib import admin
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404

from core.models import HelpTicket
from core.models.HelpTicket import ALLOWED_ATTACHMENT_FIELDS


def admin_tickets_json(request, app_label, model_name, object_id):
    if model_name not in ALLOWED_ATTACHMENT_FIELDS:
        return JsonResponse({"tickets": []})
    # найдём модель и её ModelAdmin (если есть)
    Model = apps.get_model(app_label, model_name)
    if Model is None:
        raise Http404("Model not found")

    model_admin = admin.site._registry.get(Model)
    base_qs = model_admin.get_queryset(request) if model_admin else Model.objects.all()

    obj = get_object_or_404(base_qs, pk=object_id)
    # проверка прав: если есть ModelAdmin — используем его; иначе стандарт permission
    if model_admin:
        if not model_admin.has_view_permission(request, obj):
            return HttpResponseForbidden()
    else:
        if not request.user.has_perm(f"{app_label}.view_{model_name}"):
            return HttpResponseForbidden()

    # определим по какому полю фильтровать: имя модели в админ-классе
    # field = self.model._meta.model_name  # e.g. "dispatch", "employee", "crew"
    # filter_kw = {f"{field}__id": object_id}
    # employee = getattr(request.user, "employee", None)
    # print("employee:", employee.user)
    # if employee:
    #     qs = HelpTicket.objects.filter(
    #         assigned_to=employee,
    #         # assigned_to__user=request.user,
    #         employee__id=object_id,
    #         status__in=("send", "processing")
    #     ).select_related("assigned_to")[:25]
    # else:
    #     qs = []

    # if model_name == "employees":
    #     filter_kw = {"employee__id": object_id}
    # else:
    #     filter_kw = {f"{model_name}__id": object_id}

    filter_kw = {f"{model_name}__id": object_id}
    qs = HelpTicket.objects.filter(
        # assigned_to=employee,
        **filter_kw,
        assigned_to__user=request.user,
        status__in=("send", "processing")
    ).select_related("assigned_to")[:25]

    data = []
    for t in qs:
        data.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,  # raw value: e.g. "send", "processing"
            "priority": t.priority,  # raw value: e.g. "extreme"
            # "assigned_to": str(t.assigned_to) if t.assigned_to else None,
            # "created_by_admin": str(t.created_by_admin) if t.created_by_admin else None,
            "body": (t.body[:255] + "...") if t.body and len(t.body) > 200 else (t.body or ""),
            "document_url": t.document.url if t.document else None,
        })
    return JsonResponse({"tickets": data})
