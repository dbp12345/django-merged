# from django.contrib import admin
# # from exchange.models import Request_To_Exchange
# from django.utils.html import format_html
#
# from exchange.models.ContactsPropLogs import Contacts_Prop_Logs
#
#
# class ContactsPropInline(admin.TabularInline):  #admin.StackedInline
#     def has_add_permission(self, request, obj=None):
#         return False
#
#     model = Contacts_Prop_Logs
#     fields = (
#         "body",
#         "status_code",
#         "updated_at",
#     )
#     readonly_fields = (
#         # "contacts",
#         # "changed_properties",
#         # "errors",
#         # "status_code",
#         "updated_at",
#     )
#     extra = 0
#     can_delete = False
#     ordering = ("-id",)
#
# @admin.register(Request_To_Exchange)
# class RequestToExchangeAdmin(FlexListAdmin):
#     def has_add_permission(self, request):
#         return False
#
#     def preview_link(self, obj):
#         return format_html(
#             '<a target="_blank" rel="noreferrer noopener" class="button" href="/request/to/exchange/{}/preview">Preview</a>',
#             obj.id
#         )
#     preview_link.short_description = "Preview"
#
#     def execute_link(self, obj):
#         return format_html(
#             '<a class="button" style="background: var(--delete-button-bg);" href="/request/to/exchange/{}/execute">Execute</a>',
#             obj.id
#         )
#     preview_link.short_description = "Preview"
#     execute_link.short_description = "Execute"
#
#     inlines = (ContactsPropInline,)
#
#     list_per_page = 100
#     search_fields = ("email",)
#     list_display = (
#         "id",
#         "email",
#         # "request",
#         "errors",
#         "status_code",
#         "updated",
#         "preview_link",
#         "execute_link"
#     )
#     ordering = ("-updated",)
#
#     list_editable = ("status_code",)
#
#     fields = (
#         "id",
#         # "email",
#         "request",
#         "errors",
#         "critical",
#         "status_code",
#         ("created", "updated")
#     )
#     readonly_fields = (
#         "id",
#         "email",
#         "request",
#         "created",
#         "updated"
#     )
#
#     # list_filter = ("status_code", "email")
#     list_filter = ("status_code",)
