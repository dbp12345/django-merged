import datetime

from django.utils import timezone

from company.services.EmployeesService import EmployeesService
from core.models.EmployeeLastUpdates import ApiType
from paychex.services import (
    PaychexCompanyWorkersService,
    PaychexPayPeriodService,
    PaychexPaycheckService,
)


def update_only_current_all():
    now = timezone.localtime()
    last_updates_obj = EmployeesService.get_employee_last_updates(
        type_api=ApiType.PAYCHEX
    )
    date_updated = timezone.localtime(last_updates_obj.date_updated)
    utc_dt = date_updated.astimezone(datetime.timezone.utc).replace(microsecond=0)
    s = utc_dt.isoformat().replace("+00:00", "Z")

    date_updated_from = (
        (date_updated - datetime.timedelta(days=15))
        .astimezone(datetime.timezone.utc)
        .replace(microsecond=0)
    )
    utc_dt_from = date_updated_from.astimezone(datetime.timezone.utc).replace(
        microsecond=0
    )
    s_from = utc_dt_from.isoformat().replace("+00:00", "Z")

    date_updated_to = (
        (date_updated + datetime.timedelta(days=7))
        .astimezone(datetime.timezone.utc)
        .replace(microsecond=0)
    )
    utc_dt_to = date_updated_to.astimezone(datetime.timezone.utc).replace(microsecond=0)
    s_to = utc_dt_to.isoformat().replace("+00:00", "Z")

    paychexCompanyWorkersService = PaychexCompanyWorkersService
    paychexCompanyWorkersService.sync_company_workers_from_api(
        from_date=s, to_date=s_to
    )

    paychexPayPeriodService = PaychexPayPeriodService
    payperiods = paychexPayPeriodService.sync_payperiod_from_api(
        from_date=s_from, to_date=s_to
    )

    paychexPaycheckService = PaychexPaycheckService
    for pay_period in payperiods:
        paychexPaycheckService.sync_checks_for_payperiod(
            payperiod_id=pay_period.payperiod_id
        )

    EmployeesService.save_or_update_employee_last_updates(
        contact_id="None",
        type_api=ApiType.PAYCHEX,
        date_updated=now,
    )
