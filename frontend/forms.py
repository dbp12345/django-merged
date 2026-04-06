from django import forms

from dispatch.models.VehicleCheckout import VehicleCheckout


class VehicleCheckoutForm(forms.ModelForm):
    class Meta:
        model = VehicleCheckout
        fields = [
            "truck",
            "status",
            "license_plate",
            "picture_front",
            "picture_passenger_side",
            "picture_rear",
            "picture_driver_side",
        ]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "truck": forms.Select(attrs={"class": "form-control"}),
            "license_plate": forms.TextInput(attrs={"class": "form-control"}),

            "picture_front": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "capture": "environment",
            }),
            "picture_passenger_side": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "capture": "environment",
            }),
            "picture_rear": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "capture": "environment",
            }),
            "picture_driver_side": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "capture": "environment",
            }),
        }
