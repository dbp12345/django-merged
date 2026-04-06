from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from privser.services.PrivserService import PrivserService


# @staff_member_required
# def set_all_identified_fields_to_exchange(request):
#     taf_service = TestAllFieldsService()
#     response_data = taf_service.set_all_identified_fields_to_exchange()
#
#     return JsonResponse(response_data)

# @staff_member_required
# def create_test_request_to_exchange(request):
#     taf_service = TestAllFieldsService()
#     response_data = taf_service.test_exchange()
#
#     return JsonResponse(response_data)

# @staff_member_required
# def create_test_request_to_privser(request):
#     taf_service = TestAllFieldsService()
#     response_data = taf_service.test_privser()
#
#     return JsonResponse(response_data)

@staff_member_required
def update_fields_from_privser(request):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    privser_service = PrivserService()

    privser_service.update_custom_fields_in_db()

    url = reverse('admin:privser_custom_fields_changelist')
    return redirect(url)