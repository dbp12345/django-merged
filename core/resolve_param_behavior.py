from django.contrib.admin.widgets import AdminDateWidget, AdminFileWidget
from django import forms

from exchange.models import Contacts_Prop
from company.models.Employees import AVAILABILITY_STATUS, INTERACTION_STATUS, DispatchStatus, MEDICAL_CARD_TYPE


CHOICE_FIELDS = {
    "Availability status": AVAILABILITY_STATUS,
    "Dispatch Call Status": [(status.label, status.label) for status in DispatchStatus],
    "Type of interaction": INTERACTION_STATUS,
    "Medical Card Type": MEDICAL_CARD_TYPE,
}

# FORCE_DATE_FIELDS = [
#     "ETA, Late, Dispatch",
#     "Driver's License Issue Date",
#     "Driver's License Expiration Date",
# ]


def resolve_param_behavior(prop, instance=None):
    prop_type = prop.property_type
    name = prop.property_name
    fmt = prop.datetime_format or "%m/%d/%Y"

    value = ""
    widget = None

    if prop_type == Contacts_Prop.TypeChoices.BOOL:
        value = getattr(instance, "value_bool", False) if instance else False
        widget = forms.CheckboxInput()

    elif prop_type == Contacts_Prop.TypeChoices.SYSTEM_TIME:  # or name in FORCE_DATE_FIELDS:
        value_date = getattr(instance, "value_date", None)
        value = value_date.strftime(fmt) if value_date else ""
        widget = AdminDateWidget(format=fmt)

    elif prop_type == Contacts_Prop.TypeChoices.DOCUMENT:
        value_file = getattr(instance, "value_file", None)
        value = value_file if value_file else None
        widget = AdminFileWidget()

    elif name in CHOICE_FIELDS:
        value = getattr(instance, "value", "")
        widget = forms.Select(choices=CHOICE_FIELDS[name])

    else:
        value = getattr(instance, "value", "")

    return {
        "name": name,
        "id": prop.id,
        "type": prop_type,
        "value": value,
        "widget_html": widget.render(str(prop.id), None, {"id": str(prop.id)}) if widget else "",
        "is_checkbox": isinstance(widget, forms.CheckboxInput),
        "is_file": isinstance(widget, AdminFileWidget),
        "is_date": isinstance(widget, AdminDateWidget),
        "choices": CHOICE_FIELDS.get(name),
    }
