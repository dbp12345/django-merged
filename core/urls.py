from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.urls import re_path
from django.views.generic import RedirectView

# from core.admin_panel.views.logs import logs_view
# from core.admin_panel.views.docs_old import docs_view
from core.admin_panel.views.documentation import documentation_view
from company.views.EmployeesParametersAjaxView import (
    EmployeesTableView,
    EmployeesTableData,
    update_employee_parameter,
)
from core.views.DayOnFire.DayOfFire import (
    DayOnFireView,
    get_crew_employees,
    search_employees,
    get_dayonfire_table,
    delete_dayonfire,
)
from core.views.FilterManagementView import (
    FilterManagementView,
    FilterManagementOrderView,
)
from core.views.Test.test_pwa import PWAView

# from core.views.Exchange.edit_field import ApiView
from core.views.Test.test_py import TestView
from core.views.ColumnsSettingsView import (
    columns_settings_view_json,
    update_columns_settings,
    columns_settings_for_filter,
    columns_settings_update_for_filter,
)
from core.views.api.EmployeeDataAPIView import EmployeeDataAPIView
from core.views.api.indeed import handle_requested_data_indeed
from core.views.api.n8n import handle_requested_data_n8n
from core.views.api.push_to_exchange import forcepush_to_exchange, remove_from_system
from core.views.api.push_to_privser import forcepush_to_privser
from core.views.autocomplete import (
    PhoneAutocomplete,
    RadioAutocomplete,
    SawAutocomplete,
    TruckAutocomplete,
    NomexAutocomplete,
    EquipmentAutocomplete,
    EquipmentGroupAutocomplete,
    TagAutocomplete,
    CrewAutocomplete,
)
from core.views.cards.cards import CardsView, CrewCardsView
from core.views.crew.mspa import CrewMSPAView
from core.views.crews_management.CrewsManagement import (
    CrewsManagementView,
    CrewsManagementDataView,
    AssignEmployeeToCrewView,
    RemoveEmployeeFromCrewView,
    AssignCrewBossView,
    firecrew_visible_disable,
    firecrew_status_change,
    FireRunForEmployeeView,
    employee_param_change,
)
from core.views.cropped.edit import CroppedEditView
from core.views.csv.form_for_dayonfire import CsvDayonfireImportFormView
from core.views.csv.status import CsvImportStatusView
from core.views.csv.status_for_dayonfire import CsvForDayOnFireImportStatusView
from core.views.documents.exhibit_docs import ExhibitDocsView
from core.views.documents.students_docs import StudentsDocsView
from core.views.employees.EmployeesAdd import EmployeesAdd
from core.views.employees.EmployeesParametersView import update_employee_parameters
from core.views.external_sync.external_sync import ExternalSyncView
from core.views.external_pdf.external_pdf import ExternalPdfView
from core.views.find_by_crwb.FindByCrwb import FindByCrwbView, search_crew_bosses
from core.views.metrics_charts import (
    metrics_charts,
    metrics_charts_dashboard,
    metrics_charts_data,
    metrics_charts_settings,
    delete_chart,
    save_chart,
)
from core.views.needs_maintenance.NeedsMaintenance import NeedsMaintenanceView
from core.views.scans.scans import ScansView
from core.views.schema.schema_view import schema_diagram_view
from core.views.tickets import admin_tickets_json
from core.views.equipment import get_equipment_type_schema
from dispatch.views.Dispatch.dispatch_set_global_status import (
    dispatch_set_global_status,
)
from dispatch.views.documents.get import DispatchDocsView
from dispatch.views.documents.get_Extension_Form import DispatchDocsExtensionFormView
from dispatch.views.documents.get_VIPR import DispatchDocsVIPRView
from dispatch.views.documents.get_pdf import DispatchDocsPdfView
from dispatch.views.documents.get_vipr_eqp_pdf import DispatchPdfViprEqpView
from dispatch.views.documents.get_vipr_extension_form_pdf import (
    DispatchPdfExtensionFormView,
)
from exchange.views.Exchange.create_test_request import update_fields_from_privser
from exchange.views.Exchange.request_to_exchange import (
    update_contact_from_exchange_by_email,
)
from ghl_calls.views import ghl_call_webhook, ghl_transcript_webhook
from integrations.views import ghl_oauth_callback, ghl_oauth_start
from learndash_webhook.views import learndash_webhook
from paychex.views.paychex.admin_status import employees_status_view
from paychex.views.paychex.test import PaychexTestView
from paychex.views.paychex.worker_transactions import (
    worker_transactions,
    worker_transactions_json,
)
from privser.views.Privser.api import handle_requested_data
from privser.views.Privser.request_to_privser import (
    update_contact_from_privser_by_id,
    update_contact_from_privser_by_email,
)

# from synchronization.views.Synchronization.request_to_privser import sync_update_all_by_email
from synchronization.views.Synchronization.sync_parameters_logs import (
    sync_parameters_logs_execute,
)
from synchronization.views.Synchronization.sync_delivery_logs import (
    sync_delivery_logs_execute,
)
from core.views.csv.form import CsvImportFormView

# from privser.views.Privser.create_request_to_privser_from_contact import create_request_to_privser_from_contact

admin.site.index_title = ""  # "Dust Busters Plus LLC"  # Меняем заголовок
# admin.site.site_header = "Django administration"  # Заголовок вверху
# admin.site.site_title = "Admin Portal"  # Заголовок вкладки

# Example for a docs redirect view:
# def docs_old_redirect_view(request):
#     """Redirects to the old documentation manual page."""
#     return redirect("docs_old", filename="manual")
#     return redirect("docs_old", filename="manual")


def docs_redirect_view(request):
    return redirect("documentation", slug="manual")


urlpatterns = [
    # path("admin/docs_old/", docs_old_redirect_view),
    # path("admin/docs_old/<str:filename>/", docs_view, name="docs_old"),
    re_path(
        r"^favicon\.ico$",
        RedirectView.as_view(url="/static/favicon.ico", permanent=True),
    ),
    path("grappelli/", include("grappelli.urls")),
    path("test/", TestView.as_view(), name="test"),
    path("pwa-test/", PWAView.as_view(), name="test"),
    path("docs/", docs_redirect_view),
    path(
        "admin/<str:app_label>/<str:model_name>/<int:object_id>/tickets-json/",
        admin.site.admin_view(admin_tickets_json),
        name="admin_tickets_json",
    ),
    path(
        "admin/employees/update-parameters/",
        update_employee_parameters,
        name="update_employee_parameters",
    ),
    path(
        "admin/columns-settings/json/",
        columns_settings_view_json,
        name="columns_settings_json",
    ),
    path(
        "admin/update-columns-settings/",
        update_columns_settings,
        name="update_columns_settings",
    ),
    path(
        "admin/columns-settings/<int:filter_id>/columns/",
        columns_settings_for_filter,
        name="columns_settings_for_filter",
    ),
    path(
        "admin/columns-settings-update/<int:filter_id>/columns/",
        columns_settings_update_for_filter,
        name="columns_settings_update_for_filter",
    ),
    path("admin/saved-filters/", FilterManagementView.as_view(), name="saved_filters"),
    path(
        "admin/saved-filters-order/",
        FilterManagementOrderView.as_view(),
        name="saved_filters_order",
    ),
    path(
        "admin/employees-table/", EmployeesTableView.as_view(), name="employees_table"
    ),
    path(
        "admin/employees-table/data/",
        EmployeesTableData.as_view(),
        name="employees_table_data",
    ),
    path(
        "admin/employees-table/update/",
        update_employee_parameter,
        name="update_employee_parameter",
    ),
    path(
        "admin/equipment/type/<int:equipment_type_id>/schema/",
        admin.site.admin_view(get_equipment_type_schema),
        name="get_equipment_type_schema",
    ),
    path(
        "admin/autocomplete/phone/",
        PhoneAutocomplete.as_view(),
        name="phone-autocomplete",
    ),
    path(
        "admin/autocomplete/radio/",
        RadioAutocomplete.as_view(),
        name="radio-autocomplete",
    ),
    path("admin/autocomplete/saw/", SawAutocomplete.as_view(), name="saw-autocomplete"),
    path(
        "admin/autocomplete/truck/",
        TruckAutocomplete.as_view(),
        name="truck-autocomplete",
    ),
    path(
        "admin/autocomplete/nomex/",
        NomexAutocomplete.as_view(),
        name="nomex-autocomplete",
    ),
    path(
        "admin/autocomplete/equipment/",
        EquipmentAutocomplete.as_view(),
        name="equipment-autocomplete",
    ),
    path(
        "admin/autocomplete/equipment-group/",
        EquipmentGroupAutocomplete.as_view(),
        name="equipment-group-autocomplete",
    ),
    path("admin/autocomplete/tag/", TagAutocomplete.as_view(), name="tag-autocomplete"),
    path(
        "admin/crew-autocomplete/", CrewAutocomplete.as_view(), name="crew-autocomplete"
    ),
    path(
        "admin/crews-management/",
        CrewsManagementView.as_view(),
        name="crews_management",
    ),
    path(
        "admin/crews-management/data/",
        CrewsManagementDataView.as_view(),
        name="crews_management_data",
    ),
    path(
        "admin/crews-management/assign-employee/",
        AssignEmployeeToCrewView.as_view(),
        name="assign_employee",
    ),
    path(
        "admin/crews-management/remove-employee/",
        RemoveEmployeeFromCrewView.as_view(),
        name="remove_employee",
    ),
    path(
        "admin/crews-management/firerun-employee/",
        FireRunForEmployeeView.as_view(),
        name="firerun_for_employee",
    ),
    path(
        "admin/crews-management/assign-crwb/",
        AssignCrewBossView.as_view(),
        name="assign_crwb",
    ),
    path(
        "admin/employee/employee-param-change/",
        employee_param_change,
        name="employee_param_change",
    ),
    path("admin/add/employees/", EmployeesAdd.as_view(), name="add_employee"),
    path(
        "admin/needs-maintenance/",
        NeedsMaintenanceView.as_view(),
        name="needs_maintenance",
    ),
    path("admin/find-by-crwb/", FindByCrwbView.as_view(), name="find_by_crwb"),
    path(
        "admin/find-by-crwb/search-bosses",
        search_crew_bosses,
        name="search-crew-bosses",
    ),
    path(
        "admin/crews-management/settings/",
        FilterManagementView.as_view(),
        name="crews_management_settings",
    ),
    path("admin/schema/", schema_diagram_view, name="schema-diagram"),
    path(
        "admin/firecrew/visible/disable/<int:crew_id>",
        firecrew_visible_disable,
        name="firecrew_visible_disable",
    ),
    path(
        "admin/firecrew/status/change/<int:crew_id>",
        firecrew_status_change,
        name="firecrew_status_change",
    ),
    path("admin/metrics-charts/", metrics_charts, name="metrics_charts"),
    path(
        "admin/metrics-charts-dashboard/",
        metrics_charts_dashboard,
        name="metrics_charts_dashboard",
    ),
    path("admin/metrics-charts-data/", metrics_charts_data, name="metrics_charts_data"),
    path(
        "admin/metrics-charts-settings/",
        metrics_charts_settings,
        name="metrics_charts_settings",
    ),
    path(
        "admin/metrics-charts-settings/<int:chart_id>/",
        metrics_charts_settings,
        name="metrics_charts_edit",
    ),
    path("admin/delete-chart/<int:chart_id>/", delete_chart, name="delete_chart"),
    path("admin/save-chart/", save_chart, name="save_chart"),
    path("admin/docs/<str:slug>/", documentation_view, name="documentation"),
    path(
        "admin/sync_parameters_logs/execute/<int:sync_parameters_logs_id>",
        sync_parameters_logs_execute,
        name="sync_parameters_logs_execute",
    ),
    path(
        "admin/sync_delivery_logs/execute/<int:sync_delivery_logs_id>",
        sync_delivery_logs_execute,
        name="sync_delivery_logs_execute",
    ),
    # path("admin/set_all_identified_fields_to_exchange/",
    #      set_all_identified_fields_to_exchange,
    #      name="set_all_identified_fields_to_exchange"),
    # path("admin/create_test_request_to_exchange/",
    #      create_test_request_to_exchange,
    #      name="create_test_request_to_exchange"),
    # path("admin/create_test_request_to_privser/",
    #      create_test_request_to_privser,
    #      name="create_test_request_to_privser"),
    path(
        "admin/update_fields_from_privser/",
        update_fields_from_privser,
        name="update_fields_from_privser",
    ),
    path(
        "admin/update/contact/from/privser/email/<str:obj_email>",
        update_contact_from_privser_by_email,
        name="update_contact_from_privser_by_email",
    ),
    path(
        "admin/update/contact/from/privser/<str:obj_id>",
        update_contact_from_privser_by_id,
        name="update_contact_from_privser_by_id",
    ),
    path(
        "admin/update/contact/forcepush/privser/<str:obj_id>",
        forcepush_to_privser,
        name="contact_forcepush_to_privser",
    ),
    path(
        "admin/update/contact/from/exchange/<str:obj_id>",
        update_contact_from_exchange_by_email,
        name="update_contact_from_exchange_by_email",
    ),
    path(
        "admin/update/contact/forcepush/exchange/<str:obj_id>",
        forcepush_to_exchange,
        name="contact_forcepush_to_exchange",
    ),
    path(
        "admin/remove/contact/<str:obj_id>",
        remove_from_system,
        name="remove_from_system",
    ),
    # path("admin/sync/update/all/<str:obj_id>", sync_update_all_by_email, name="sync_update_all_by_email"),
    path("admin/external_sync/", ExternalSyncView.as_view(), name="external_sync"),
    path("admin/external_pdf/", ExternalPdfView.as_view(), name="external_pdf"),
    path("admin/csv/import/", CsvImportFormView.as_view(), name="csv_import"),
    path(
        "admin/csv/import/status/",
        CsvImportStatusView.as_view(),
        name="csv_import_status",
    ),
    path(
        "admin/csv/dayonfire/import/",
        CsvDayonfireImportFormView.as_view(),
        name="csv_dayonfire_import",
    ),
    path(
        "admin/csv/dayonfire/import/status/",
        CsvForDayOnFireImportStatusView.as_view(),
        name="csv_dayonfire_import_status",
    ),
    path(
        "admin/day-on-fire/service/",
        DayOnFireView.as_view(),
        name="day_on_fire_service",
    ),
    path(
        "admin/day-on-fire/service/employees-by-dispatch/<int:dispatch_id>/",
        get_crew_employees,
        name="employees_by_dispatch",
    ),
    path(
        "admin/day-on-fire/service/search-employees",
        search_employees,
        name="search_employees",
    ),
    path(
        "admin/day-on-fire/service/table",
        get_dayonfire_table,
        name="get_dayonfire_table",
    ),
    path(
        "admin/day-on-fire/service/delete/<int:obj_id>/",
        delete_dayonfire,
        name="delete_dayonfire",
    ),
    path("admin/cards/", CardsView.as_view(), name="cards_create"),
    path("admin/cards/crew/", CrewCardsView.as_view(), name="cards_crew_create"),
    path("admin/crew/mspa/", CrewMSPAView.as_view(), name="crew_mspa"),
    path(
        "admin/pictures/cropped/edit",
        CroppedEditView.as_view(),
        name="pictures_cropped_edit",
    ),
    path(
        "dispatch/manifest/get/odf_crew_manifest/docx",
        DispatchDocsView.as_view(),
        name="dispatch_docs_odf_crew_manifest_docx_get",
    ),
    path(
        "dispatch/manifest/get/odf_eqp_manifest/pdf",
        DispatchDocsPdfView.as_view(),
        name="dispatch_docs_odf_eqp_manifest_pdf_get",
    ),
    path(
        "dispatch/manifest/get/odf_extension_form/docx",
        DispatchDocsExtensionFormView.as_view(),
        name="dispatch_docs_odf_extension_form_docx_get",
    ),
    path(
        "dispatch/manifest/get/vipr_crew_manifest/docx",
        DispatchDocsVIPRView.as_view(),
        name="dispatch_docs_vipr_crew_manifest_docx_get",
    ),
    path(
        "dispatch/manifest/get/vipr_eqp_manifest/pdf",
        DispatchPdfViprEqpView.as_view(),
        name="dispatch_vipr_eqp_manifest_pdf_get",
    ),
    path(
        "dispatch/manifest/get/vipr_extension_form/pdf",
        DispatchPdfExtensionFormView.as_view(),
        name="dispatch_vipr_extension_form_pdf_get",
    ),
    path(
        "dispatch/set-global-status/on-fire/<str:status>/<str:obj_id>",
        dispatch_set_global_status,
        name="dispatch_set_global_status",
    ),
    path("admin/exhibit/get/docx", ExhibitDocsView.as_view(), name="exhibit_docx_get"),
    path("admin/students/get/pdf", StudentsDocsView.as_view(), name="students_pdf_get"),
    path("admin/scans/phone", ScansView.as_view(), name="scans_phone"),
    path("admin/paychex/test/", PaychexTestView.as_view(), name="paychex_test"),
    path(
        "admin/paychex/workers/<int:pk>/transactions/",
        worker_transactions,
        name="paychex_worker_transactions",
    ),
    path(
        "admin/paychex/workers/<int:pk>/transactions/json/",
        worker_transactions_json,
        name="paychex_worker_transactions_json",
    ),
    # path("admin/logs/", logs_view, name="logs"),
    path(
        "admin/employees-status/",
        admin.site.admin_view(employees_status_view),
        name="employees_status",
    ),
    path(
        "admin/tools/checkin-pwa/",
        include(("checkin_pwa.urls", "checkin_pwa"), namespace="checkin_pwa"),
    ),
    path(
        "admin/tools/evernote-pwa/",
        include(("evernote_pwa.urls", "evernote_pwa"), namespace="evernote_pwa"),
    ),
    path(
        "admin/tools/contacts-checkin/",
        include(("contacts.pwa_urls", "contacts_pwa"), namespace="contacts_pwa"),
    ),
    path(
        "admin/tools/pic-pwa/",
        include(("pic_pwa.urls", "pic_pwa"), namespace="pic_pwa"),
    ),
    path(
        "admin/tools/id-scanner/",
        include(("id_scanner.urls", "id_scanner"), namespace="id_scanner"),
    ),
    path("oauth/start/", ghl_oauth_start, name="ghl_oauth_start_public"),
    path("oauth/start", ghl_oauth_start, name="ghl_oauth_start_public_no_slash"),
    path("oauth/callback/", ghl_oauth_callback, name="ghl_oauth_callback_public"),
    path("oauth/callback", ghl_oauth_callback, name="ghl_oauth_callback_public_no_slash"),
    path("api/webhooks/ghl-calls/", include("ghl_calls.urls")),
    path("api/webhooks/ghl-calls", ghl_call_webhook, name="ghl_call_webhook_api_no_slash"),
    path(
        "api/webhooks/ghl-calls/transcript",
        ghl_transcript_webhook,
        name="ghl_transcript_webhook_api_no_slash",
    ),
    path("api/webhooks/learndash/", include("learndash_webhook.urls")),
    path("api/webhooks/learndash", learndash_webhook, name="learndash_webhook_api_no_slash"),
    path("admin/tools/integrations/", include("integrations.urls")),
    path("admin/tools/ghl-calls/", include("ghl_calls.urls")),
    path("admin/tools/learndash-webhook/", include("learndash_webhook.urls")),
    path("admin/pdf-plugin/", include("pdf_plugin.urls_admin")),
    path("admin/", admin.site.urls),
    path("", include("frontend.urls")),
    path("pwa/", include("pwa_vehicle.urls")),
    path("crwb/", include("pwa_crwb.urls")),
    path("notifications/", include("pwa_notifications.urls")),
    path("attendance/", include("attendance.urls")),
    path("markdownx/", include("markdownx.urls")),
    path("api/privser/", handle_requested_data, name="api_privser"),
    path("api/indeed/", handle_requested_data_indeed, name="api_indeed"),
    path("api/n8n/", handle_requested_data_n8n, name="api_n8n"),
    path("api/employees/", EmployeeDataAPIView.as_view(), name="api_employees_update"),
    path('webpush/', include('webpush.urls')),
    path("", include("django_admin_flexlist.urls")),
    path("checkin/", include("checkin_pwa.urls")),
    path("evernote/", include("evernote_pwa.urls")),
    path("id-scan/", include("id_scanner.urls")), 


   # path("request/to/exchange/<int:request_to_exchange_id>/<str:operation>",
    #      request_to_exchange, name="request_to_exchange"),
    # path("request/to/privser/<int:request_to_privser_id>",
    #      request_to_privser, name="request_to_privser"),
    # path("update/statuses/contacts/",
    #      request_to_exchange_update_statuses_user_not_found,
    #      name="request_to_exchange_update_statuses_user_not_found"),
    # path("create/request/to/privser/<int:obj_id>",
    #      create_request_to_privser_from_contact,
    #      name="create_request_to_privser_from_contact"),
    # path("api/edit/", api_catch_request, name="api_catch_request"),
    # path("api/edit/", edit_field, name="api_edit_field"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

