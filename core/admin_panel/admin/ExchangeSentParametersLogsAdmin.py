# from django.contrib import admin
# from exchange.models import Contacts_Prop_Logs

# @admin.register(Contacts_Prop_Logs)
# class ExchangeSentParametersLogsAdmin(FlexListAdmin):
#     def has_add_permission(self, request):
#         return False
#
#     search_fields = ("id", "email", "request_to_exchange__id")
#     list_display = (
#         "id",
#         "request_to_exchange_id",
#         "email",
#         "body",
#         "status_code",
#         "updated_at"
#     )
#     ordering = ("-id",)
#
#     fields = (
#         "body",
#         "status_code",
#         "critical",
#         ("created_at", "updated_at")
#     )
#     readonly_fields = ("email", "created_at", "updated_at",)
#
#     # list_filter = ("status_code", "email")
#     list_filter = ("status_code",)

# Register your models here.
# admin.site.register(Contacts_Prop_Logs, ExchangeSentParametersLogsAdmin)