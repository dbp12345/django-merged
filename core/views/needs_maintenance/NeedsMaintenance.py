from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.admin.utils import quote
from django.urls import reverse
from django.views import View
from dispatch.models import Equipment
from dispatch.models.Dispatch import Saw, Radio, Phone, Truck
from core.models.HelpTicket import HelpTicket
from core.models.Task import Category


def get_equipment_children_ids():
    """Get IDs of Equipment category children."""
    try:
        equipment_category = Category.objects.get(name="Equipment")
        equipment_children = equipment_category.get_children()
        return list(equipment_children.values_list("id", flat=True))
    except Category.DoesNotExist:
        return []


def get_equipment_objects_with_help_tickets(model_class, field_name):
    """
    Get objects that have Help Tickets with Equipment child categories (excluding completed).

    Args:
        model_class: The model class (Truck, Saw, Radio, Phone)
        field_name: The field name in HelpTicket model (truck, saw, radio, phone)
    """
    equipment_children_ids = get_equipment_children_ids()
    if not equipment_children_ids:
        return model_class.objects.none()

    # Get Help Tickets with Equipment child categories (excluding completed)
    help_tickets = HelpTicket.objects.filter(
        **{field_name + "__isnull": False},
        category_id__in=equipment_children_ids
    ).exclude(status="completed")

    # Get unique object IDs from help tickets
    object_ids = help_tickets.values_list(field_name, flat=True).distinct()

    # Return objects ordered by updated_at
    return model_class.objects.filter(pk__in=object_ids).order_by("-updated_at")


def get_categories_for_object(obj, field_name):
    """Get unique categories from Help Tickets for an object."""
    equipment_children_ids = get_equipment_children_ids()
    if not equipment_children_ids:
        return []

    filter_kwargs = {
        field_name: obj,
        "category_id__in": equipment_children_ids
    }
    help_tickets = HelpTicket.objects.filter(**filter_kwargs).exclude(status="completed").select_related("category")

    categories = set()
    for ticket in help_tickets:
        if ticket.category:
            categories.add(ticket.category)

    return sorted(categories, key=lambda x: x.name)


@method_decorator(staff_member_required, name="dispatch")
class NeedsMaintenanceView(View):
    template_name = "admin/needs_maintenance/needs_maintenance.html"

    def get(self, request, *args, **kwargs):
        title = "Action Required"

        truck_qs = get_equipment_objects_with_help_tickets(Truck, "truck")
        saw_qs = get_equipment_objects_with_help_tickets(Saw, "saw")
        radio_qs = get_equipment_objects_with_help_tickets(Radio, "radio")
        phone_qs = get_equipment_objects_with_help_tickets(Phone, "phone")
        equipment_qs = get_equipment_objects_with_help_tickets(Equipment, "equipment")

        def admin_change_url(obj):
            opts = obj._meta
            return reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[quote(obj.pk)])

        def prepare_items(qs, field_name):
            """Prepare items with object, URL, and categories."""
            return [
                (obj, admin_change_url(obj), get_categories_for_object(obj, field_name))
                for obj in qs
            ]

        context = {
            "title": title,
            "truck_items": prepare_items(truck_qs, "truck"),
            "saw_items": prepare_items(saw_qs, "saw"),
            "radio_items": prepare_items(radio_qs, "radio"),
            "phone_items": prepare_items(phone_qs, "phone"),
            "equipment_items": prepare_items(equipment_qs, "equipment"),
        }
        return render(request, self.template_name, context)
