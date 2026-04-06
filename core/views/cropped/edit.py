from django.views import View
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect

from company.models import Employees_Pictures, Employees
from privser.services.PrivserAPI2Service import PrivserAPI2Service
from privser.models import Contacts as ContactsPrivser


class CroppedEditView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        pictures_id = request.GET.get("id")

        employees_pictures = Employees_Pictures.objects.get(id=pictures_id)
        photo = None
        if employees_pictures and employees_pictures.photo_privser_picture_at_field_training and not employees_pictures.photo_privser_cropped_picture_for_red_card:
            photo = employees_pictures.photo_privser_picture_at_field_training

        title = "Add cropped_picture_for_red_card"
        return render(
            request,
            "cropped/edit.html",
            context={
                "title": title,
                "pictures": photo,
            }
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        pictures_id = request.POST.get("id")
        cropped_image = request.FILES.get("cropped_image")

        if not (pictures_id and cropped_image):
            return HttpResponse(status=400)

        image_file, relative_path = convert_imagefield_to_jpg(cropped_image)

        obj = Employees_Pictures.objects.get(id=pictures_id)
        obj.photo_privser_cropped_picture_for_red_card.save(relative_path, image_file, save=True)
        obj.save()

        email = obj.employee.email
        contact_privser_obj = ContactsPrivser.objects.get(email=email)

        privser_api2_service = PrivserAPI2Service()
        privser_api2_service.upload_custom_field_file(
            contact_id=contact_privser_obj.contact_id,
            field_id="G0MIEOY6M6QiManeaWw7",
            file_field=obj.photo_privser_cropped_picture_for_red_card
        )
        return redirect("admin:%s_%s_change" % (Employees._meta.app_label, Employees._meta.model_name), obj.employee.id)

def convert_imagefield_to_jpg(image_field):
    from PIL import Image
    import uuid
    from django.core.files.base import ContentFile
    from io import BytesIO

    if not image_field:
        return None

    img = Image.open(image_field)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    filename = f"cropped_{uuid.uuid4().hex}.jpg"
    relative_path = filename

    return ContentFile(buffer.read()), relative_path