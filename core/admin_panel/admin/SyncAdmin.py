# import json
#
# from django.contrib import admin
# from django.db.models import Q, Count
# from django.utils.html import format_html
# from django.utils.http import urlencode
#
# from synchronization.models.Sync import Sync
# from synchronization.models.SyncParameters import Sync_Parameters, ChangesInParameter
# from synchronization.services.SyncService import SyncService
#
#
# class SyncParametersInline(admin.TabularInline):  # admin.StackedInline
#     def get_queryset(self, request):
#         all = request.GET.get('all', 'false').lower()
#         queryset = super().get_queryset(request)
#         if all == 'true':
#             return queryset
#         return queryset.filter(removed=False)
#
#     def get_formset(self, request, obj=None, **kwargs):
#         all = request.GET.get('all', 'false').lower()
#         extra = request.GET.get('extra', 'false').lower()
#         if all == 'true':
#             self.fields = tuple(list(self.fields) + ['removed'])
#             self.readonly_fields = tuple(list(self.readonly_fields) + ['removed'])
#
#             readonly_fields = list(self.readonly_fields)
#             readonly_fields.remove('exchange_value')
#             readonly_fields.remove('privser_value')
#             readonly_fields.remove('removed')
#             self.readonly_fields = tuple(readonly_fields)
#
#         if extra != 'true':
#             fields_list = list(self.fields)
#             if 'override_value' in fields_list:
#                 fields_list.remove('override_value')
#             self.fields = tuple(fields_list)
#
#         return super().get_formset(request, obj, **kwargs)
#
#     class Media:
#         js = ("synchronization/admin_sync_page.js",)
#         css = {
#             "all": ("synchronization/admin_sync_page.css",)
#         }
#
#     def has_add_permission(self, request, obj=None):
#         return False
#
#     @admin.display(description="Exchange Property")
#     def related_exchange_property(self, obj):
#         if obj.privser_custom_fields and hasattr(obj.privser_custom_fields, 'exchange_property'):
#             if obj.privser_custom_fields.exchange_property:
#                 return obj.privser_custom_fields.exchange_property
#             else:
#                 return "-"
#
#         return "-"
#
#     @admin.display(description="Errors")
#     def custom_column(self, obj):
#         values = []
#         if obj.exchange_property_not_found:
#             values.append(f"exchange: {obj.exchange_property_not_found}")
#         if obj.privser_property_not_found:
#             values.append(f"privser: {obj.privser_property_not_found}")
#         if obj.body:
#             values.append(json.dumps(obj.body, ensure_ascii=False))
#         return ", ".join(values)
#
#     model = Sync_Parameters
#     fields = (
#         "id",
#         "privser_custom_fields",
#         "privser_datetime",
#         "privser_apply",
#         "privser_value",
#         "override_value",
#         "exchange_value",
#         "exchange_apply",
#         "exchange_datetime",
#         "related_exchange_property",
#         # "exchange_property_not_found",
#         # "privser_property_not_found",
#         # "body",
#         "custom_column",
#     )
#     readonly_fields = (
#         "id",
#         "privser_custom_fields",
#         "privser_value",
#         "exchange_value",
#         "privser_datetime",
#         "exchange_datetime",
#         "related_exchange_property",
#         # "exchange_property_not_found",
#         # "privser_property_not_found",
#         # "body",
#         "custom_column",
#     )
#
#     # extra = 0
#     # can_delete = True
#     ordering = ("id",)
#
#
# class SyncParametersChangesInline(admin.TabularInline):
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.filter(removed=True).filter(
#             Q(exchange_apply=True) | Q(privser_apply=True)
#         )
#
#     def has_add_permission(self, request, obj=None):
#         return False
#
#     @admin.display(description="Exchange Property")
#     def related_exchange_property(self, obj):
#         if obj.privser_custom_fields and hasattr(obj.privser_custom_fields, 'exchange_property'):
#             if obj.privser_custom_fields.exchange_property:
#                 return obj.privser_custom_fields.exchange_property
#             else:
#                 return "-"
#
#         return "-"
#
#     @admin.display(description="Errors")
#     def custom_column(self, obj):
#         values = []
#         if obj.exchange_property_not_found:
#             values.append(f"exchange: {obj.exchange_property_not_found}")
#         if obj.privser_property_not_found:
#             values.append(f"privser: {obj.privser_property_not_found}")
#         if obj.body:
#             values.append(json.dumps(obj.body, ensure_ascii=False))
#         return ", ".join(values)
#
#     model = ChangesInParameter
#     fields = (
#         "id",
#         "privser_custom_fields",
#         "privser_datetime",
#         "privser_apply",
#         "privser_value",
#         "exchange_value",
#         "exchange_apply",
#         "exchange_datetime",
#         "related_exchange_property",
#         # "exchange_property_not_found",
#         # "privser_property_not_found",
#         # "body",
#         "custom_column",
#     )
#     readonly_fields = (
#         "id",
#         "privser_custom_fields",
#         "privser_apply",
#         "privser_value",
#         "exchange_apply",
#         "exchange_value",
#         "privser_datetime",
#         "exchange_datetime",
#         "related_exchange_property",
#         # "exchange_property_not_found",
#         # "privser_property_not_found",
#         # "body",
#         "custom_column",
#     )
#
#     # extra = 0
#     can_delete = False
#     ordering = ("id",)
#
#
# class StatusCodeFilter(admin.SimpleListFilter):
#     title = "Status"
#     parameter_name = "status_code"
#
#     def lookups(self, request, model_admin):
#         statuses = Sync.objects.values("status_code").annotate(count=Count("status_code"))
#         return [
#             (status["status_code"], f"{Sync.StatusCode(status['status_code']).label} ({status['count']})")
#             for status in statuses
#         ]
#
#     def queryset(self, request, queryset):
#         if self.value() is not None:
#             return queryset.filter(status_code=self.value())
#         return queryset
#
#
# @admin.register(Sync)
# class SyncAdmin(FlexListAdmin):
#     def has_add_permission(self, request):
#         return False
#
#     inlines = (
#         SyncParametersInline,
#         SyncParametersChangesInline
#     )
#
#     @admin.display(description="Extra modification")
#     def extra_link(self, obj):
#         params = {"extra": "true"}
#         return format_html(
#             '<a class="button" style="background: var(--border-color);" href="?{}">Extra</a>',
#             urlencode(params)
#         )
#
#     @admin.display(description="Sync all parameters")
#     def update_all_sync_by_email(self, obj):
#         return format_html(
#             '<a class="button" href="/admin/sync/update/all/{}">Run</a>',
#             obj.id
#         )
#
#     @admin.display(description="Email")
#     def short_email(self, obj):
#         if len(obj.email) > 36:
#             return f"{obj.email[:36]}..."
#         return obj.email
#
#     list_per_page = 100
#     search_fields = ("id", "email")
#     list_display = (
#         "short_email",
#         "updated_at",
#         "status_code",
#     )
#     ordering = ("-updated_at",)
#
#     fields = (
#         ("update_all_sync_by_email", "extra_link"),
#         "employee",
#         "contact_privser",
#         "status_code",
#         ("created_at", "updated_at")
#     )
#     readonly_fields = (
#         "update_all_sync_by_email",
#         "extra_link",
#         "employee",
#         "contact_privser",
#         "created_at",
#         "updated_at"
#     )
#
#     list_editable = ("status_code",)
#     list_filter = (StatusCodeFilter,)
#
#     def save_related(self, request, form, formsets, change):
#         super().save_related(request, form, formsets, change)
#
#         sync_obj = form.instance
#
#         SyncService.update_remote_contacts(sync_obj)
#
#         status_code = SyncService.get_correct_status(sync_obj)
#         sync_obj.status_code = status_code
#         sync_obj.save()
