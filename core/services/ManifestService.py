from django.conf import settings
from django.db.models import OuterRef, Exists
from django.utils.timezone import now
from datetime import timedelta

from company.models import Employees, Employees_Parameters
from core.tasks import check_possibility_firecrew_task
from exchange.models import Contacts_Prop


class ManifestService:
    # если хочу брать манифест, только самый свежий по updated_at
    # @staticmethod
    # def update_is_manifested_flags(employee_id=None):
    #     twelve_months_ago = now().date() - timedelta(days=365)
    #
    #     latest_manifest_date = Subquery(
    #         CompanyManifest.objects.filter(employee=OuterRef("pk"))
    #         .order_by("-updated_at")
    #         .values("date")[:1]
    #     )
    #
    #     queryset = Employees.objects.annotate(
    #         latest_date=latest_manifest_date
    #     )
    #
    #     if employee_id:
    #         queryset = queryset.filter(id=employee_id)
    #
    #     manifested_ids = list(queryset.filter(latest_date__gte=twelve_months_ago).values_list("id", flat=True))
    #     not_manifested_ids = list(queryset.filter(latest_date__lt=twelve_months_ago).values_list("id", flat=True))
    #
    #     if manifested_ids:
    #         Employees.objects.filter(id__in=manifested_ids).update(is_manifested=True)
    #     if not_manifested_ids:
    #         Employees.objects.filter(id__in=not_manifested_ids).update(is_manifested=False)

    # если хочу выбирать из всех манифестов
    @staticmethod
    def update_is_manifested_flags_from_all_dates(employee_id=None):
        twelve_months_ago = now().date() - timedelta(days=365)

        property_names = [
            "Manifest Date",
            "Manifest Date, 2025"
        ]

        manifest_prop_ids = list(
            Contacts_Prop.objects.filter(property_name__in=property_names)
            .values_list("id", flat=True)
        )

        recent_manifest_exists = Exists(
            Employees_Parameters.objects.filter(
                employee=OuterRef("pk"),
                contacts_prop_id__in=manifest_prop_ids,
                value_date__gte=twelve_months_ago
            )
        )

        queryset = Employees.objects.annotate(has_recent=recent_manifest_exists)
        if employee_id:
            queryset = queryset.filter(id=employee_id)

        manifested_ids = list(queryset.filter(has_recent=True).values_list("id", flat=True))
        not_manifested_ids = list(queryset.filter(has_recent=False).values_list("id", flat=True))

        if manifested_ids:
            Employees.objects.filter(id__in=manifested_ids).update(is_manifested=True)
        if not_manifested_ids:
            Employees.objects.filter(id__in=not_manifested_ids).update(is_manifested=False)

            for employee_id in not_manifested_ids:
                if settings.DEBUG:
                    check_possibility_firecrew_task.run(employee_id=employee_id)
                else:
                    check_possibility_firecrew_task.delay(employee_id=employee_id)

    # если хочу выбирать из всех манифестов
    # @staticmethod
    # def update_is_manifested_flags_from_all_dates_OLD(employee_id=None):
    #     twelve_months_ago = now().date() - timedelta(days=365)
    #
    #     recent_manifest_exists = Exists(
    #         CompanyManifest.objects.filter(
    #             employee=OuterRef("pk"),
    #             date__gte=twelve_months_ago
    #         )
    #     )
    #
    #     queryset = Employees.objects.annotate(has_recent=recent_manifest_exists)
    #     if employee_id:
    #         queryset = queryset.filter(id=employee_id)
    #
    #     manifested_ids = list(
    #         queryset.filter(has_recent=True).values_list("id", flat=True)
    #     )
    #
    #     not_manifested_ids = list(
    #         queryset.filter(has_recent=False).values_list("id", flat=True)
    #     )
    #
    #     if manifested_ids:
    #         Employees.objects.filter(id__in=manifested_ids).update(is_manifested=True)
    #     if not_manifested_ids:
    #         Employees.objects.filter(id__in=not_manifested_ids).update(is_manifested=False)
