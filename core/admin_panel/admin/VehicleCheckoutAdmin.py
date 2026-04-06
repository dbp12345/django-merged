from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django_admin_flexlist import FlexListAdmin
from dispatch.models.VehicleCheckout import VehicleCheckout
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(VehicleCheckout)
class VehicleCheckoutAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("license_plate",)
    autocomplete_fields = ("truck", "employee",)

    list_display_links = ("updated_at",)

    list_display = (
        # "__str__",
        "updated_at",
        "truck",
        "employee",
        "status",
        "milage",
        "license_plate",
        "picture_front_preview",
        "picture_passenger_side_preview",
        "picture_rear_preview",
        "picture_driver_side_preview",
        # "created_at",
    )
    list_editable = (
        "status",
        "milage",
        "license_plate",
    )
    ordering = ("-updated_at",)

    fields = (
        "truck",
        "employee",
        "status",
        "milage",
        "license_plate",
        ("picture_front", "picture_front_preview"),
        ("picture_passenger_side", "picture_passenger_side_preview"),
        ("picture_rear", "picture_rear_preview"),
        ("picture_driver_side", "picture_driver_side_preview"),
        ("created_at", "updated_at"),
    )
    readonly_fields = (
        "picture_front_preview",
        "picture_passenger_side_preview",
        "picture_rear_preview",
        "picture_driver_side_preview",
        "created_at",
        "updated_at",
    )

    list_filter = (
        ("employee", RelatedOnlyFieldListFilter),
        ("truck", RelatedOnlyFieldListFilter),
        "status",
    )

    class Media:
        css = {
            "all": (
                "custom_modal/custom_modal.css",
            )
        }
        js = (
            "custom_modal/custom_modal.js",
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        for name in ("truck",):
            f = form.base_fields.get(name)
            if not f:
                continue
            w = f.widget
            if isinstance(w, RelatedFieldWidgetWrapper):
                w.can_delete_related = False  # убираем опасный крестик удаления

        return form
