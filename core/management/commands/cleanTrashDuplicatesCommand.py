from django.core.management.base import BaseCommand

from company.models import Availability, DispatchingStatus, Interaction
from django.db.models import Count


class Command(BaseCommand):
    help = "cleanTrashDuplicatesCommand"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"Run cleanTrashDuplicatesCommand."))

        # Availability
        Availability.objects.filter(notes__isnull=True).update(notes="")
        Availability.objects.filter(location_state__isnull=True).update(location_state="")
        Availability.objects.filter(location_city__isnull=True).update(location_city="")

        dupes = (
            Availability.objects
            .values(
                "employee",
                "availability_status",
                # "date_of_change",
                "date_of_expected_future_change",
                "travel_time",
                "location_state",
                "location_city",
                "notes",
            )
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for d in dupes:
            entries = Availability.objects.filter(
                employee=d["employee"],
                availability_status=d["availability_status"],
                # date_of_change=d["date_of_change"],
                date_of_expected_future_change=d["date_of_expected_future_change"],
                travel_time=d["travel_time"],
                location_state=d["location_state"],
                location_city=d["location_city"],
                notes=d["notes"],
            ).order_by("id")  # или по updated_at, если нужно

            keep_one = entries.first()
            for e in entries:
                if e != keep_one:
                    print("deleting", e.id, e.employee.id, e.availability_status, e.date_of_expected_future_change, e.location_state, e.location_city, e.travel_time, e.notes, )
                    e.delete()
                else:
                    print("stay    ", e.id, e.employee.id, e.availability_status, e.date_of_expected_future_change, e.location_state, e.location_city, e.travel_time, e.notes, )

        # DispatchingStatus
        DispatchingStatus.objects.filter(notes__isnull=True).update(notes="")
        DispatchingStatus.objects.filter(location__isnull=True).update(location="")
        DispatchingStatus.objects.filter(dispatch_category__isnull=True).update(dispatch_category="")

        dupes = (
            DispatchingStatus.objects
            .values(
                "employee",
                # "date",
                # "time",
                "dispatch_status",
                "dispatch_category",
                "positive_interaction",
                "ETA",
                "location",
                "notes",
            )
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for d in dupes:
            entries = DispatchingStatus.objects.filter(
                employee=d["employee"],
                # date=d["date"],
                # time=d["time"],
                dispatch_status=d["dispatch_status"],
                dispatch_category=d["dispatch_category"],
                positive_interaction=d["positive_interaction"],
                ETA=d["ETA"],
                location=d["location"],
                notes=d["notes"],
            ).order_by("id")  # или по updated_at, если нужно

            keep_one = entries.first()
            for e in entries:
                if e != keep_one:
                    print("deleting", e.id, e.employee.id, e.dispatch_status, e.dispatch_category, e.positive_interaction, e.ETA, e.location, e.notes, )
                    e.delete()
                else:
                    print("stay    ", e.id, e.employee.id, e.dispatch_status, e.dispatch_category, e.positive_interaction, e.ETA, e.location, e.notes, )

        # Interaction
        Interaction.objects.filter(notes__isnull=True).update(notes="")

        dupes = (
            Interaction.objects
            .values(
                "employee",
                "type_of_interaction",
                "date",
                "negative_interaction",
                "notes",
            )
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for d in dupes:
            entries = Interaction.objects.filter(
                employee=d["employee"],
                type_of_interaction=d["type_of_interaction"],
                date=d["date"],
                negative_interaction=d["negative_interaction"],
                notes=d["notes"],
            ).order_by("id")  # или по updated_at, если нужно

            keep_one = entries.first()
            for e in entries:
                if e != keep_one:
                    print("deleting", e.id, e.employee.id, e.type_of_interaction, e.date, e.negative_interaction, e.notes, )
                    e.delete()
                else:
                    print("stay    ", e.id, e.employee.id, e.type_of_interaction, e.date, e.negative_interaction, e.notes, )

        self.stdout.write(self.style.SUCCESS("End cleanTrashDuplicatesCommand."))
