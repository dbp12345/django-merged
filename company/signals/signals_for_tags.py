# from django.db.models.signals import m2m_changed, post_save, post_delete
# from django.dispatch import receiver
# from typing import Any
# #
# # from django.db import transaction
# #
# from company.models import Employees
#
#
# from django.db import transaction
# from django.db.models.signals import post_save, post_delete
#
# Through = Employees.tags.through
#
#
# def _get_employee_pk_from_through(instance) -> int | None:
#     # Находим FK-поле, которое ссылается на Employees и читаем attname (employee_id)
#     for field in instance._meta.fields:
#         rel = getattr(field, "remote_field", None)
#         if rel and rel.model is Employees:
#             return getattr(instance, field.attname)
#     # fallback: check attrs
#     for name in ("employee_id", "employees_id", "employee"):
#         if hasattr(instance, name):
#             val = getattr(instance, name)
#             if isinstance(val, int):
#                 return val
#     return None
#
#
# @receiver(post_save, sender=Through)
# @receiver(post_delete, sender=Through)
# def _through_changed(sender, instance, **kwargs: Any):
#     print("44444444444")
#     emp_pk = _get_employee_pk_from_through(instance)
#     if not emp_pk:
#         return
#
#     conn = transaction.get_connection()
#     if not hasattr(conn, "_tags_changed_pks"):
#         conn._tags_changed_pks = set()
#     conn._tags_changed_pks.add(emp_pk)
#
#     if not getattr(conn, "_tags_on_commit_registered", False):
#         def _on_commit():
#             pks = getattr(conn, "_tags_changed_pks", set()).copy()
#             conn._tags_changed_pks.clear()
#             if hasattr(conn, "_tags_on_commit_registered"):
#                 delattr(conn, "_tags_on_commit_registered")
#
#             for pk in pks:
#                 try:
#                     emp = Employees.objects.get(pk=pk)
#                 except Employees.DoesNotExist:
#                     continue
#                 # здесь вместо print — вызов процесса
#                 print("3333333333333333", emp.pk)
#
#         transaction.on_commit(_on_commit)
#         conn._tags_on_commit_registered = True
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# # assuming Employees is imported
# # sender for m2m_changed — through model
# M2M_SENDER = Employees.tags.through
#
# @receiver(m2m_changed, sender=M2M_SENDER)
# def employee_tags_changed(sender, instance: Employees, action: str, pk_set: set | None, **kwargs: Any):
#     """
#     React to changes in employee.tags.
#     action in: pre_add, post_add, pre_remove, post_remove, pre_clear, post_clear
#     We act on post_* actions.
#     """
#     print("111111111111111111111111111111")
#     if action not in ("post_add", "post_remove", "post_clear"):
#         return
#     # pk_set — set of tag PKs added/removed (None for clear)
#     # instance — employee instance
#     # здесь дергаем процессинг тегов для сотрудника
#     # ___
#     # contacts_prop_obj = Contacts_Prop.objects.filter(property_name=param_name).first()
#     # if contacts_prop_obj:
#     #     parameters_dict[contacts_prop_obj] = param_value
#     #
#     # EmployeesService.update_employee_parameters_raw(employee=employee, parameters=parameters_dict, modified_name=username)
#
#
# # Если кто-то может манипулировать через модель напрямую — слушаем её:
# ThroughModel = Employees.tags.through
#
# @receiver(post_save, sender=ThroughModel)
# @receiver(post_delete, sender=ThroughModel)
# def through_model_changed(sender, instance, **kwargs):
#     print("22222222222222222222222222222")
#     # instance содержит объект through; нужно получить employee
#     employee = getattr(instance, "employees", None) or getattr(instance, "employee", None)
#     # Предположение: имя FK может быть "employee" или "employees" — проверь.
#     if employee:
#         print("22222222222222222222222222222")
#         # process_all_tags_for_employee(employee)
