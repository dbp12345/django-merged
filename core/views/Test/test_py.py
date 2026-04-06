from django.db.models import Subquery, OuterRef
from django.http import JsonResponse
from django.views import View
from company.models import Employees_Parameters
from core.services.RecordsService import RecordsService
from core.services.SanitazerService import SanitazerService
from privser.models import Contacts as Custom_Fields
from exchange.services.ExchangeService import ExchangeService
from privser.services.PrivserAPI2Service import PrivserAPI2Service
from privser.services.PrivserService import PrivserService
from privser.services.PrivserUpdatesService import PrivserUpdatesService
from synchronization.models import Sync_Parameters
from privser.models.ContactsParameters import Contacts_Parameters as Contacts_Parameters_Privser


class TestView(View):

    def get(self, request):

        employee_id = 49634
        print(f"employee_id: {employee_id}")

        RecordsService.set_operational_periods_for_all_employees(employee_id=employee_id)

        return JsonResponse({"status": "test"})



        # username = "test_py"
        # employee_id = 49482
        #
        #
        # employee = Employees.objects.get(id=employee_id)
        # # employee.last_modified_time = datetime.now().astimezone()
        # employee.last_modified_name = username
        # employee.save()
        #
        # parameters_dict = {}
        # param_name = "tags"
        # param_value = (
        #     # "instagram applicant - no privser",
        #     # "maybe transfer",
        #     "test-33",
        #     "test-44",
        #     "test22-44",
        # )
        #
        # contacts_prop_obj = Contacts_Prop.objects.filter(property_name=param_name).first()
        # if contacts_prop_obj:
        #     parameters_dict[contacts_prop_obj] = param_value
        #
        #
        # EmployeesService.update_employee_parameters_raw(employee=employee, parameters=parameters_dict, modified_name=username)

        return JsonResponse({"status": "ok"})

        privser_api2_service = PrivserAPI2Service()


        contact_response = privser_api2_service.get_contacts_by_id("GQJaJQNCXOH63FqFJj7x")
        fields_arr = PrivserService.get_all_fields_from_contact_response(contact_response)

        import json
        formatted_result = json.dumps(fields_arr, indent=4, ensure_ascii=False)
        print(formatted_result)

        return JsonResponse({"status": "ok"})

        exit()

        # fire_runs = (
        #     FireRun.objects
        #     .filter(employee_id=employee_id)
        #     .select_related("crew", "crew__fire")
        #     .order_by("-start_date")[:10]
        # )
        #
        # fire_runs_list = []
        # for fr in fire_runs:
        #     fire_runs_list.append({
        #         "job_title": fr.job_title or "",
        #         "start_date": fr.start_date.strftime("%m/%d/%Y") if fr.start_date else "",
        #         "crew_fire_state": fr.crew.fire.state if fr.crew and fr.crew.fire else "",
        #         "operational_periods": fr.operational_periods or "",
        #         "crew_fire_incident_name": fr.crew.fire.incident_name if fr.crew and fr.crew.fire else "",
        #         "crew_crew_name": fr.crew.crew_name if fr.crew else "",
        #         "eval_hotline": fr.eval_hotline or "",
        #         "hotline_in_remarks": fr.hotline_in_remarks or "",
        #         "ranking": fr.ranking or "",
        #     })

        employees_qs = Employees.objects.annotate(
            last_s230_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="S-230"
                ).order_by("-training_class__date").values("training_class__date")[:1]
            ),
            last_s290_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="S-290"
                ).order_by("-training_class__date").values("training_class__date")[:1]
            ),
            last_s131_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="S-131"
                ).order_by("-training_class__date").values("training_class__date")[:1]
            ),
            last_is200_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="IS-200"
                ).order_by("-training_class__date").values("training_class__date")[:1]
            )
        ).get(pk=employee_id)

        students_list = []
        if employees_qs.last_s230_date:
            students_list.append(["S-230:", employees_qs.last_s230_date.strftime("%m/%d/%Y")])
        if employees_qs.last_s290_date:
            students_list.append(["S-290:", employees_qs.last_s290_date.strftime("%m/%d/%Y")])
        if employees_qs.last_s131_date:
            students_list.append(["S-131:", employees_qs.last_s131_date.strftime("%m/%d/%Y")])
        if employees_qs.last_is200_date:
            students_list.append(["IS-200:", employees_qs.last_is200_date.strftime("%m/%d/%Y")])

        return JsonResponse({"status": "ok", "data": {"students": students_list}})


        # employee_id = 24453
        #
        # fire_runs = (
        #     FireRun.objects
        #     .filter(employee_id=employee_id)
        #     .select_related("crew", "crew__fire")
        #     .order_by("-start_date")[:10]
        # )
        #
        # result = []
        # for fr in fire_runs:
        #     result.append({
        #         "job_title": fr.job_title or "",
        #         "start_date": fr.start_date.strftime("%Y-%m-%d") if fr.start_date else "",
        #         "crew_fire_state": fr.crew.fire.state if fr.crew and fr.crew.fire else "",
        #         "operational_periods": fr.operational_periods or "",
        #         "crew_fire_incident_name": fr.crew.fire.incident_name if fr.crew and fr.crew.fire else "",
        #         "crew_crew_name": fr.crew.crew_name if fr.crew else "",
        #         "eval_hotline": fr.eval_hotline or "",
        #         "hotline_in_remarks": fr.hotline_in_remarks or "",
        #         "ranking": fr.ranking or "",
        #     })
        # return JsonResponse({"status": "ok", "data": result})




        # from core.tasks import generate_entities_from_contact_params_task
        # if settings.DEBUG:
        #     generate_entities_from_contact_params_task.run(employee_id=49482)
        # else:
        #     generate_entities_from_contact_params_task.delay(employee_id=49482)

        return JsonResponse("rrrrr", safe=False)
        # check_possibility_firecrew_task.run(49482)
        exit()


        # aaa = Contacts_Prop.objects.filter(property_name__icontains="Manifest Date").values("id", "property_name", "property_type", "datetime_format")
        bbb = Employees_Parameters.objects.filter(
            employee_id=49482
        ).filter(
            contacts_prop__property_name__icontains="Manifest Date"
        ).select_related("contacts_prop").values(
            "id", "contacts_prop__id", "contacts_prop__property_name", "value", "value_date"
        )
        print("bbb: ", bbb)
        exit()





        contact_email = "test10@automation.com"
        privser_api2_service = PrivserAPI2Service()
        # contact_response = privser_api2_service.get_contacts_by_email(contact_email)
        # contact_id = contact_response.get("id")
        contact_id = "olV8ESTkIxjTCdPD9peS"

        response = PrivserAPI2Service().get_contacts_by_id(contact_id=contact_id)

        fields_arr = PrivserService.get_all_fields_from_contact_response(response)
        PrivserUpdatesService.save_or_update_contacts_photos_from_arr(fields_arr, False)

        # data = PrivserUpdatesService.update_all_fields_from_contact_id(contact_id)

        # print(fields_arr)
        return JsonResponse(fields_arr, safe=False)

        # employee = Employees.objects.get(id=29656)

        from core.services.ChangedParametersService import ChangedParametersService
        ChangedParametersService.send_grouped_changes()
        return JsonResponse({"sssss": "ok"})

        from core.tasks.check_and_send_employee_to_paychex import check_and_send_employee_to_paychex
        check_and_send_employee_to_paychex(29656)
        return JsonResponse({"sssss": "ok"})

        # privser_api2_service = PrivserAPI2Service()
        # contact_priv = privser_api2_service.get_contacts_by_id(contact_id="olV8ESTkIxjTCdPD9peS")
        #
        # return JsonResponse(contact_priv, safe=False)

        # print(contact_priv)
        # exit()

        contact_exc = ExchangeService.find_user_by_email(contact_exc_email="test10@automation.com")
        attachments = contact_exc.attachments
        for attachment in attachments:
            if getattr(attachment, "is_contact_photo", False):
                print(attachment.last_modified_time)
                # content = attachment.content
                # filename = attachment.name or "contact_photo.jpg"
                # employee.document.save(filename, ContentFile(content), save=False)
                # employee.save()
                break

        """
        Contact(
            mime_content=b'BEGIN:VCARD\r\nPROFILE:VCARD\r\nVERSION:3.0\r\nMAILER:Microsoft Exchange\r\nPRODID:Microsoft Exchange\r\nFN:Test10 Test-112 Test-11\r\nN:Test-11;Test10;Test-112;;\r\nPHOTO;TYPE=JPEG;ENCODING=B:/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAICAgICAQICAgID\r\n AgIDAwYEAwMDAwcFBQQGCAcJCAgHCAgJCg0LCQoMCggICw8LDA0ODg8OCQsQERAOEQ0ODg7/2w\r\n BDAQIDAwMDAwcEBAcOCQgJDg4ODg4ODg4ODg4ODg4ODg4ODg4ODg4ODg4ODg4ODg4ODg4ODg4O\r\n Dg4ODg4ODg4ODg7/wAARCADhAOEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAw\r\n QFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0Kx\r\n wRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3\r\n R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW\r\n 19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQ\r\n oL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAV\r\n YnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eH\r\n l6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna\r\n 4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKACiiigAooooAKKzrq6t7Swa5u\r\n Zo7e3jHMspGBXxH8V/21PBvhA3Ok+ALc+NtfHW6/1emw/8D/5a/wDAP++68zG5hg8vpOpiZqK/\r\n H5Lc8TMs3y7KKPtcZVUF+L9Fuz7imuIIE82aVFGOpOK+bPHf7VXwb8ELdW9x4jHiDVYRzp+hj7\r\n TJ/wB98Iv/AH3X5Q/EH42fEv4n3v8AxVviS7/sv/oD2B+z2P8A3wv3/wDge+sDwZ8MvHfj/Uvs\r\n /gvwlqGvjP8Ax8W9v5dt/wADmf5Er8vxXGlevU9jltG76N6t+iX+Z+GY/wAR8Vi6zw+TYfmb2c\r\n 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\r\nEMAIL;TYPE=INTERNET:test10@automation.com\r\nNOTE:Qwert33333\\n\\n\r\nORG:;\r\nCLASS:PUBLIC\r\nADR;TYPE=WORK:;;;;;;\r\nADR;TYPE=HOME:;;;;;;\r\nADR;TYPE=POSTAL:;;;;;;\r\nTEL;TYPE=WORK:+1 (111) 222-7777\r\nTEL;TYPE=HOME:+1 (765) 571-1236\r\nTEL;TYPE=CELL:+17655711277\r\nTITLE:CRWB-test\r\nX-MS-IMADDRESS:\r\nCATEGORIES:Red Category\r\nREV;VALUE=DATE-TIME:2025-04-21T20:12:03,121Z\r\nEND:VCARD\r\n',
            _id=ItemId(
                id='AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAWiKldZAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=',
                changekey='EQAAABYAAADy7w6A6MWMTKhQqDM7ARKlAAY6cLhn'),
            parent_folder_id=ParentFolderId(id='AQEuAAADGkRzkKpmEc2byACqAC/EWgMA8u8OgOjFjEyoUKgzOwESpQAAAcbmQwAAAA==', changekey='AQAAAA=='),
            item_class='IPM.Contact.AllFields', subject='Test10 Test-112 Test-11', sensitivity='Normal', text_body='Qwert33333\r\n\r\n',
            body='<html>\r\n<head>\r\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\r\n<meta name="Generator" content="Microsoft Exchange Server">\r\n<!-- converted from rtf -->\r\n<style><!-- .EmailQuote { margin-left: 1pt; padding-left: 4pt; border-left: #800000 2px solid; } --></style>\r\n</head>\r\n<body>\r\n<font face="Times New Roman" size="3"><span style="font-size:12pt;"><a name="BM_BEGIN"></a>\r\n<div><font face="Courier New" size="3"><span style="font-size:12pt;">Qwert33333</span></font></div>\r\n<div><font face="Calibri" size="3"><span style="font-size:12pt;">&nbsp;</span></font></div>\r\n</span></font>\r\n</body>\r\n</html>\r\n',
            attachments=[FileAttachment(attachment_id=AttachmentId(
                id='AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAWiKldZAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAABEgAQABgmywBeF/lPvyRwiswuZWw=',
                root_id=None, root_changekey=None), name='ContactPicture.jpg', content_type='image/jpeg', content_id=None, content_location=None, size=20287,
                last_modified_time=EWSDateTime(2025, 4, 21, 13, 12, 2, tzinfo=EWSTimeZone(key='America/Los_Angeles')), is_inline=False,
                is_contact_photo=True)], datetime_received=EWSDateTime(2024, 7, 3, 4, 24, 49, tzinfo=EWSTimeZone(key='UTC')),
            size=34097, categories=['Red Category'], importance='Normal', is_submitted=False, is_draft=False, is_from_me=False, is_resend=False,
            is_unmodified=False, datetime_sent=EWSDateTime(2024, 7, 3, 4, 24, 49, tzinfo=EWSTimeZone(key='UTC')),
            datetime_created=EWSDateTime(2024, 7, 3, 4, 21, 5, tzinfo=EWSTimeZone(key='UTC')), reminder_is_set=False, reminder_minutes_before_start=0,
            has_attachments=True, culture='en-US',
            effective_rights=EffectiveRights(create_associated=False, create_contents=False, create_hierarchy=False, delete=False, modify=True, read=True,
                                             view_private_items=False), last_modified_name='Exchange Sync',
            last_modified_time=EWSDateTime(2025, 4, 21, 20, 12, 3, tzinfo=EWSTimeZone(key='UTC')), is_associated=False,
            web_client_read_form_query_string='https://mail.privser.com/owa?ItemID=AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAWiKldZAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA%3D&exvsurl=1&viewmodel=ReadMessageItem',
            conversation_id=ConversationId(id='AAQkAGNiZTMxOWU0LWNlMGMtNDk0Yy04N2ExLWMyMTM3YzAyNDdiZAAQAKryXIZU3kbgqK1Ur5/mtfc=', changekey=None),
            file_as='Test-11, Test10 Test-112', file_as_mapping='LastCommaFirst', display_name='Test10 Test-112 Test-11', given_name='Test10',
            initials='T.T.T.', middle_name='Test-112',
            complete_name=CompleteName(title=None, first_name='Test10', middle_name='Test-112', last_name='Test-11', suffix=None, initials='T.T.T.',
                                       full_name='Test10 Test-112 Test-11', nickname=None, yomi_first_name=None, yomi_last_name=None),
            email_addresses=[EmailAddress(label='EmailAddress1', email='test10@automation.com')],
            phone_numbers=[PhoneNumber(label='BusinessPhone', phone_number='+1 (111) 222-7777'),
                           PhoneNumber(label='HomePhone', phone_number='+1 (765) 571-1236'), PhoneNumber(label='MobilePhone', phone_number='+17655711277')],
            im_addresses=[ImAddress(label='ImAddress1', im_address=None)], job_title='CRWB-test', postal_address_index='None', surname='Test-11',
            has_picture=True)
        """
        return JsonResponse({"sssss": contact_exc})

        # value = "2034-05-01"
        # value = SanitazerService.datetime_str_to_datetime(value)
        # print("value", value)
        # print("type", type(value))
        # logger = logging.getLogger("my_log")
        # logger.error(
        #     "\n================ ERROR ================\n"
        #     f"User_email    : {value}\n"
        #     f"model_field   : {value}\n"
        #     f"value         : {value}\n"
        #     f"type          : {type(value)}\n"
        # )

        email = "test10@automation.com"
        contact = ExchangeService.find_user_by_email(contact_exc_email=email)
        print(contact.email_addresses)
        print(contact.phone_numbers)
        mobile_phone = next((p.phone_number for p in contact.phone_numbers if p.label == "MobilePhone"), None)

        exit()
        # Дата, после которой нужны контакты
        date_after = datetime(2025, 1, 30)
        timestamp_after = int(date_after.timestamp() * 1000)

        # query = {
        #     'dateUpdated_gt': timestamp_after
        # }

        privser_api2_service = PrivserAPI2Service()

        # query = {
        #     "filters": [
        #         {
        #             "field": "email",
        #             "operator": "eq",
        #             "value": "test10@automation.com"
        #         }
        #     ]
        # }

        query = {
            "filters": [
                {
                    "field": "dateUpdated",
                    "operator": "range",
                    "value": {
                        "gt": "2025-01-25T00:00:00.000Z",
                        # "lt": "2025-02-21T00:00:00.000Z"
                    }
                }
            ]
        }

        print(json.dumps(query))
        print(json.loads(json.dumps(query)))
        exit()

        result = privser_api2_service.search_contacts(query=query, page_limit=100)

        # formatted_result = json.dumps(result, indent=4, ensure_ascii=False)
        # print(formatted_result)
        return JsonResponse(result)
        exit()

        exit()

        # privser_service = PrivserService()
        # privser_api2_service = PrivserAPI2Service()
        #
        # response = privser_api2_service.get_contacts_by_id("Mx2pvABKW3VLDb6Lx47W")
        #
        # fields_arr = PrivserService.get_all_fields_from_contact_response(response)
        #
        # response = privser_api2_service.get_all_notes("Mx2pvABKW3VLDb6Lx47W")
        # note_text = privser_service.all_notes_to_str_from_res(response)
        # fields_arr["Notes"] = note_text
        #
        # res = PrivserUpdatesService.save_or_update_contacts_from_arr(fields_arr, True)
        #
        # print(res)
        # return JsonResponse({"sssss": fields_arr})

        sync_parameters_obj = Sync_Parameters.objects.get(id=1385)
        print(type(sync_parameters_obj.exchange_value), sync_parameters_obj.exchange_value)
        print(type(sync_parameters_obj.privser_value), sync_parameters_obj.privser_value)
        if sync_parameters_obj.exchange_value == sync_parameters_obj.privser_value:
            print(type(sync_parameters_obj.exchange_value), sync_parameters_obj.exchange_value)
            print(type(sync_parameters_obj.privser_value), sync_parameters_obj.privser_value)
            sync_parameters_obj.delete()

        return JsonResponse({"sssss": "dfsdsfsd"})

        key = "Ranking 1 to 10"
        email = "test10@automation.com"
        custom_fields_obj = Custom_Fields.objects.filter(exchange_property__property_name=key)
        custom_fields_obj_first = custom_fields_obj.first()

        print(custom_fields_obj_first)

        contacts_parameters_privser_obj = Contacts_Parameters_Privser.objects.get(
            contacts__email=email,
            name__in=[custom_fields_obj_first.privser_name, custom_fields_obj_first.privser_id],
        )
        privser_value_from_db = contacts_parameters_privser_obj.value

        print(privser_value_from_db)

        return JsonResponse({"sssss": "ok"})


        # c = Contacts.objects.get(id=22024)
        # print(c.updated_at)
        # print(localtime(c.updated_at))
        # print(is_aware(c.updated_at))
        # return JsonResponse({"sssss": "ok"})

        folder = ExchangeService.get_exchange_folder()

        contact = folder.get(email_addresses="Test10@Automation.com")

        str_from_last_modified_time_ewsdatetime = contact.last_modified_time  # 2024-12-30 01:42:01+00:00
        # print(type(str_from_last_modified_time_ewsdatetime.astimezone()), str_from_last_modified_time_ewsdatetime.astimezone())

        # last_modified_time_datetime = SanitazerService.format_ewsdatetime_or_str_to_str(str_from_last_modified_time_ewsdatetime) # 2024-12-29 17:42:01
        # last_modified_time_datetime = SanitazerService.datetime_str_to_datetime(last_modified_time_datetime) #2024-12-29 17:42:01-08:00

        # last_modified_time_datetime = SanitazerService.(str_from_last_modified_time_ewsdatetime) #2024-12-29 17:42:01-08:00

        last_modified_time_datetime = SanitazerService.format_ewsdatetime_to_str(str_from_last_modified_time_ewsdatetime)  # 2024-12-29 17:42:01
        print(type(last_modified_time_datetime), last_modified_time_datetime)

        return JsonResponse({"sssss": "ok"})

        str_from_last_modified_time_EWSDateTime = contact.last_modified_time
        print(type(str_from_last_modified_time_EWSDateTime), str_from_last_modified_time_EWSDateTime)
        # last_modified_time_datetime = datetime.strptime(str_from_last_modified_time_EWSDateTime, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)

        last_modified_time_datetime_qqq = SanitazerService.format_ewsdatetime_or_str_to_str(str_from_last_modified_time_EWSDateTime)

        print(type(str_from_last_modified_time_EWSDateTime), str_from_last_modified_time_EWSDateTime)
        print(type(last_modified_time_datetime_qqq), last_modified_time_datetime_qqq)

        return JsonResponse({"sssss": "ok"})
