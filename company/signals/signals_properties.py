# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from company.models import MSPA, IdentificationDocuments, DispatchingStatus, Employees_Parameters
#
#
# @receiver(post_save, sender=MSPA)
# def update_mspa_params(sender, instance, **kwargs):
#     Employees_Parameters.objects.update_or_create(
#         employee=instance.contact,
#         employees_parameters='MSPA_number',  # предполагается, что это поле как-то определено
#         defaults={
#             'value': instance.MSPA_number,
#             'modified_by': instance.modified_by,
#             'sync_updated_at': instance.updated_at
#         }
#     )
#
#
# # Повторите для других моделей
# @receiver(post_save, sender=IdentificationDocuments)
# def update_identification_params(sender, instance, **kwargs):
#     # добавьте здесь логику обновления
#     pass
#
#
# @receiver(post_save, sender=DispatchingStatus)
# def update_dispatching_status_params(sender, instance, **kwargs):
#     # добавьте здесь логику обновления
#     pass
