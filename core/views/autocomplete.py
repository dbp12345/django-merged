from dal import autocomplete
from django.db.models import Q, Count

from company.models import Tag, Crew
from dispatch.models.Dispatch import *
from dispatch.models.Equipment import Equipment


class PhoneAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Phone.objects.none()

        qs = Phone.objects.filter(equipment_group__isnull=True)

        instance_id = self.forwarded.get("instance_id")
        if instance_id:
            qs = qs | Phone.objects.filter(equipment_group_id=instance_id)

        if self.q:
            qs = qs.filter(
                Q(make__icontains=self.q) |
                Q(name__icontains=self.q) |
                Q(model__icontains=self.q) |
                Q(number__icontains=self.q) |
                Q(os__icontains=self.q) |
                Q(serial_number__icontains=self.q) |
                Q(condition__icontains=self.q) |
                Q(status__icontains=self.q)
            )

        return qs.distinct()


class RadioAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Radio.objects.none()

        qs = Radio.objects.filter(equipment_group__isnull=True)

        instance_id = self.forwarded.get("instance_id")
        if instance_id:
            qs = qs | Radio.objects.filter(equipment_group_id=instance_id)

        if self.q:
            qs = qs.filter(
                Q(make__icontains=self.q) |
                Q(model__icontains=self.q) |
                Q(serial_number__icontains=self.q) |
                Q(condition__icontains=self.q) |
                Q(status__icontains=self.q)
            )

        return qs.distinct()


class SawAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Saw.objects.none()

        qs = Saw.objects.filter(equipment_group__isnull=True)

        instance_id = self.forwarded.get("instance_id")
        if instance_id:
            qs = qs | Saw.objects.filter(equipment_group_id=instance_id)

        if self.q:
            qs = qs.filter(
                Q(make__icontains=self.q) |
                Q(model__icontains=self.q) |
                Q(serial_number__icontains=self.q) |
                Q(condition__icontains=self.q) |
                Q(status__icontains=self.q)
            )

        return qs.distinct()


class TruckAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Truck.objects.none()

        qs = Truck.objects.filter(equipment_group__isnull=True)

        instance_id = self.forwarded.get("instance_id")
        if instance_id:
            qs = qs | Truck.objects.filter(equipment_group_id=instance_id)

        if self.q:
            qs = qs.filter(
                Q(key__icontains=self.q) |
                Q(make__icontains=self.q) |
                Q(model__icontains=self.q) |
                Q(license_plate__icontains=self.q) |
                Q(year__icontains=self.q) |
                Q(vin_number__icontains=self.q) |
                Q(serial_number__icontains=self.q) |
                Q(color__icontains=self.q) |
                Q(fuel_type__icontains=self.q) |
                Q(registration_state__icontains=self.q) |
                Q(status__icontains=self.q)
            )

        return qs.distinct()


class NomexAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Nomex.objects.none()

        qs = Nomex.objects.filter(equipment_group__isnull=True)

        instance_id = self.forwarded.get("instance_id")
        if instance_id:
            qs = qs | Nomex.objects.filter(equipment_group_id=instance_id)

        if self.q:
            qs = qs.filter(
                Q(type__icontains=self.q) |
                Q(size__icontains=self.q) |
                Q(serial_number__icontains=self.q) |
                Q(condition__icontains=self.q) |
                Q(status__icontains=self.q)
            )

        return qs.distinct()


class TagAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Tag.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class CrewAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Crew.objects.none()

        qs = Crew.objects.filter(dispatch__isnull=True)

        instance_id = self.forwarded.get("instance_id")
        if instance_id:
            qs = qs | Crew.objects.filter(dispatch_id=instance_id)

        q = self.q
        if q:
            qs = qs.filter(
                Q(crew_name__icontains=q) |
                Q(fire__incident_name__icontains=q) |
                Q(c_number__icontains=q) |
                Q(fire__fire_number__icontains=q)
            )

        return qs.distinct().order_by("crew_name")


class EquipmentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Equipment.objects.none()

        # Equipment uses ManyToMany, so filter for items with no equipment_group
        qs = Equipment.objects.annotate(
            eg_count=Count('equipment_group')
        ).filter(eg_count=0)

        instance_id = self.forwarded.get("instance_id")
        if instance_id:
            # Include Equipment that already belongs to this instance
            from dispatch.models.Dispatch import Equipment_group
            try:
                instance = Equipment_group.objects.get(pk=instance_id)
                qs = qs | instance.equipment_entries.all()
            except Equipment_group.DoesNotExist:
                pass

        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(serial_number__icontains=self.q) |
                Q(equipment_type__name__icontains=self.q) |
                Q(make__icontains=self.q) |
                Q(model__icontains=self.q) |
                Q(license_plate__icontains=self.q) |
                Q(vin_number__icontains=self.q) |
                Q(condition__icontains=self.q) |
                Q(status__icontains=self.q)
            )

        return qs.distinct()


class EquipmentGroupAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Equipment_group.objects.none()

        qs = Equipment_group.objects.all()

        instance_id = self.forwarded.get("instance_id")
        if instance_id:
            # Include the current instance if editing
            try:
                current_instance = Equipment_group.objects.get(pk=instance_id)
                # Already included in all()
            except Equipment_group.DoesNotExist:
                pass

        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(status__icontains=self.q)
            )

        return qs.distinct().order_by("name")
