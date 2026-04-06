# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
# from attendance.models import Punch_Event
# from exchange.models import Contacts_Prop
#
#
# from synchronization.services.SyncDeliveryService import SyncDeliveryService
#
#
# @receiver(post_save, sender=Punch_Event)
# def sync_student_relations(sender, instance, **kwargs):
#     if instance.employee:
#         property_name = "Employee Working Status"
#
#         contacts_prop_instance = Contacts_Prop.objects.get(property_name=property_name)
#         val = instance.event_type
#         SyncDeliveryService.do_sync_parameters(instance.employee, contacts_prop_instance, value=val, modified_by="sync_student_relations")
