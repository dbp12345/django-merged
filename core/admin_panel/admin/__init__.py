from django.contrib import admin
from . import TaskResultAdmin  # noqa: F401

# from .ExchangeSentParametersLogsAdmin import ExchangeSentParametersLogsAdmin   # noqa: F401
# from .EmployeesNewAdmin import EmployeesNewAdmin   # noqa: F401
from .EmployeesAdmin import EmployeesAdmin  # noqa: F401

# from .ChangesInContactsAdmin import ChangesInContactsAdmin   # noqa: F401
from .ContactsPrivserAdmin import ContactsPrivserAdmin  # noqa: F401
from .ContactsPropAdmin import ContactsPropAdmin  # noqa: F401

# from .RequestToPrivserAdmin import RequestToPrivserAdmin   # noqa: F401
from .CustomFieldsAdmin import CustomFieldsAdmin  # noqa: F401
from .DocumentationPage import DocumentationPageAdmin  # noqa: F401

# from .CronLogsAdmin import CronLogsAdmin   # noqa: F401
# from .RequestToExchangeAdmin import RequestToExchangeAdmin   # noqa: F401
# from .RequestFromPrivserAdmin import RequestFromPrivserAdmin   # noqa: F401
# from .SyncAdmin import SyncAdmin   # noqa: F401
from .SyncParametersLogsAdmin import SyncParametersLogsAdmin  # noqa: F401
from .SyncDeliveryLogsAdmin import SyncDeliveryLogsAdmin  # noqa: F401
from .EmployeeChangeQueueAdmin import EmployeeChangeQueueAdmin  # noqa: F401

from .FireCrewAdmin import FireCrewAdmin  # noqa: F401
from .DispatchingStatusAdmin import DispatchingStatusAdmin  # noqa: F401
from .EmergencyContactAdmin import EmergencyContactAdmin  # noqa: F401
from .MSPAAdmin import MSPAAdmin  # noqa: F401
# from .IdentificationDocumentsAdmin import IdentificationDocumentsAdmin  # noqa: F401
from .DriverLicenseAdmin import DriverLicenseAdmin  # noqa: F401
from .PassportAdmin import PassportAdmin  # noqa: F401
from .SocialSecurityNumberAdmin import SocialSecurityNumberAdmin  # noqa: F401
from .MedicalCardAdmin import MedicalCardAdmin  # noqa: F401
from .ManifestAdmin import ManifestAdmin  # noqa: F401
from .DrugTestAdmin import DrugTestAdmin  # noqa: F401
from .NomexCheckOutAdmin import NomexCheckOutAdmin  # noqa: F401
from .NomexCheckInAdmin import NomexCheckInAdmin  # noqa: F401
from .EmploymentPacketAdmin import EmploymentPacketAdmin  # noqa: F401
from .IQCCardAdmin import IQCCardAdmin  # noqa: F401
from .InteractionAdmin import InteractionAdmin  # noqa: F401
from .TaskBookAdmin import TaskBookAdmin  # noqa: F401
from .AvailabilityAdmin import AvailabilityAdmin  # noqa: F401
from .BankTransactionAdmin import BankTransactionAdmin  # noqa: F401
from .CurrentAssignedAdmin import CurrentAssignedAdmin  # noqa: F401
from .TrainingTypeAdmin import TrainingTypeAdmin  # noqa: F401
from .CourseAdmin import CourseAdmin  # noqa: F401
from .TrainingClassAdmin import TrainingClassAdmin  # noqa: F401
from .StudentAdmin import StudentAdmin  # noqa: F401
from .RateOfPayAdmin import RateOfPayAdmin  # noqa: F401
from .FireAdmin import FireAdmin  # noqa: F401
from .CrewAdmin import CrewAdmin  # noqa: F401
from .FireRunAdmin import FireRunAdmin  # noqa: F401
from .EvaluationAdmin import EvaluationAdmin  # noqa: F401
from .DayOnFireAdmin import DayOnFireAdmin  # noqa: F401
from .CrewTimeReportAdmin import CrewTimeReportAdmin  # noqa: F401
from .SavedFilterAdmin import SavedFilterAdmin  # noqa: F401
from .TaskToggleAdmin import TaskToggleAdmin  # noqa: F401
from .NotesAdmin import NotesAdmin  # noqa: F401
from .DispatchAdmin import *  # noqa: F401, F403
from .DispatchInvoicesAdmin import *  # noqa: F401, F403
from .ContractsAdmin import ContractsAdmin  # noqa: F401
from .InvoiceAdmin import InvoiceAdmin  # noqa: F401
from .NomexAdmin import NomexAdmin  # noqa: F401
from .SawAdmin import SawAdmin  # noqa: F401
from .RadioAdmin import RadioAdmin  # noqa: F401
from .PhoneAdmin import PhoneAdmin  # noqa: F401
from .TruckAdmin import TruckAdmin  # noqa: F401
from .DrawsAdmin import DrawsAdmin  # noqa: F401
from .MqttLogAdmin import MqttLogAdmin  # noqa: F401
from .VehicleCheckoutAdmin import VehicleCheckoutAdmin  # noqa: F401
from .CompanyAdmin import CompanyAdmin  # noqa: F401
from .HelpTicketAdmin import HelpTicketAdmin  # noqa: F401
from .PaychexCompanyWorkersAdmin import PaychexCompanyWorkersAdmin  # noqa: F401
from .PaychexPaycheckAdmin import PaychexPaycheckAdmin  # noqa: F401
from .TaskAdmin import TaskAdmin, CategoryAdmin  # noqa: F401
from .EmployeesStudentsAdmin import EmployeesStudentsAdmin  # noqa: F401
from .EquipmentAdmin import EquipmentAdmin  # noqa: F401
from .InspectionAdmin import InspectionAdmin, InspectionTypeAdmin  # noqa: F401

# Unregister Value model from admin (not useful for direct editing)
from eav.models import Value
admin.site.unregister(Value)


class GlobalMediaMixin:
    class Media:
        css = {
            "all": (
                "core/collapsible.css",
                "core/custom_styles.css",
                "grappelli/css/admin_breadcrumbs.css",
                "grappelli/css/admin_overrides.css",
                "admin/css/helpticket_overlay.css",
                "admin/css/fixed_admin_header.css",
            )
        }
        js = (
            "grappelli/js/admin_breadcrumbs.js",
            "grappelli/js/grappelli_related_link.js",
            "core/collapsible.js",
            "admin/js/helpticket_overlay_ajax_no_template.js",
            "pdf/pdf.min.js",
            "admin/js/pdf_preview.js",
        )


for model, model_admin in admin.site._registry.items():
    old_media = getattr(model_admin, "Media", None)

    old_css = (
        tuple(getattr(getattr(old_media, "__class__", None), "css", {}).get("all", []))
        if old_media
        else ()
    )
    old_js = (
        tuple(getattr(getattr(old_media, "__class__", None), "js", ()))
        if old_media
        else ()
    )

    bases = (GlobalMediaMixin.Media,)
    if old_media:
        bases += (old_media.__class__,)

    class NewMedia(*bases):
        css = {"all": tuple(set(GlobalMediaMixin.Media.css["all"] + old_css))}
        js = tuple(set(GlobalMediaMixin.Media.js + old_js))

    model_admin.__class__ = type(
        model_admin.__class__.__name__, (model_admin.__class__,), {"Media": NewMedia}
    )
