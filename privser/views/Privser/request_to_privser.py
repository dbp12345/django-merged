from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseRedirect

from privser.models import Contacts, Contacts_Parameters
from privser.services.PrivserAPI2Service import PrivserAPI2Service
from privser.services.PrivserUpdatesService import PrivserUpdatesService


# @staff_member_required
# def request_to_privser(request, request_to_privser_id):
#     if not request.user.is_authenticated:
#         return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)
#
#     privser_service = PrivserService()
#
#     request_to_privser_db = Request_To_Privser.objects.get(
#         id=request_to_privser_id
#     )
#
#     # privser_service.create_request_to_privser_from_contact(contact)
#     privser_service.handle_request_to_privser(request_to_privser_db)
#
#
#     referer = request.META.get('HTTP_REFERER', '/admin/privser/request_to_privser/')
#     return HttpResponseRedirect(referer)


@staff_member_required
def update_contact_from_privser_by_id(request, obj_id):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    priv_cont = Contacts.objects.get(id=obj_id)
    Contacts_Parameters.objects.filter(contacts=priv_cont).delete()

    email = Contacts.objects.get(id=obj_id).email
    print("email: ", email)
    cont = PrivserAPI2Service().get_contacts_by_email(email=email)["contact"][0]
    priv_cont.delete()

    contact_id = cont.get("id")

    print("cont: ", contact_id)

    PrivserUpdatesService.update_all_fields_from_contact_id(contact_id=contact_id, ignore_diff_properties=False)

    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer)

@staff_member_required
def update_contact_from_privser_by_email(request, obj_email):
    # priv_cont = Contacts.objects.get(email=obj_email)
    # email = priv_cont.email
    # print("email: ", email)
    cont = PrivserAPI2Service().get_contacts_by_email(email=obj_email)["contact"][0]

    # print(cont)

    contact_id = cont.get("id")

    # print("cont: ", contact_id)

    PrivserUpdatesService.update_all_fields_from_contact_id(contact_id=contact_id, ignore_diff_properties=False)

    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer)
