from urllib.parse import urlencode

from django.conf import settings
from django.db.models import Q
from django.test import RequestFactory
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.modules import DashboardModule

from core.models import Saved_Filter
from core.models.HelpTicket import HelpTicket
from core.views.metrics_charts import metrics_charts_dashboard
from dispatch.models.Equipment import EquipmentType

SPECIAL_USERS_SET = {u.strip().lower() for u in settings.SPECIAL_USERS}
# from grappelli.dashboard.utils import get_admin_site_name


class ChartModule(DashboardModule):
    template = "admin/charts/chart_dashboard.html"

    def __init__(self, **kwargs):
        super().__init__(title="Charts", column=3, **kwargs)

    def init_with_context(self, context):
        request = context.get("request")

        if request:
            response = metrics_charts_dashboard(request)
            context["chart_content"] = (
                response.content.decode("utf-8") if hasattr(response, "content") else ""
            )
        else:
            fake_request = RequestFactory().get(reverse("metrics_charts_dashboard"))
            response = metrics_charts_dashboard(fake_request)
            context["chart_content"] = (
                response.content.decode("utf-8") if hasattr(response, "content") else ""
            )


class EquipmentTypeListModule(modules.LinkList):
    """Custom module to display list of EquipmentType objects"""

    def __init__(self, *args, **kwargs):
        # Устанавливаем CSS класс для wrapper'а модуля
        kwargs.setdefault("css_classes", [])
        if "equipment-type-list" not in kwargs["css_classes"]:
            kwargs["css_classes"].append("equipment-type-list")
        super().__init__(*args, **kwargs)

    def init_with_context(self, context):
        equipment_types = EquipmentType.objects.all().order_by("name")
        self.children = [
            {
                "title": str(et),
                "url": reverse("admin:dispatch_equipment_changelist")
                + f"?equipment_type__id__exact={et.pk}",
                "external": False,
            }
            for et in equipment_types
        ]
        super().init_with_context(context)


class MyHelpTicketsModule(modules.LinkList):
    """Custom module to display Help Tickets assigned to the current user or their groups."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_with_context(self, context):
        request = context.get("request")
        if not request:
            self.children = []
            super().init_with_context(context)
            return

        user = request.user
        emp = getattr(user, "employee", None)
        my_groups = list(user.groups.values_list("pk", flat=True))

        # Build Q-filter to match tickets assigned to this employee, their user, or any of their groups
        mine_filter = (
            Q(assigned_to=emp) |
            Q(assigned_to__user=user) |
            Q(assigned_to_group_id__in=my_groups)
        )

        # Only show open / pending tickets; you can change this logic as needed
        # Example: Only show tickets with status not 'completed'
        status_filter = Q(status__in=["send", "unresolved"])

        tickets = (
            HelpTicket.objects
            .filter(mine_filter)
            .filter(status_filter)
            .distinct()
            .order_by("-priority", "-updated_at")[:25]
        )

        self.children = [
            {
                "title": str(ticket),
                "url": reverse("admin:core_helpticket_change", args=[ticket.pk]),
                "external": False,
            }
            for ticket in tickets
        ]
        super().init_with_context(context)


class CustomIndexDashboard(Dashboard):
    columns = 3

    class Media:
        # js = ("npm/chart.js")
        css = {"all": ("grappelli/css/custom_dashboard.css",)}

    def init_with_context(self, context):
        user = context["request"].user
        # site_name = get_admin_site_name(context)

        saved_filters = Saved_Filter.objects.filter(dashboard=True).order_by("order")

        # Формируем список ссылок на сохранённые фильтры
        filter_links = [
            {
                "title": f"{f.name}",
                "url": reverse("employees_table") + "?" + urlencode(f.params),
                "external": False,
            }
            for f in saved_filters
        ]

        self.children.append(
            modules.LinkList(
                _("Employees"),
                column=1,
                children=[
                    {
                        "title": "Employees",
                        "url": reverse("employees_table"),
                        "external": False,
                    },
                    *filter_links,
                ],
            )
        )

        # self.children.append(modules.ModelList(
        #     _("Company original"),
        #     column=1,
        #     collapsible=False,
        #     models=(
        #         "company.models.Employees.Employees",
        #     )
        # ))

        self.children.append(
            modules.ModelList(
                _("Objects"),
                column=1,
                collapsible=True,
                css_classes=("collapse closed grp-closed g-d-12",),
                models=(
                    "company.models.Employees.DispatchingStatus",
                    "company.models.Employees.EmergencyContact",
                    "company.models.Employees.MSPA",
                    # "company.models.Employees.IdentificationDocuments",
                    "company.models.Employees.DriverLicense",
                    "company.models.Employees.SocialSecurityNumber",
                    "company.models.Employees.MedicalCard",
                    "company.models.Employees.Passport",
                    "company.models.Employees.CompanyManifest",
                    "company.models.Employees.DrugTest",
                    "company.models.Employees.NomexCheckOut",
                    "company.models.Employees.NomexCheckIn",
                    "company.models.Employees.EmploymentPacket",
                    "company.models.Employees.IQCCard",
                    "company.models.Employees.Interaction",
                    "company.models.Employees.TaskBook",
                    "company.models.Employees.Availability",
                    "company.models.Employees.CurrentAssigned",
                    "company.models.Employees.RateOfPay",
                    # "company.models.Employees.Draws",
                ),
            )
        )

        self.children.append(
            modules.LinkList(
                _("Settings"),
                column=1,
                collapsible=True,
                css_classes=("collapse closed grp-closed g-d-12",),
                children=[
                    {
                        "title": _("Privser contacts"),
                        "url": reverse("admin:privser_contacts_changelist"),
                        "external": True,
                    },
                    {
                        "title": _("Properties"),
                        "url": reverse("admin:exchange_contacts_prop_changelist"),
                        "external": True,
                    },
                    {
                        "title": _("Synchronized fields"),
                        "url": reverse("admin:privser_custom_fields_changelist"),
                        "external": True,
                    },
                ],
            )
        )

        self.children.append(
            modules.ModelList(
                _("Logs"),
                column=1,
                collapsible=False,
                # css_classes=("collapse closed",),
                models=(
                    # "synchronization.models.Sync.*",
                    "synchronization.models.SyncDeliveryLogs.Sync_Delivery_Logs",
                    # "synchronization.models.SyncParametersLogs.Sync_Parameters_Logs",
                    "company.models.EmployeeChangeQueue.Employee_Change_Queue",
                    "core.models.MqttLog.Mqtt_Log",
                ),
            )
        )

        self.children.append(
            modules.Group(
                title=_("Axes"),
                column=1,
                collapsible=True,
                css_classes=("collapse closed grp-closed g-d-12",),
                children=[
                    modules.ModelList(
                        "",
                        models=(
                            # "axes.models.AccessAttempt",
                            # "axes.models.AccessLog",
                            # "axes.models.AccessFailureLog",
                            "axes.*",
                        ),
                    ),
                ],
            )
        )

        self.children.append(
            modules.Group(
                title=_("Dispatch"),
                column=2,
                collapsible=False,
                # css_classes=["dispatch-links"],
                children=[
                    modules.LinkList(
                        "",
                        children=[
                            {
                                "title": _("Crews management"),
                                "url": reverse("crews_management"),
                                "external": True,
                            },
                            {
                                "title": _("Dispatch"),
                                "url": reverse("admin:dispatch_dispatch_changelist"),
                                "external": False,
                            },
                            {
                                "title": _("Fire crews (list)"),
                                "url": reverse("admin:company_firecrew_changelist"),
                                "external": False,
                            },
                            {
                                "title": _("Find by crwb"),
                                "url": reverse("find_by_crwb"),
                                "external": True,
                            },
                        ],
                    ),
                ],
            )
        )

        # self.children.append(modules.ModelList(
        #     _("Equipment"),
        #     column=2,
        #     collapsible=False,
        #     # css_classes=("collapse closed",),
        #     models=(
        #         # "dispatch.models.Dispatch.*",
        #         # "dispatch.models.Dispatch.Dispatch",
        #         "dispatch.models.Dispatch.Equipment_group",
        #         # "dispatch.models.Contracts.Contracts",
        #         # "dispatch.models.Invoice.Invoice",
        #         "dispatch.models.Dispatch.Truck",
        #         "dispatch.models.Dispatch.Phone",
        #         "dispatch.models.Dispatch.Radio",
        #         "dispatch.models.Dispatch.Saw",
        #         "dispatch.models.Dispatch.Nomex",
        #         "dispatch.models.VehicleCheckout.VehicleCheckout",
        #         # "dispatch.models.*",
        #     ),
        # ))
        self.children.append(
            modules.Group(
                title=mark_safe(
                    format_html(
                        '{} <a href="{}" style="font-size: 0.9em; color: #999; float: right;"> _new</a>',
                        _("Equipment"),
                        reverse("admin:dispatch_equipmenttype_changelist"),
                    )
                ),
                column=2,
                collapsible=False,
                children=[
                    modules.ModelList(
                        "",
                        models=(
                            # "dispatch.models.Dispatch.*",
                            # "dispatch.models.Dispatch.Dispatch",
                            "dispatch.models.Dispatch.Equipment_group",
                            # "dispatch.models.Contracts.Contracts",
                            # "dispatch.models.Invoice.Invoice",
                            "dispatch.models.Dispatch.Truck",
                            "dispatch.models.Dispatch.Phone",
                            "dispatch.models.Dispatch.Radio",
                            "dispatch.models.Dispatch.Saw",
                            # "dispatch.models.Dispatch.Nomex",
                            # "dispatch.models.VehicleCheckout.VehicleCheckout",
                            "dispatch.models.Equipment.Factory",
                            # "dispatch.models.Equipment.Equipment",
                            # "dispatch.models.Equipment.EquipmentType",
                        ),
                    ),
                    EquipmentTypeListModule(
                        _(""),
                        css_classes=["equipment-type-list"],
                    ),
                    # modules.ModelList(
                    #     "",
                    #     models=(
                    #         "dispatch.models.VehicleCheckout.VehicleCheckout",
                    #         "dispatch.models.Equipment.Factory",
                    #     ),
                    # ),
                    modules.LinkList(
                        "",
                        children=[
                            # {
                            #     "title": _("Equipment Type"),
                            #     "url": reverse("admin:dispatch_equipmenttype_changelist"),
                            #     "external": False,
                            # },
                            {
                                "title": _("Vehicle Checkouts"),
                                "url": reverse(
                                    "admin:dispatch_vehiclecheckout_changelist"
                                ),
                                "external": True,
                            },
                            {
                                "title": _("Action Required"),
                                "url": reverse("needs_maintenance"),
                                "external": True,
                            },
                        ],
                    ),
                ],
            )
        )

        self.children.append(
            modules.Group(
                title=mark_safe(
                    format_html(
                        '{} <a href="{}" style="font-size: 0.9em; color: #999; float: right;"> _new</a>',
                        _("Inspection"),
                        reverse("admin:dispatch_inspectiontype_changelist"),
                    )
                ),
                column=2,
                collapsible=False,
                children=[
                    modules.ModelList(
                        "",
                        models=(
                            "dispatch.models.Inspection.Inspection",
                            # "dispatch.models.Inspection.InspectionType",
                        ),
                    ),
                    modules.LinkList(
                        _(""),
                        children=[
                            {
                                "title": _("EAV Settings"),
                                "url": reverse("admin:app_list", args=["eav"]),
                                "external": True,
                            },
                        ],
                    ),
                    # modules.ModelList(
                    #     "Settings",
                    #     models=(
                    #         "eav.models.attribute.Attribute",
                    #         "eav.models.value.Value",
                    #         "eav.models.enum_group.EnumGroup",
                    #         "eav.models.enum_value.EnumValue",
                    #     ),
                    # ),
                ],
            )
        )

        self.children.append(
            modules.Group(
                title=_("Tickets"),
                column=2,
                collapsible=False,
                children=[
                    modules.ModelList(
                        "",
                        models=("core.models.HelpTicket.HelpTicket",),
                    ),
                ],
            )
        )

        self.children.append(
            modules.Group(
                title=_("Tasks"),
                column=2,
                collapsible=False,
                children=[
                    modules.ModelList(
                        "",
                        models=("core.models.Task.*",),
                    ),
                ],
            )
        )

        self.children.append(
            modules.Group(
                title=_("Training"),
                column=2,
                collapsible=False,
                children=[
                    modules.ModelList(
                        "",
                        models=(
                            "company.models.Employees.TrainingType",
                            "company.models.Employees.Course",
                            "company.models.Employees.TrainingClass",
                            "company.models.Employees.Student",
                        ),
                    ),
                ],
            )
        )

        self.children.append(
            modules.Group(
                title=_("Finance"),
                column=2,
                collapsible=False,
                children=[
                    modules.ModelList(
                        "",
                        models=(
                            "dispatch.models.Contracts.Contracts",
                            "dispatch.models.Invoice.Invoice",
                            "dispatch.models.Dispatch.DispatchInvoicesProxy",
                            "company.models.Company.Company",
                            "company.models.BankTransaction.BankTransaction",
                        ),
                    ),
                ],
            )
        )

        self.children.append(
            modules.Group(
                title=_("Fire History"),
                column=2,
                collapsible=False,
                children=[
                    modules.ModelList(
                        "",
                        models=[
                            "company.models.Employees.Fire",
                            "company.models.Employees.Crew",
                            "company.models.Employees.FireRun",
                            "company.models.Employees.DayOnFire",
                            "company.models.Employees.CrewTimeReport",
                            "company.models.Employees.Evaluation",
                        ],
                    ),
                    modules.LinkList(
                        "",
                        children=[
                            {
                                "title": _("Day On fire Service Page"),
                                "url": reverse("day_on_fire_service"),
                                "external": True,
                            },
                            {
                                "title": _("csv_import"),
                                "url": reverse("csv_import"),
                                "external": True,
                            },
                            {
                                "title": _("csv_dayonfire_import"),
                                "url": reverse("csv_dayonfire_import"),
                                "external": True,
                            },
                        ],
                    ),
                ],
            )
        )

        if user.username in SPECIAL_USERS_SET:
            self.children.append(
                modules.Group(
                    title=_("Paychex"),
                    column=2,
                    collapsible=False,
                    children=[
                        modules.ModelList(
                            "",
                            models=("paychex.models.CompanyWorkers.CompanyWorkers",),
                        ),
                        modules.ModelList(
                            "",
                            models=("paychex.models.Paycheck.Paycheck",),
                        ),
                        modules.LinkList(
                            "",
                            children=[
                                {
                                    "title": _("Working status"),
                                    "url": reverse("employees_status"),
                                    "external": True,
                                },
                            ],
                        ),
                    ],
                )
            )

        # self.children.append(modules.Group(
        #     _("Remote servers"),
        #     column=1,
        #     collapsible=False,
        #     children=[
        #         modules.ModelList(
        #             _("Exchange"),
        #             column=1,
        #             collapsible=False,
        #             css_classes=("collapse closed",),
        #             models=("exchange.models.Contacts.Contacts",),
        #         ),
        #         modules.ModelList(
        #             _("Privser"),
        #             column=1,
        #             collapsible=False,
        #             css_classes=("collapse closed",),
        #             models=("privser.models.CustomFields.Custom_Fields",),
        #         )
        #     ]
        # ))

        # append an app list module for "Applications"
        # self.children.append(modules.AppList(
        #     _("AppList: Applications"),
        #     collapsible=True,
        #     column=1,
        #     css_classes=("collapse closed",),
        #     exclude=("django.contrib.*",),
        # ))

        self.children.append(
            MyHelpTicketsModule(
                _("My Help Tickets"),
                collapsible=False,
                column=3,
                css_classes=["g-d-12 collapse my-help-tickets-list"],
            )
        )

        self.children.append(
            modules.RecentActions(
                _("Recent actions"),
                limit=5,
                collapsible=False,
                column=3,
                # include_list=("django_celery_results.TaskResult",),
                exclude_list=(
                    "django_celery_results.TaskResult",
                    "django_celery_results.GroupResult",
                    "synchronization.sync_parameters_logs",
                    "core.task_toggle",
                    "core.mqtt_log",
                ),
                css_classes=["g-d-12"],
            )
        )
        self.children.append(
            modules.ModelList(
                _("Celery"),
                column=3,
                collapsible=True,
                css_classes=("collapse closed grp-closed g-d-12",),
                models=("django_celery_results.*",),
            )
        )
        self.children.append(
            modules.ModelList(
                _("Administration"),
                column=3,
                collapsible=True,
                css_classes=("collapse closed grp-closed g-d-12",),
                models=("django.*",),
            )
        )

        if user.is_superuser:
            self.children.append(
                modules.LinkList(
                    _("Additional.."),
                    column=3,
                    css_classes=["collapse closed grp-closed g-d-12"],
                    children=[
                        {
                            "title": _("Update fields from Privser"),
                            "url": reverse("update_fields_from_privser"),
                            "external": False,
                        },
                        {
                            "title": _("Background tasks"),
                            "url": reverse("admin:core_task_toggle_changelist"),
                            "external": False,
                        },
                        {
                            "title": _("External Sync"),
                            "url": reverse("external_sync"),
                            "external": False,
                        },
                        {
                            "title": _("External PDF"),
                            "url": reverse("external_pdf"),
                            "external": False,
                        },
                        {
                            "title": _("Filters settings"),
                            "url": reverse("admin:core_saved_filter_changelist"),
                            "external": False,
                        },
                        {
                            "title": _("Metrics and charts"),
                            "url": reverse("metrics_charts"),
                            "external": False,
                        },
                        {
                            "title": _("schema diagram"),
                            "url": reverse("schema-diagram"),
                            "external": False,
                        },
                        {
                            "title": _("Tags"),
                            "url": reverse("admin:company_tag_changelist"),
                            "external": False,
                        },
                        {
                            "title": _("Inline config"),
                            "url": reverse("admin:core_admininlineconfig_changelist"),
                            "external": False,
                        },
                    ],
                )
            ),
            self.children.append(
                modules.ModelList(
                    _("Automation"),
                    column=3,
                    collapsible=True,
                    css_classes=("collapse closed grp-closed g-d-12",),
                    models=(
                        "automations.models.Automation",
                        "automations.models.AutomationLog",
                    ),
                )
            )

        self.children.append(
            modules.ModelList(
                _("PDF Plugin"),
                column=3,
                collapsible=True,
                css_classes=("collapse closed grp-closed g-d-12",),
                models=(
                    "pdf_plugin.models.PDFTemplate",
                    "pdf_plugin.models.PDFFieldMap",
                    "pdf_plugin.models.PDFRenderLog",
                ),
            )
        )

        self.children.append(
            modules.ModelList(
                _("Documentation"),
                column=3,
                collapsible=True,
                css_classes=("collapse closed grp-closed g-d-12",),
                models=("core.models.DocumentationPage.Documentation_Page",),
            )
        )

        self.children.append(
            modules.Group(
                title=_("Chloe's Apps"),
                column=3,
                collapsible=True,
                css_classes=("collapse closed grp-closed g-d-12",),
                children=[
                    modules.ModelList(
                        _("Companies"),
                        models=("companies.*",),
                    ),
                    modules.ModelList(
                        _("Contacts"),
                        models=("contacts.*",),
                    ),
                    modules.LinkList(
                        _("Contacts Check-in PWA"),
                        children=[
                            {
                                "title": _("Open Check-in Page"),
                                "url": reverse("contacts_pwa:pwa1_checkin_page"),
                                "external": False,
                            },
                        ],
                    ),
                    modules.LinkList(
                        _("Check-in PWA"),
                        children=[
                            {
                                "title": _("Open Check-in Page"),
                                "url": reverse("checkin_pwa:index"),
                                "external": False,
                            },
                        ],
                    ),
                    modules.Group(
                        title=_("Evernote PWA"),
                        children=[
                            modules.ModelList(
                                "",
                                models=("evernote_pwa.*",),
                            ),
                            modules.LinkList(
                                "",
                                children=[
                                    {
                                        "title": _("Dashboard"),
                                        "url": reverse("evernote_pwa:dashboard"),
                                        "external": False,
                                    },
                                ],
                            ),
                        ],
                    ),
                    modules.LinkList(
                        _("Pic PWA"),
                        children=[
                            {
                                "title": _("Open Scanner"),
                                "url": reverse("pic_pwa:pic_scan"),
                                "external": False,
                            },
                        ],
                    ),
                    modules.Group(
                        title=_("ID Scanner"),
                        children=[
                            modules.ModelList(
                                "",
                                models=("id_scanner.*",),
                            ),
                            modules.LinkList(
                                "",
                                children=[
                                    {
                                        "title": _("Dashboard"),
                                        "url": reverse("id_scanner:dashboard"),
                                        "external": False,
                                    },
                                ],
                            ),
                        ],
                    ),
                    modules.ModelList(
                        _("Jobs"),
                        models=("jobs.*",),
                    ),
                    modules.ModelList(
                        _("Invoices"),
                        models=("invoices.*",),
                    ),
                    modules.ModelList(
                        _("Integrations"),
                        models=("integrations.*",),
                    ),
                    modules.Group(
                        title=_("GHL Calls"),
                        children=[
                            modules.ModelList(
                                "",
                                models=("ghl_calls.*",),
                            ),
                            modules.LinkList(
                                "",
                                children=[
                                    {
                                        "title": _("Bulk Edit"),
                                        "url": reverse("ghl_call_bulk_edit"),
                                        "external": False,
                                    },
                                ],
                            ),
                        ],
                    ),
                    modules.ModelList(
                        _("LearnDash Webhook"),
                        models=("learndash_webhook.*",),
                    ),
                ],
            )
        )

        self.children.append(ChartModule())

        # python manage.py shell
        # >>> from django.contrib import admin
        # >>> admin.site._registry

        # 🔹 auth.models.models.Group
        # 🔹 auth.models.models.User
        # 🔹 django_celery_results.models.models.TaskResult
        # 🔹 django_celery_results.models.models.GroupResult
        # 🔹 exchange.models.Employees.EmployeesNew
        # 🔹 company.models.Employees.Employees
        # 🔹 privser.models.Contacts.Contacts
        # 🔹 exchange.models.ContactsProp.Contacts_Prop
        # 🔹 privser.models.CustomFields.Custom_Fields
        # 🔹 core.models.DocumentationPage.Documentation_Page
        # 🔹 privser.models.RequestFromPrivser.Request_From_Privser
        # 🔹 synchronization.models.Sync.Sync
        # 🔹 company.models.Employees.DispatchingStatus
        # 🔹 company.models.Employees.EmergencyContact
        # 🔹 company.models.Employees.MSPA
        # 🔹 company.models.Employees.IdentificationDocuments
        # 🔹 company.models.Employees.CompanyManifest
        # 🔹 company.models.Employees.DrugTest
        # 🔹 company.models.Employees.NomexCheckOut
        # 🔹 company.models.Employees.NomexCheckIn
        # 🔹 company.models.Employees.EmploymentPacket
        # 🔹 company.models.Employees.IQCCard
        # 🔹 company.models.Employees.Interaction
        # 🔹 company.models.Employees.TaskBook
        # 🔹 company.models.Employees.Availability
        # 🔹 company.models.Employees.CurrentAssigned
        # 🔹 company.models.Employees.RateOfPay
