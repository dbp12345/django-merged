import copy
import datetime
import logging as logging_uniq_name
import traceback
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from typing import Dict, Any, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from company.models.EmployeesParameters import Employees_Parameters
from core.models import Employee_Last_Updates
from core.models.EmployeeLastUpdates import ApiType
from core.models.FieldsSettings import Fields_Settings, Type
from core.services.SanitazerService import SanitazerService
from exchange.models import Contacts_Prop
from company.models.Employees import (
    MSPA,
    Course,
    DriverLicense,
    Employees,
    FireCrew,
    # IdentificationDocuments,
    DispatchingStatus,
    CompanyManifest,
    DrugTest,
    EmploymentPacket,
    IQCCard,
    Interaction,
    Availability,
    MedicalCard,
    Passport,
    SocialSecurityNumber,
    Student,
    Notes,
    RateOfPay,
    TrainingClass,
    TrainingType,
)
from django.utils import timezone


class EmployeesService:
    def __init__(self):
        self.employee_obj = None
        self._contact_parameters = {}
        self._new_params = {}
        self._old_params = {}
        self._updated_params = {}
        self._delete_params = {}

    # field_mappings = {
    #     "varchar": ("issue_date", "mspa_defaults"),
    #     "MSPA Expiration Date": ("expiration_date", "mspa_defaults"),
    #     "MSPA Number": ("MSPA_number", "mspa_defaults"),
    #     "varchar": ("link_to_document", "mspa_defaults"),
    #
    #     "url": ("link_to_document", "crew_time_report_defaults")
    # }

    dictionary_list = [
        {
            MSPA: {
                "MSPA Issue date": "issue_date",
                "MSPA Expiration Date": "expiration_date",
                "MSPA Number": "MSPA_number",
                "MSPA Pending": "pending",
                # "MSPA document": "document",
            }
        },
        # {
        #     IdentificationDocuments: {
        #         # "??": "type",
        #         "Driver's License Issue Date": "issue_date",
        #         "Driver's License Expiration Date": "expiration_date",
        #         "Driver's License State, Number": "number",
        #         # "??": "link_to_document",
        #         "Driver's License Endorsements": "endorsement",
        #         "Driver's License Restrictions": "restriction",
        #     },
        #     "extra": {"type": IdentificationDocumentsType.DL.name},
        # },
        {
            DriverLicense: {
                "Driver's License Issue Date": "issue_date",
                "Driver's License Expiration Date": "expiration_date",
                "Driver's License State, Number": "number",
                "Driver's License Endorsements": "endorsement",
                "Driver's License Restrictions": "restriction",
            },
        },
        # {
        #     IdentificationDocuments: {
        #         # "??": "type",
        #         # "??": "issue_date",
        #         "Medical Card Expiration Date": "expiration_date",
        #         "Medical Card Issue Date": "issue_date",
        #         "Medical Card Type": "number",
        #         "Medical Card Document": "document",
        #         # "??": "number",
        #         # "??": "link_to_document",
        #         # "??": "endorsement",
        #         # "??": "restriction",
        #     },
        #     "extra": {"type": IdentificationDocumentsType.MEDICAL_CARD.name},
        # },
        {
            MedicalCard: {
                "Medical Card Expiration Date": "expiration_date",
                "Medical Card Issue Date": "issue_date",
                "Medical Card Type": "type",
                "Medical Card Document": "document",
            },
        },
        # {
        #     IdentificationDocuments: {
        #         # "??": "type",
        #         # "??": "issue_date",
        #         "Passport Expiration Date": "expiration_date",
        #         "Passport Number": "number",
        #         # "??": "link_to_document",
        #         # "??": "endorsement",
        #         # "??": "restriction",
        #     },
        #     "extra": {"type": IdentificationDocumentsType.PASSPORT.name},
        # },
        {
            Passport: {
                "Passport Expiration Date": "expiration_date",
                "Passport Number": "number",
            },
        },
        # {
        #     IdentificationDocuments: {
        #         # "??": "type",
        #         # "??": "issue_date",
        #         # "??": "expiration_date",
        #         "Social Security Number": "number",
        #         # "??": "link_to_document",
        #         # "??": "endorsement",
        #         # "??": "restriction",
        #     },
        #     "extra": {"type": IdentificationDocumentsType.SSN.name},
        # },
        {
            SocialSecurityNumber: {
                "Social Security Number": "number",
            },
        },
        {
            DispatchingStatus: {
                "Dispatch Status Update Date": "date",
                "Dispatch Status Update Time": "time",
                # "??": "negative_interaction",
                "Dispatch Call Status": "dispatch_status",
                "Dispatch Category": "dispatch_category",
                "ETA, Late, Dispatch": "ETA",
                "Dispatch location": "location",
                "Dispatch notes": "notes",
            }
        },
        # {
        #     CompanyManifest: {
        #         # "??": "year"
        #         "Manifest Date, 2025": "date"
        #     },
        #     # "extra": {"year": "2021"}
        # },
        # {
        #     CompanyManifest: {
        #         # "??": "year"
        #         "Manifest Date, 2024": "date"
        #     },
        #     # "extra": {"year": "2022"}
        # },
        # {
        #     CompanyManifest: {
        #         # "??": "year"
        #         "Manifest Date, 2023": "date"
        #     },
        #     # "extra": {"year": "2023"}
        # },
        # {
        #     CompanyManifest: {
        #         # "??": "year"
        #         "Manifest Date, 2022": "date"
        #     },
        #     # "extra": {"year": "2024"}
        # },
        # {
        #     CompanyManifest: {
        #         # "??": "year"
        #         "Manifest Date, 2021": "date"
        #     },
        #     # "extra": {"year": "2025"}
        # },
        {
            CompanyManifest: {
                # "??": "year"
                "Manifest Date": "date"
            },
        },
        # {
        #     DrugTest: {
        #         # "??": "date",
        #         "Drug Test, 2018, PreSeason": "result"
        #     },
        #     "extra": {"date": "2018"}
        # },
        # {
        #     DrugTest: {
        #         # "??": "date",
        #         "Drug Test, 2019, PreSeason": "result"
        #     },
        #     "extra": {"date": "2019"}
        # },
        # {
        #     DrugTest: {
        #         # "??": "date",
        #         "Drug Test, 2020, PreSeason": "result"
        #     },
        #     "extra": {"date": "2020"}
        # },
        # {
        #     DrugTest: {
        #         # "??": "date",
        #         "Drug Test, 2021, PreSeason": "result"
        #     },
        #     "extra": {"date": "2021"}
        # },
        # {
        #     DrugTest: {
        #         # "??": "date",
        #         "Drug Test, 2022, PreSeason": "result"
        #     },
        #     "extra": {"date": "2022"}
        # },
        # {
        #     DrugTest: {
        #         # "??": "date",
        #         "Drug Test, 2025, Preseason": "result"
        #     },
        #     "extra": {"date": "2025-01-01"},
        # },
        # {
        #     DrugTest: {
        #         # "??": "date",
        #         "Drug Test, 2024, Preseason": "result"
        #     },
        #     "extra": {"date": "2024-01-01"},
        # },
        # {
        #     DrugTest: {
        #         # "??": "date",
        #         "Drug Test, 2023, Preseason": "result"
        #     },
        #     "extra": {"date": "2023-01-01"},
        # },
        {
            DrugTest: {"Drug Test date": "date", "Drug Test preseason": "result"},
        },
        # {
        #     NomexCheckOut: {
        #         "??": "date",
        #         "??": "pants_serial_number",
        #         "??": "shirt_serial_number",
        #     }
        # },
        # {
        #     NomexCheckIn: {
        #         "??": "date",
        #         "??": "pants_serial_number",
        #         "??": "shirt_serial_number",
        #     }
        # },
        # {  # TO-DO
        #     EmploymentPacket: {
        #         "2025 Employee Packet": "packet_name",
        #         "Pack Test Date": "date_sent",
        #         # "??": "date_signed",
        #         # "??": "link_to_document",
        #     },
        #     "extra": {"date_sent": "2025-01-01"},
        # },
        # {
        #     EmploymentPacket: {
        #         "2024 Employee Packet": "packet_name",
        #         "Pack Test Date": "date_sent",
        #         # "??": "date_signed",
        #         # "??": "link_to_document",
        #     },
        #     "extra": {"date_sent": "2024-01-01"},
        # },
        {
            EmploymentPacket: {
                "Employee Packet": "packet_name",
                "Current Pack Test Date": "date_sent",
                "Current Pack Test Date signed": "date_signed",
                # "Pack Test document": "document", # чегото в рекурсию залипает....
            },
        },
        # {
        #     IQCCard: {
        #         #         "??": "position",
        #         "IQC Provider": "pack_test",
        #         # "2024 IQC": "date",
        #     }
        # },
        # {
        #     IQCCard: {
        #         #         "??": "position",
        #         # "IQC Provider": "pack_test",
        #         "2024 IQC": "date",
        #     }
        # },
        # {
        #     IQCCard: {
        #         #         "??": "position",
        #         # "IQC Provider": "pack_test",
        #         "2025 IQC": "date",
        #     }
        # },
        {
            IQCCard: {
                "IQC Position": "position",
                "Packtest Results": "pack_test",
                "IQC Issue date": "date",
                # "Pack Test document": "document",
            }
        },
        # {
        #     Interaction: {
        #         "Type of interaction": "type_of_interaction",
        #         "Last Communication with DB": "date",
        #         "Interaction notes": "notes",
        #         "Negative interaction": "negative_interaction",
        #     },
        #     "extra": {"negative_interaction": False}
        # },
        # {
        #     Interaction: {
        #         "Type of interaction": "type_of_interaction",
        #         "Last Attempted Communication": "date",
        #         "Interaction notes": "notes",
        #         "Negative interaction": "negative_interaction",
        #     },
        #     "extra": {"negative_interaction": False}
        # },
        {
            Interaction: {
                "Type of interaction": "type_of_interaction",
                "Last Attempted Communication": "date",
                "Negative interaction": "negative_interaction",
                "Interaction notes": "notes",
            },
        },
        # {# there are no entries in exchange
        #     TaskBook: {
        #         # "??": "type_of_taskbook",
        #         "TB, CRWB, Initiated": "initiated_date",
        #         "TB, CRWB, Completed": "completed_date",
        #         "TB, CRWB, Updated": "updated_date",
        #         # "??": "final_evaluator",
        #         # "??": "link_to_document",
        #     },
        #     "extra": {"type_of_taskbook": TaskBookType.CRWB}
        # },
        {
            Availability: {
                "Availability status": "availability_status",
                "Date of expected future change": "date_of_expected_future_change",
                "Current State Dispatching From": "location_state",
                "Current City Dispatching From": "location_city",
                "Travel Time": "travel_time",
                "Availability notes": "notes",
            },
            # "extra": {"date_of_change": now()}
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Refresher 2024": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Refresher 2025": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "RT-130 Webinar 2020": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "RT-130 Webinar 2021": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "RT-130 Webinar 2022": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "RT-130 Webinar 2023": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "RT-130 Webinar 2024": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "RT-130 Webinar 2025": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "S130": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "S130 Online Component": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "S-131": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "S190": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "S-190 Webinar": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "S-212": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "S-230": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "S-290": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "L180": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "L-180 Webinar": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "ICS100": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "IS-200.b": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "I700": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "M-410": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Pack Test 2020": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Pack Test 2021": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Pack Test 2022": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Pack Test 2023": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Pack Test 2024": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Pack Test 2025": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Current Pack Test Date": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Pack Test Date": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Driver Training": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Student: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "Current Refresher Date": "date",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        {
            Notes: {
                # "??": "course",
                # "??": "test_score",
                # "??": "instructor",
                "text_body": "body",
                # "??": "online_component",
                # "??": "location",
                # "??": "document",
            },
        },
        # we don't use it
        #     CurrentAssigned: {
        #         "date": "date"
        #     }
        # },
        # {
        #     RateOfPay: {
        #         "Rate of Pay": "base_rate",  # не работают Currency из Exchange
        #         # "Bonus Rate, 2021": "bonus_rate",
        #         # "??": "office_rate",
        #     },
        #     "extra": {"year": "2018"}
        # },
        # {
        #     RateOfPay: {
        #         "Rate of Pay, 2019": "base_rate",
        #         # "??": "bonus_rate",
        #         # "??": "office_rate",
        #     },
        #     "extra": {"year": "2019"}
        # },
        # {
        #     RateOfPay: {
        #         "Rate of Pay, 2020": "base_rate",
        #         # "??": "bonus_rate",
        #         # "??": "office_rate",
        #     },
        #     "extra": {"year": "2020"}
        # },
        # {
        #     RateOfPay: {
        #         "Rate of Pay, 2021": "base_rate",
        #         # "??": "bonus_rate",
        #         # "??": "office_rate",
        #     },
        #     "extra": {"year": "2021"}
        # },
        # {
        #     RateOfPay: {
        #         "Rate of Pay, 2022": "base_rate",
        #         # "??": "bonus_rate",
        #         # "??": "office_rate",
        #     },
        #     "extra": {"year": "2022"}
        # },
        # {
        #     RateOfPay: {
        #         "Rate of Pay, 2023": "base_rate",
        #         # "??": "bonus_rate",
        #         # "??": "office_rate",
        #     },
        #     "extra": {"year": "2023"}
        # },
        # {
        #     RateOfPay: {
        #         "Rate of Pay, 2024": "base_rate",
        #         # "??": "bonus_rate",
        #         # "??": "office_rate",
        #     },
        #     "extra": {"year": "2024"}
        # },
        # {
        #     RateOfPay: {
        #         "Rate of Pay, 2025": "base_rate",
        #         # "??": "bonus_rate",
        #         # "??": "office_rate",
        #     },
        #     "extra": {"year": "2025"}
        # },
        # {
        #     Fire: {
        #         "fire_number": "fire_number",
        #         "incident_name": "incident_name",
        #         "incident_type": "incident_type",
        #         "agency": "agency",
        #         "state": "state",
        #         "month_year": "month_year",
        #         "hotline_shifts": "hotline_shifts",
        #     }
        # },
        # {
        #     FireRun: {
        #         "crew": "crew",
        #         "rate_of_pay": "rate_of_pay",
        #         "job_title": "job_title",
        #         "CRWB_potential": "CRWB_potential",
        #         "rating": "rating",
        #         "ranking": "ranking",
        #         "professionalism_rating": "professionalism_rating",
        #         "attitude_rating": "attitude_rating",
        #         "sawyer_rating": "sawyer_rating",
        #     }
        # },
        # {
        #     DayOnFire: {
        #         "fire_run": "fire_run",
        #         "job_title": "job_title",
        #         "date": "date",
        #         "clockin1": "clockin1",
        #         "clockout1": "clockout1",
        #         "clockin2": "clockin2",
        #         "clockout2": "clockout2",
        #         "hours_per_day": "hours_per_day",
        #         "reliability_leaving": "reliability_leaving",
        #     }
        # },
        # {
        #     CrewTimeReport: {
        #         "fire_run": "fire_run",
        #         "link_to_document": "link_to_document",
        #     }
        # },
        # {
        #     Crew: {
        #         # "??": "fire",
        #         # "??": "c_number",
        #         "Crew": "contract",
        #         # "??": "crew_name",
        #     }
        # },
        # {
        #     Crew: {
        #         # "??": "fire",
        #         # "??": "c_number",
        #         "Crew 2025": "contract",
        #         # "??": "crew_name",
        #     }
        # },
    ]

    def set_contact(self, employee_obj):
        self.employee_obj = employee_obj
        return self.employee_obj

    def update_or_create_contact(
        self,
        contact_id,
        email,
        last_modified_time,
        last_modified_name,
        datetime_created,
        status_code=Employees.StatusCode.NEW,
        # contact_parameters=None
    ):
        employee_obj, created = Employees.objects.get_or_create(
            # contact_id=contact_id, Этот contact_id не хотим пользовать глючный он в эксчендж
            email=email,
            defaults={
                "contact_id": contact_id,
                "last_modified_time": last_modified_time,
                "last_modified_name": last_modified_name,
                "datetime_created": datetime_created,
                "status_code": status_code,
                "test": 575,
            },
        )

        if not created:
            employee_obj.contact_id = contact_id
            employee_obj.last_modified_time = last_modified_time
            employee_obj.last_modified_name = last_modified_name
            employee_obj.datetime_created = datetime_created
            employee_obj.status_code = status_code
            employee_obj.test = 576
            employee_obj.save()

        self.set_contact(employee_obj=employee_obj)
        return employee_obj, created

    def set_contact_parameters(self, contacts_prop: Contacts_Prop, value):
        if contacts_prop is not None:
            self._contact_parameters[contacts_prop] = value
        return self

    def get_contact_parameters(self) -> Dict[Contacts_Prop, Any]:
        return self._contact_parameters

    def _update_or_create_contact_relations(self, relations_fields=None):
        return

    def do_update_or_create_contact_parameters(self, modified_by=None):
        self.do_update_or_create_contact_parameters_fields(
            parameters_fields=self.get_contact_parameters(), modified_by=modified_by
        )
        return
        # parameters_fields, relations_fields = self.extract_relations_and_parameters_fields()
        # self.do_update_or_create_contact_parameters_fields(parameters_fields=parameters_fields)
        # self.do_update_or_create_contact_relations_fields(relations_fields=relations_fields)

    def do_update_or_create_contact_parameters_fields(
        self,
        parameters_fields: Dict[Contacts_Prop, Any],
        modified_by: Optional[str] = None,
    ):
        if not self.employee_obj:
            return
        logger = logging_uniq_name.getLogger("my_log")

        new_params_prop_to_val = {}
        old_params_prop_to_val = {}
        existing_params_prop_to_val = {}
        to_delete_params_prop_to_val = {}

        contacts_prop_ids = [prop.id for prop in parameters_fields.keys()]

        existing_objs = Employees_Parameters.objects.filter(
            contacts_prop_id__in=contacts_prop_ids, employee=self.employee_obj
        ).select_related("contacts_prop")

        existing_objs_dict = {obj.contacts_prop_id: obj for obj in existing_objs}

        # with transaction.atomic():
        for contacts_prop_i, value in parameters_fields.items():
            if not contacts_prop_i:
                continue

            obj = existing_objs_dict.get(contacts_prop_i.id)

            if contacts_prop_i.property_type == Contacts_Prop.TypeChoices.DOCUMENT:
                value = None
                if value:
                    value = next(reversed(value.values()), None)
                if not isinstance(value, dict) or not value:
                    continue

            if obj:
                if contacts_prop_i.property_type == Contacts_Prop.TypeChoices.ARRAY:
                    old_value = obj.value_array
                else:
                    old_value = obj.value
                # print("______________: ", self.employee_obj.id)
                # print("self.employee_obj: ", self.employee_obj)
                # print("old_value, value: ", old_value, value)
                if value in [None, "", []]:
                    try:
                        obj.delete()
                        to_delete_params_prop_to_val[contacts_prop_i] = None
                        old_params_prop_to_val[contacts_prop_i] = old_value
                    except Exception as e:
                        logger.error(
                            "\n================ DELETE do_update_or_create_contact_parameters_fields ================\n"
                            f"employee_obj.id : {self.employee_obj.id}\n"
                            f"contacts_prop_i : {contacts_prop_i.property_name}\n"
                            f"value           : {value}\n"
                            f"Error           : {e}\n"
                        )
                elif str(old_value) != str(value):
                    try:
                        if (
                            contacts_prop_i.property_type
                            == Contacts_Prop.TypeChoices.ARRAY
                        ):
                            obj.value_array = value
                        else:
                            obj.value = value
                        obj.modified_by = modified_by
                        obj.save()
                        existing_params_prop_to_val[contacts_prop_i] = value
                        old_params_prop_to_val[contacts_prop_i] = old_value
                    except Exception as e:
                        logger.error(
                            "\n================ UPDATE do_update_or_create_contact_parameters_fields ================\n"
                            f"employee_obj.id : {self.employee_obj.id}\n"
                            f"contacts_prop_i : {contacts_prop_i.property_name}\n"
                            f"value           : {value}\n"
                            f"Error           : {e}\n"
                        )
            else:
                if value not in (None, "", []):
                    if contacts_prop_i.property_name not in (
                        "text_body",
                        "cropped_picture_for_red_card",
                    ):
                        with transaction.atomic():
                            if (
                                contacts_prop_i.property_type
                                == Contacts_Prop.TypeChoices.ARRAY
                            ):
                                new_obj = Employees_Parameters(
                                    contacts_prop=contacts_prop_i,
                                    employee=self.employee_obj,
                                    value_array=value,
                                    modified_by=modified_by,
                                )
                            else:
                                new_obj = Employees_Parameters(
                                    contacts_prop=contacts_prop_i,
                                    employee=self.employee_obj,
                                    value=value,
                                    modified_by=modified_by,
                                )
                            # if len(str(value)) < 512:
                            #     new_obj = Employees_Parameters(
                            #         contacts_prop=contacts_prop_i,
                            #         employee=self.employee_obj,
                            #         value=value,
                            #         modified_by=modified_by,
                            #     )
                            # else:
                            #     new_obj = Employees_Parameters(
                            #         contacts_prop=contacts_prop_i,
                            #         employee=self.employee_obj,
                            #         value_long=value,
                            #         modified_by=modified_by,
                            #     )
                            new_obj.save()
                            old_params_prop_to_val[contacts_prop_i] = None
                            new_params_prop_to_val[contacts_prop_i] = value

        self._old_params = old_params_prop_to_val
        self._new_params = new_params_prop_to_val
        self._updated_params = existing_params_prop_to_val
        self._delete_params = to_delete_params_prop_to_val

        from core.tasks import generate_entities_from_contact_params_task

        # generate_entities_from_contact_params_task.run(employee_id=self.employee_obj.id)
        if settings.DEBUG:
            generate_entities_from_contact_params_task.run(
                employee_id=self.employee_obj.id
            )
        else:
            generate_entities_from_contact_params_task.delay(
                employee_id=self.employee_obj.id
            )

    # @staticmethod
    # def get_defaults_from_incoming_values(keys_map: dict, incoming_values: dict) -> dict:
    #     defaults = {}
    #     for friendly_key, model_field in keys_map.items():
    #         if friendly_key in incoming_values:
    #             value = incoming_values[friendly_key]
    #             defaults[model_field] = value
    #         else:
    #             defaults[
    #                 model_field] = None  # или вообще тут значения брать из таблицы Employees_Parameters
    #                                      # Или другое значение по умолчанию, если необходимо
    #
    #     return defaults

    # def do_update_or_create_contact_relations_fields(self, relations_fields: Dict[Contacts_Prop, Any]):
    #     # This is an old idea and method in its infancy
    #     mspa_defaults = {}
    #     identification_documents_defaults = {}
    #
    #     for contacts_prop_i, value in relations_fields.items():
    #         field_name, defaults_key = self.field_mappings[contacts_prop_i.property_name]
    #         self._updated_params[contacts_prop_i] = value
    #         if defaults_key == "mspa_defaults":
    #             mspa_defaults[field_name] = value
    #         elif defaults_key == "identification_documents_defaults":
    #             identification_documents_defaults[field_name] = value
    #
    #     if mspa_defaults:
    #         MSPA.objects.update_or_create(
    #             contact=self.employee_obj,
    #             # is_primary=True,
    #             defaults=mspa_defaults
    #         )
    #
    #     if identification_documents_defaults:
    #         IdentificationDocuments.objects.update_or_create(
    #             contact=self.employee_obj,
    #             # is_primary=True,
    #             defaults=identification_documents_defaults
    #         )

    # рабочий метод, но скою за ненадобностю
    # def extract_relations_and_parameters_fields(self) -> Tuple[Dict[Contacts_Prop, Any], Dict[Contacts_Prop, Any]]:
    #     contact_parameters = self.get_contact_parameters()
    #     relations_fields = {}
    #     parameters_fields = {}
    #     for contacts_prop_i, value in contact_parameters.items():
    #         if contacts_prop_i.property_name in self.field_mappings:
    #             relations_fields[contacts_prop_i] = value
    #         else:
    #             parameters_fields[contacts_prop_i] = value
    #     return parameters_fields, relations_fields

    # рабочий метод, но скрою за ненадобностю
    # def _set_prop_obj_by_property_name_dict(self, contact_parameters):
    #     parameters_keys_list = list(contact_parameters.keys())
    #     contacts_prop_obj = Contacts_Prop.objects.filter(visibility=True, property_name__in=parameters_keys_list)
    #     self._prop_obj_by_property_name_dict = {obj.property_name: obj for obj in contacts_prop_obj}

    def get_new_parameters_obj(self):
        return self._new_params

    def get_old_parameters_obj(self):
        return self._old_params

    def get_updated_parameters_obj(self):
        return self._updated_params

    def get_delete_parameters_obj(self):
        return self._delete_params

    def get_all_changed_parameters_obj(self):
        return {**self._new_params, **self._updated_params, **self._delete_params}

    # def get_all_parameters_for_contact(self, contact: Employees):
    #     employee_obj = self.employee_obj
    #     employee_obj = contact
    #
    #     print(employee_obj.email)
    #     parameters = employee_obj.contacts_parameters_entries.all()
    #     for param in parameters:
    #         print(f"Parameter ID: {param.contacts_parameters.property_name}, Value: {param.value}")
    #
    #     mspa = contact.mspa_entries.get(is_primary=True)
    #     custom_fields_obj = Custom_Fields.objects.filter(exchange_property="")
    #
    #
    #     # Извлечение restriction из всех связанных объектов IdentificationDocuments
    #     for idoc in contact.identification_documents_entries.all():
    #         print(f"Restriction: {idoc.restriction}")

    @staticmethod
    def sync_crew_from_contact_params(employee: Employees):
        crew_value = (
            Employees_Parameters.objects.filter(
                employee=employee, contacts_prop__property_name="Crew"
            )
            .values_list("value", flat=True)
            .first()
        )

        new_crew = (
            FireCrew.objects.filter(name=crew_value).only("id").first()
            if crew_value
            else None
        )

        current_crew_id = getattr(employee.fire_crew, "id", None)
        new_crew_id = getattr(new_crew, "id", None)

        if current_crew_id != new_crew_id:
            Employees.objects.filter(pk=employee.pk).update(fire_crew_id=new_crew_id)

    @staticmethod
    def generate_entities_from_contact_params(employee_id):
        employee = Employees.objects.get(id=employee_id)
        EmployeesService.sync_crew_from_contact_params(employee=employee)
        with transaction.atomic():
            for dictionary in EmployeesService.dictionary_list:
                dictionary = copy.deepcopy(dictionary)
                extra = dictionary.get("extra", None)
                # print("___")
                # # print("===dictionary", dictionary)
                # # print("===extra=====", extra)
                for model_class, keys_map in dictionary.items():
                    if not isinstance(model_class, type):
                        continue
                    keys_list = keys_map.keys()
                    # print("keys_map", keys_map)
                    # print("model_class", model_class)
                    # print("keys_list", keys_list)
                    # if isinstance(model_field, list):
                    employees_parameters = Employees_Parameters.objects.filter(
                        employee=employee, contacts_prop__property_name__in=keys_list
                    ).select_related("contacts_prop")

                    defaults = {}
                    lookup = {"employee": employee}

                    for parameter in employees_parameters:
                        # print("parameter.contacts_prop.property_name:", parameter.contacts_prop.property_name)
                        # print("parameter.contacts_prop.property_type:", parameter.contacts_prop.property_type)
                        # print("parameter.contacts_prop.datetime_format:", parameter.contacts_prop.datetime_format)
                        # print("parameter.value:", parameter.value)
                        model_field = keys_map[parameter.contacts_prop.property_name]
                        value = parameter.value
                        try:
                            value = SanitazerService.normalize_from_str_by_property_type(
                                value=value,
                                property_type=parameter.contacts_prop.property_type,
                                output_format=parameter.contacts_prop.datetime_format,
                            )
                        except Exception:
                            if not isinstance(value, datetime.date):
                                value = SanitazerService.datetime_str_to_datetime(value)

                        # это можно удалить после импорта.
                        if (
                            model_class.__name__ == RateOfPay.__name__
                            and model_class.__module__ == RateOfPay.__module__
                        ):
                            if model_field in [
                                "base_rate",
                                "office_rate",
                                "bonus_rate",
                            ]:
                                try:
                                    value = Decimal(value.replace("$", "")).quantize(
                                        Decimal("0.01"), rounding=ROUND_HALF_UP
                                    )
                                except Exception:
                                    print("================ERROR================")
                                    print(
                                        "Decimal id NOT Decimal __ --------------------========"
                                    )
                                    print(
                                        "User_email __ --------------------========",
                                        employee.email,
                                    )
                                    print("model_field: ", model_field)
                                    print("value", value)
                                    value = Decimal(543.21).quantize(
                                        Decimal("0.01"), rounding=ROUND_HALF_UP
                                    )
                                    logger = logging_uniq_name.getLogger("my_log")
                                    logger.error(
                                        "\n================ ERROR ================\n"
                                        f"User_email    : {employee.email}\n"
                                        f"model_field   : {model_field}\n"
                                        f"value         : {value}\n"
                                        f"type          : {type(value)}\n"
                                    )

                        if (
                            model_class.__name__ == DispatchingStatus.__name__
                            and model_class.__module__ == DispatchingStatus.__module__
                        ):
                            if model_field == "dispatch_status":
                                try:
                                    value = DispatchingStatus.get_dispatch_status_key(
                                        value
                                    )
                                except Exception:
                                    print("================ERROR================")
                                    print(
                                        "User_email __ --------------------========",
                                        employee.email,
                                    )
                                    print("model_field: ", model_field)
                                    print("value", value)
                                    print("type", type(value))
                                    value = None
                                    logger = logging_uniq_name.getLogger("my_log")
                                    logger.error(
                                        "\n================ ERROR ================\n"
                                        f"User_email    : {employee.email}\n"
                                        f"model_field   : {model_field}\n"
                                        f"value         : {value}\n"
                                        f"type          : {type(value)}\n"
                                    )

                        # if model_class.__name__ == DispatchingStatus.__name__ 
                        # and model_class.__module__ == DispatchingStatus.__module__:
                        #     if model_field == "date":
                        #         try:
                        #             if not value:
                        #                 value = now().date()
                        #         except Exception:
                        #             print("================ERROR================")
                        #             print("User_email __ --------------------========", employee.email)
                        #             print("model_field: ", model_field)
                        #             print("value", value)
                        #             print("type", type(value))
                        #             value = None
                        #             logger = logging_uniq_name.getLogger("my_log")
                        #             logger.error(
                        #                 "\n================ ERROR ================\n"
                        #                 f"User_email    : {employee.email}\n"
                        #                 f"model_field   : {model_field}\n"
                        #                 f"value         : {value}\n"
                        #                 f"type          : {type(value)}\n"
                        #             )
                        #
                        # if model_class.__name__ == DispatchingStatus.__name__ 
                        # and model_class.__module__ == DispatchingStatus.__module__:
                        #     if model_field == "time":
                        #         try:
                        #             if not value:
                        #                 value = now().time()
                        #         except Exception:
                        #             print("================ERROR================")
                        #             print("User_email __ --------------------========", employee.email)
                        #             print("model_field: ", model_field)
                        #             print("value", value)
                        #             print("type", type(value))
                        #             value = None
                        #             logger = logging_uniq_name.getLogger("my_log")
                        #             logger.error(
                        #                 "\n================ ERROR ================\n"
                        #                 f"User_email    : {employee.email}\n"
                        #                 f"model_field   : {model_field}\n"
                        #                 f"value         : {value}\n"
                        #                 f"type          : {type(value)}\n"
                        #             )

                        if (
                            model_class.__name__ == DispatchingStatus.__name__
                            and model_class.__module__ == DispatchingStatus.__module__
                        ):
                            if model_field == "ETA":
                                try:
                                    if not isinstance(value, datetime.date):
                                        value = (
                                            SanitazerService.datetime_str_to_datetime(
                                                value
                                            )
                                        )
                                except Exception:
                                    print("================ERROR================")
                                    print(
                                        "User_email __ --------------------========",
                                        employee.email,
                                    )
                                    print("model_field: ", model_field)
                                    print("value", value)
                                    print("type", type(value))
                                    value = None
                                    logger = logging_uniq_name.getLogger("my_log")
                                    logger.error(
                                        "\n================ ERROR ================\n"
                                        f"User_email    : {employee.email}\n"
                                        f"model_field   : {model_field}\n"
                                        f"value         : {value}\n"
                                        f"type          : {type(value)}\n"
                                    )

                        if (
                            model_class.__name__ == MSPA.__name__
                            and model_class.__module__ == MSPA.__module__
                        ):
                            if model_field == "expiration_date":
                                try:
                                    if not isinstance(value, datetime.date):
                                        value = (
                                            SanitazerService.datetime_str_to_datetime(
                                                value
                                            )
                                        )
                                except Exception:
                                    print("================ERROR================")
                                    print(
                                        "User_email __ --------------------========",
                                        employee.email,
                                    )
                                    print("model_field: ", model_field)
                                    print("value", value)
                                    print("type", type(value))
                                    value = None
                                    logger = logging_uniq_name.getLogger("my_log")
                                    logger.error(
                                        "\n================ ERROR ================\n"
                                        f"User_email    : {employee.email}\n"
                                        f"model_field   : {model_field}\n"
                                        f"value         : {value}\n"
                                        f"type          : {type(value)}\n"
                                    )

                        # if (
                        #     model_class.__name__ == IdentificationDocuments.__name__
                        #     and model_class.__module__
                        #     == IdentificationDocuments.__module__
                        # ):
                        #     if model_field in [
                        #         "issue_date",
                        #         "expiration_date",
                        #     ]:
                        #         try:
                        #             if not isinstance(value, datetime.date):
                        #                 value = (
                        #                     SanitazerService.datetime_str_to_datetime(
                        #                         value
                        #                     )
                        #                 )
                        #         except Exception:
                        #             print("================ERROR================")
                        #             print(
                        #                 "User_email __ --------------------========",
                        #                 employee.email,
                        #             )
                        #             print("model_field: ", model_field)
                        #             print("value", value)
                        #             print("type", type(value))
                        #             value = None
                        #             logger = logging_uniq_name.getLogger("my_log")
                        #             logger.error(
                        #                 "\n================ ERROR ================\n"
                        #                 f"User_email    : {employee.email}\n"
                        #                 f"model_field   : {model_field}\n"
                        #                 f"value         : {value}\n"
                        #                 f"type          : {type(value)}\n"
                        #             )

                        if (
                            model_class.__name__ == Interaction.__name__
                            and model_class.__module__ == Interaction.__module__
                        ):
                            if model_field in [
                                "date",
                            ]:
                                try:
                                    if not isinstance(value, datetime.date):
                                        value = (
                                            SanitazerService.datetime_str_to_datetime(
                                                value
                                            )
                                        )
                                except Exception:
                                    print("================ERROR================")
                                    print(
                                        "User_email __ --------------------========",
                                        employee.email,
                                    )
                                    print("model_field: ", model_field)
                                    print("value", value)
                                    print("type", type(value))
                                    value = None
                                    logger = logging_uniq_name.getLogger("my_log")
                                    logger.error(
                                        "\n================ ERROR ================\n"
                                        f"User_email    : {employee.email}\n"
                                        f"model_field   : {model_field}\n"
                                        f"value         : {value}\n"
                                        f"type          : {type(value)}\n"
                                    )

                        # if model_class.__name__ == Availability.__name__ 
                        # and model_class.__module__ == Availability.__module__:
                        # Перенес в сигналы

                        if (
                            model_class.__name__ == Student.__name__
                            and model_class.__module__ == Student.__module__
                        ):
                            if parameter.contacts_prop.property_name in [
                                "Refresher 2024",
                                "Refresher 2025",
                            ]:
                                training_type = TrainingType.objects.get(name="RT-130")

                            if parameter.contacts_prop.property_name in [
                                "RT-130 Webinar 2020",
                                "RT-130 Webinar 2021",
                                "RT-130 Webinar 2022",
                                "RT-130 Webinar 2023",
                                "RT-130 Webinar 2024",
                                "RT-130 Webinar 2025",
                            ]:
                                training_type = TrainingType.objects.get(
                                    name="RT-130 Webinar"
                                )

                            if parameter.contacts_prop.property_name in [
                                "S130",
                            ]:
                                training_type = TrainingType.objects.get(name="S-130")

                            if parameter.contacts_prop.property_name in [
                                "S130 Online Component",
                            ]:
                                training_type = TrainingType.objects.get(
                                    name="S-130 Online Component"
                                )

                            if parameter.contacts_prop.property_name in [
                                "S-131",
                            ]:
                                if not isinstance(value, datetime.date):
                                    value = SanitazerService.datetime_str_to_datetime(
                                        value
                                    )
                                training_type = TrainingType.objects.get(name="S-131")

                            if parameter.contacts_prop.property_name in [
                                "S190",
                            ]:
                                training_type = TrainingType.objects.get(name="S-190")

                            if parameter.contacts_prop.property_name in [
                                "S-190 Webinar",
                            ]:
                                training_type = TrainingType.objects.get(
                                    name="S-190 Webinar"
                                )

                            if parameter.contacts_prop.property_name in [
                                "S-212",
                            ]:
                                if not isinstance(value, datetime.date):
                                    value = SanitazerService.datetime_str_to_datetime(
                                        value
                                    )
                                training_type = TrainingType.objects.get(name="S-212")

                            if parameter.contacts_prop.property_name in [
                                "S-230",
                            ]:
                                training_type = TrainingType.objects.get(name="S-230")

                            if parameter.contacts_prop.property_name in [
                                "S-290",
                            ]:
                                training_type = TrainingType.objects.get(name="S-290")

                            if parameter.contacts_prop.property_name in [
                                "L180",
                            ]:
                                training_type = TrainingType.objects.get(name="L-180")

                            if parameter.contacts_prop.property_name in [
                                "L-180 Webinar",
                            ]:
                                training_type = TrainingType.objects.get(
                                    name="L-180 Webinar"
                                )

                            if parameter.contacts_prop.property_name in [
                                "ICS100",
                            ]:
                                training_type = TrainingType.objects.get(name="IS-100")

                            if parameter.contacts_prop.property_name in [
                                "IS-200.b",
                            ]:
                                training_type = TrainingType.objects.get(name="IS-200")

                            if parameter.contacts_prop.property_name in [
                                "I700",
                            ]:
                                if not isinstance(value, datetime.date):
                                    value = SanitazerService.datetime_str_to_datetime(
                                        value
                                    )
                                training_type = TrainingType.objects.get(name="IS-700")

                            if parameter.contacts_prop.property_name in [
                                "M-410",
                            ]:
                                training_type = TrainingType.objects.get(name="M-410")

                            # print("parameter.contacts_prop.property_name: ALL", parameter.contacts_prop.property_name)
                            if parameter.contacts_prop.property_name in [
                                "Pack Test 2020",
                                "Pack Test 2021",
                                "Pack Test 2022",
                                "Pack Test 2023",
                                "Pack Test 2024",
                                "Pack Test 2025",
                                "Current Pack Test Date",
                            ]:
                                # print("parameter.contacts_prop.property_name", parameter.contacts_prop.property_name)
                                # print("value", value)
                                if isinstance(value, datetime.date):
                                    value = value.strftime("%Y-%m-%d")
                                elif isinstance(value, str):
                                    value = value.split(" ")[0]
                                training_type = TrainingType.objects.get(
                                    name="Pack Test"
                                )

                            if parameter.contacts_prop.property_name in [
                                "Pack Test Date",
                            ]:
                                value = value.strftime("%Y-%m-%d")
                                training_type = TrainingType.objects.get(
                                    name="Pack Test"
                                )

                            if parameter.contacts_prop.property_name in [
                                "Current Refresher Date",
                            ]:
                                value = value.strftime("%Y-%m-%d")
                                training_type = TrainingType.objects.get(name="RT-130")

                            if parameter.contacts_prop.property_name in [
                                "Driver Training",
                            ]:
                                training_type = TrainingType.objects.get(
                                    name="Driver Training"
                                )

                            if training_type:
                                course_obj, created = Course.objects.get_or_create(
                                    training_type=training_type,
                                    defaults={"training_type": training_type},
                                )
                                try:
                                    training_class_obj, created = (
                                        TrainingClass.objects.get_or_create(
                                            course=course_obj,
                                            date=value,
                                            defaults={
                                                "course": course_obj,
                                                "date": value,
                                            },
                                        )
                                    )
                                    model_field = "training_class"
                                    value = training_class_obj
                                except Exception:
                                    print("___")
                                    print("EEERRRRRRRRRRRRRROOOOOOORRRRRRRRRRRRR")
                                    print(
                                        "property_name",
                                        parameter.contacts_prop.property_name,
                                    )
                                    print("value", value)
                                    print("type(val)", type(value))
                                    logger = logging_uniq_name.getLogger("my_log")
                                    logger.error(
                                        "\n================ ERROR ================\n"
                                        f"property_name    : {parameter.contacts_prop.property_name}\n"
                                        f"value         : {value}\n"
                                        f"type          : {type(value)}\n"
                                    )
                                    continue

                        defaults[model_field] = value
                        lookup[model_field] = value

                    if defaults:
                        if extra:
                            # print("extra", extra)
                            for key, value in extra.items():
                                defaults[key] = value
                                lookup[key] = value
                        try:
                            # print("model_class: ", model_class)
                            # print("defaults: ", defaults)
                            # print("lookup: ", lookup)

                            if (
                                model_class.__name__ == Student.__name__
                                and model_class.__module__ == Student.__module__
                            ):
                                obj = model_class.objects.filter(**lookup).first()
                            else:
                                last_id = (
                                    model_class.objects.filter(employee=employee)
                                    .order_by("-id")
                                    .values_list("id", flat=True)
                                    .first()
                                )

                                if last_id:
                                    obj = model_class.objects.filter(
                                        id=last_id, **lookup
                                    ).first()
                                else:
                                    obj = None

                            if obj is None:
                                obj = model_class.objects.create(
                                    **{**lookup, **defaults}
                                )
                                obj.modified_by = employee.last_modified_name
                                obj.save(update_fields=["modified_by"])
                        except Exception as e:
                            print("EEERRRRRRRRRRRRRROOOOOOORRRRRRRRRRRRR")
                            print("model_class", model_class)
                            print("lookup", lookup)
                            print("defaults", defaults)
                            logger = logging_uniq_name.getLogger("my_log")
                            logger.error(
                                "\n================ ERROR ================\n"
                                f"model_class    : {model_class}\n"
                                f"lookup         : {lookup}\n"
                                f"defaults       : {defaults}\n"
                                f"error_message  : {str(e)}\n"
                                f"traceback      : {traceback.format_exc()}\n"
                            )
                            if settings.DEBUG:
                                raise

    @staticmethod
    def save_or_update_employee_last_updates(
        contact_id: str,
        type_api: ApiType,
        date_updated=None,
        date_updated_str: str = None,
    ):
        # with transaction.atomic():
        obj, created = Employee_Last_Updates.objects.update_or_create(
            type=type_api.name,
            defaults={
                "contact_id": contact_id,
                "date_updated": date_updated,
                "date_updated_str": str(date_updated_str),
                "updated_at": timezone.now(),
            },
        )
        return obj

    @staticmethod
    def get_employee_last_updates(type_api: ApiType):
        return Employee_Last_Updates.objects.get(type=type_api.name)

    @staticmethod
    @lru_cache(maxsize=1)
    def get_all_fields_for_employee_table():
        contacts_prop_columns_list = list(
            Contacts_Prop.objects.filter(visibility=True).values_list(
                "property_name", flat=True
            )
        )

        from company.views.EmployeesParametersAjaxView import get_relations_params

        relations_params, _ = get_relations_params()
        columns = ["students"] + contacts_prop_columns_list + relations_params
        return sorted(columns, key=str.lower)

    @staticmethod
    def get_fields_for_employee_table(user=None, type_param=None):
        user = User.objects.get(id=1)
        if type_param not in Type.__members__:
            raise
        columns = (
            Fields_Settings.objects.filter(user=user, type=type_param)
            .values_list("fields", flat=True)
            .first()
        )
        if columns:
            return columns

        return EmployeesService.get_all_fields_for_employee_table()


def get_employee_parameters(employee: Employees, parameters: list[dict]):
    response = {}
    for param in parameters:
        param_name = param.get("name")
        employees_parameters_list = list(
            Employees_Parameters.objects.filter(
                employee=employee, contacts_prop__property_name=param_name
            )
        )

        if len(employees_parameters_list) > 1:
            raise Exception(
                f"Multiple entries found for employee_id={employee.id} and parameter_name={param_name}"
            )

        employees_parameters_obj = (
            employees_parameters_list[0] if employees_parameters_list else None
        )
        if employees_parameters_obj:
            response[employees_parameters_obj.contacts_prop.property_name] = (
                employees_parameters_obj.value
            )

    return response


def update_employee_tags(employee: Employees, modified_name=None):
    parameters_dict = {}
    param_name = "tags"
    param_value = list(employee.tags.values_list("name", flat=True))

    contacts_prop_obj = Contacts_Prop.objects.filter(property_name=param_name).first()
    if contacts_prop_obj:
        parameters_dict[contacts_prop_obj] = param_value

    update_employee_parameters_raw(
        employee=employee, parameters=parameters_dict, modified_name=modified_name
    )


def update_employee_parameters_raw(
    employee: Employees, parameters: dict, modified_name=None
):
    from core.tasks import handle_sync_delivery_log_task
    from synchronization.models import Sync_Delivery_Logs
    from synchronization.services.SyncDeliveryService import SyncDeliveryService

    if modified_name:
        # employee.last_modified_time = datetime.now().astimezone()
        employee.last_modified_name = modified_name
        employee.save()

    employees_service = EmployeesService()
    employees_service.set_contact(employee_obj=employee)

    for contacts_prop_i, param_value in parameters.items():
        employees_service.set_contact_parameters(contacts_prop_i, param_value)

    employees_service.do_update_or_create_contact_parameters(modified_by=modified_name)
    changed_parameters = employees_service.get_all_changed_parameters_obj()
    old_parameters = employees_service.get_old_parameters_obj()

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
        modified_by=modified_name,
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            transaction.on_commit(
                lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                    sync_id
                )
            )
            # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
        modified_by=modified_name,
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            transaction.on_commit(
                lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                    sync_id
                )
            )
            # handle_sync_delivery_log_task.delay(sync_delivery_log_id)


def find_property_name_by_instance(instance):
    for dictionary in EmployeesService.dictionary_list:
        dictionary = dictionary.copy()
        extra = dictionary.pop("extra", None)

        for model_class, field_mapping in dictionary.items():
            if not isinstance(model_class, type):
                continue

            if not isinstance(instance, model_class):
                continue

            for friendly_name, model_field in field_mapping.items():
                instance_value = getattr(instance, model_field, None)

                if instance_value is None:
                    continue

                # Учитываем дополнительные фильтры (например, type, year)
                if extra:
                    match = True
                    for key, expected_value in extra.items():
                        actual_value = getattr(instance, key, None)
                        if str(actual_value) != str(expected_value):
                            match = False
                            break
                    if not match:
                        continue

                return friendly_name, instance_value

    return None, None


def get_employees_by_filter(filter_id: int):
    from company.views.EmployeesParametersAjaxView import (
        get_relation_param_to_annotation,
        get_employees_all_prefetch_related,
        parse_or_filter_groups,
        apply_all_filters_with_or,
    )
    from core.models import Saved_Filter

    filter_obj = Saved_Filter.objects.get(id=filter_id)
    display_fields = filter_obj.columns
    params = filter_obj.params

    relation_map = get_relation_param_to_annotation()

    employees_qs = get_employees_all_prefetch_related().order_by("-updated_at")

    for field in display_fields:
        if field in relation_map and relation_map[field]:
            alias, annotation = relation_map[field]
            employees_qs = employees_qs.annotate(**{alias: annotation})

    or_filter_groups, group_logic_map = parse_or_filter_groups(params.items())
    employees_qs = apply_all_filters_with_or(
        employees_qs, or_filter_groups, group_logic_map
    )

    return employees_qs
