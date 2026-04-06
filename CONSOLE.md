DESCRIBE company_employees;

UPDATE privser_contacts SET changed_properties = '{}' WHERE true;

SELECT test, COUNT(*) AS value_count FROM company_employees GROUP BY test;
SELECT test, COUNT(*) AS value_count FROM privser_contacts GROUP BY test;


UPDATE company_employees_parameters SET updated_at = "1999-01-01 00:00:00" WHERE true;

SELECT * FROM privser_contacts_parameters ORDER BY CHAR_LENGTH(value) DESC;



SELECT a.contact_id, a.email, a.updated_at, a.created_at, a.id
FROM privser_contacts a
JOIN (
    SELECT email
    FROM privser_contacts
    GROUP BY email
    HAVING COUNT(*) > 1
) b ON a.email = b.email;

SELECT a.contact_id, a.email, a.updated_at, a.created_at, a.id
FROM company_employees a
JOIN (
    SELECT contact_id
    FROM company_employees
    GROUP BY contact_id
    HAVING COUNT(*) > 1
) b ON a.contact_id = b.contact_id;


SELECT a.first_name, a.first_name, a.middle_name, a.contact_id, a.email, a.updated_at, a.created_at, a.id
FROM company_employees a
JOIN (
    SELECT CONCAT_WS(' ', last_name, first_name, middle_name) AS full_name
    FROM company_employees
    GROUP BY full_name
    HAVING COUNT(*) > 1
) b ON CONCAT_WS(' ', a.last_name, a.first_name, a.middle_name) = b.full_name;


SELECT a.*
FROM company_employees a
JOIN company_employees b ON a.contact_id <> b.contact_id
WHERE b.contact_id LIKE CONCAT('%', a.contact_id, '%');

DELETE FROM privser_contacts WHERE true;
DELETE FROM django_celery_results_taskresult WHERE status = "RETRY";


DELETE FROM synchronization_sync_parameters WHERE true;
DELETE FROM synchronization_sync_delivery_logs WHERE status_code="new" and target_system="Exchange";
DELETE FROM synchronization_sync WHERE true;

DELETE FROM company_identificationdocuments WHERE true;
DELETE FROM company_mspa WHERE true;
DELETE FROM company_companymanifest WHERE true;
DELETE FROM company_drugtest WHERE true;
DELETE FROM company_iqccard WHERE true;
DELETE FROM company_employmentpacket WHERE true;
DELETE FROM company_dispatchingstatus WHERE true;
DELETE FROM company_interaction WHERE true;
DELETE FROM company_rateofpay WHERE true;

DELETE FROM company_employees WHERE true;


SELECT id, LENGTH(value) AS length, value, contacts_prop_id
FROM company_employees_parameters
WHERE LENGTH(value) > 255;


# проверка считает количество value_date для типа SystemTime
SELECT cp.property_name,
       COUNT(ep.id)         AS total_with_value,
       COUNT(ep.value_date) AS total_with_value_date,
       ROUND(100.0 * COUNT(ep.value_date) / COUNT(ep.id), 2) AS success_percent
FROM company_employees_parameters ep
         JOIN exchange_contacts_prop cp ON ep.contacts_prop_id = cp.id
WHERE cp.property_type = 'SystemTime'
  AND ep.value IS NOT NULL
  AND ep.value != ''
GROUP BY cp.property_name
ORDER BY total_with_value DESC;


SELECT e.id AS employee_id,
       e.phone AS emp_phone,
#        ep_phone.value AS param_phone,
#        e.email AS emp_email,
#        ep_email.value AS param_email,
       e.first_name AS emp_first_name,
       ep_first.value AS param_first_name,
       e.middle_name AS emp_middle_name,
       ep_middle.value AS param_middle_name,
       e.last_name AS emp_last_name,
       ep_last.value AS param_last_name,
       e.job_title AS emp_job_title,
       ep_job.value AS param_job_title
FROM company_employees e
# LEFT JOIN company_employees_parameters ep_phone
#   ON ep_phone.employees_id = e.id AND ep_phone.contacts_prop_id = (
#       SELECT id FROM exchange_contacts_prop WHERE property_name = 'MobilePhone' LIMIT 1
# )
# LEFT JOIN company_employees_parameters ep_email
#   ON ep_email.employees_id = e.id AND ep_email.contacts_prop_id = (
#       SELECT id FROM exchange_contacts_prop WHERE property_name = 'Email' LIMIT 1
# )
LEFT JOIN company_employees_parameters ep_first
  ON ep_first.employees_id = e.id AND ep_first.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'given_name' LIMIT 1
)
LEFT JOIN company_employees_parameters ep_middle
  ON ep_middle.employees_id = e.id AND ep_middle.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'middle_name' LIMIT 1
)
LEFT JOIN company_employees_parameters ep_last
  ON ep_last.employees_id = e.id AND ep_last.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'surname' LIMIT 1
)
LEFT JOIN company_employees_parameters ep_job
  ON ep_job.employees_id = e.id AND ep_job.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'job_title' LIMIT 1
)
# WHERE COALESCE(e.phone, '') <> COALESCE(ep_phone.value, '')
#    OR COALESCE(e.email, '') <> COALESCE(ep_email.value, '')
WHERE
 COALESCE(e.first_name, '')<> COALESCE(ep_first.value, '')
 OR COALESCE(e.middle_name, '')<> COALESCE(ep_middle.value, '')
 OR COALESCE(e.last_name, '') <> COALESCE(ep_last.value, '')
 OR COALESCE(e.job_title, '') <> COALESCE(ep_job.value, '');


SELECT email, COUNT(*)
FROM company_employees
WHERE email IS NOT NULL
GROUP BY email
HAVING COUNT(*) > 1;



SHOW CREATE TABLE synchronization_sync_parameters;

ALTER TABLE synchronization_sync DROP FOREIGN KEY synchronization_sync_contact_exchange_id_fbf49ae6_fk_exchange_;

ALTER TABLE synchronization_sync
ADD CONSTRAINT synchronization_sync_contact_exchange_id_fbf49ae6_fk_exchange_
FOREIGN KEY (employee_id) REFERENCES company_employees(id)
ON DELETE CASCADE;


DELETE from core_mqtt_log where phone is null

SELECT employee_id,
       COUNT(DISTINCT email) AS unique_emails
FROM synchronization_sync_parameters_logs
WHERE employee_id IS NOT NULL
  AND email IS NOT NULL
GROUP BY employee_id
HAVING COUNT(DISTINCT email) > 1
ORDER BY unique_emails DESC;

# Найти дубли по email
SELECT email, COUNT(*) AS count
FROM company_employees
WHERE email IS NOT NULL AND email != ''
GROUP BY email
HAVING COUNT(*) > 1
ORDER BY count DESC;

# Удалить дубли по email
DELETE FROM company_employees
WHERE id IN (
    SELECT id FROM (
        SELECT id
        FROM company_employees
        WHERE email IS NOT NULL AND email != ''
        AND email IN (
            SELECT email
            FROM company_employees
            WHERE email IS NOT NULL AND email != ''
            GROUP BY email
            HAVING COUNT(*) > 1
        )
        AND id NOT IN (
            SELECT MIN(id)
            FROM company_employees
            WHERE email IS NOT NULL AND email != ''
            GROUP BY email
        )
    ) AS to_delete
);

SELECT employee_id,
       email,
       old_value AS old_email,
       new_value AS new_email,
       created_at
FROM synchronization_sync_parameters_logs
WHERE privser_custom_fields_id = 782
  AND email <> new_value
ORDER BY created_at DESC;

SELECT MIN(employee_id) AS employee_id,
       email,
       new_value AS new_email,
       MIN(old_value) AS old_email,
       MIN(created_at) AS first_seen
FROM synchronization_sync_parameters_logs
WHERE privser_custom_fields_id = 782
  AND new_value IS NOT NULL
  AND email <> new_value
GROUP BY email, new_value
ORDER BY first_seen DESC;

SELECT e.id,
       e.email AS employee_email,
       logs.email AS first_log_email,
       logs.created_at AS log_created_at
FROM company_employees e
LEFT JOIN (
    SELECT l1.*
    FROM synchronization_sync_parameters_logs l1
    INNER JOIN (
        SELECT employee_id, MIN(created_at) AS min_created_at
        FROM synchronization_sync_parameters_logs
        WHERE employee_id IS NOT NULL
        GROUP BY employee_id
    ) l2 ON l1.employee_id = l2.employee_id AND l1.created_at = l2.min_created_at
) logs ON logs.employee_id = e.id
WHERE logs.email IS NOT NULL
  AND e.email != logs.email;


# SELECT e.id,
#        e.email AS employee_email,
#        logs.email AS first_log_email,
#        logs.created_at AS log_created_at
# FROM company_employees e
# LEFT JOIN (
#     SELECT l1.*
#     FROM synchronization_sync_parameters_logs l1
#     INNER JOIN (
#         SELECT employee_id, MIN(created_at) AS min_created_at
#         FROM synchronization_sync_parameters_logs
#         WHERE employee_id IS NOT NULL
#         GROUP BY employee_id
#     ) l2 ON l1.employee_id = l2.employee_id AND l1.created_at = l2.min_created_at
# ) logs ON logs.employee_id = e.id
# WHERE logs.email IS NOT NULL
#   AND e.email != logs.email;


# UPDATE company_employees AS ce
# JOIN (
#     SELECT employee_id, email
#     FROM synchronization_sync_parameters_logs AS logs
#     WHERE email IS NOT NULL AND email != ''
#     AND created_at = (
#         SELECT MIN(created_at)
#         FROM synchronization_sync_parameters_logs AS sub
#         WHERE sub.employee_id = logs.employee_id
#           AND sub.email IS NOT NULL AND sub.email != ''
#     )
# ) AS first_logs
# ON first_logs.employee_id = ce.id
# SET ce.email = first_logs.email;


# SELECT ce.id, ce.email AS old_email, first_logs.email AS new_email
# FROM company_employees AS ce
# JOIN (
#     SELECT employee_id, email
#     FROM synchronization_sync_parameters_logs AS logs
#     WHERE email IS NOT NULL AND email != ''
#     AND created_at = (
#         SELECT MIN(created_at)
#         FROM synchronization_sync_parameters_logs AS sub
#         WHERE sub.employee_id = logs.employee_id
#           AND sub.email IS NOT NULL AND sub.email != ''
#     )
# ) AS first_logs
# ON first_logs.employee_id = ce.id
# WHERE ce.email != first_logs.email;

SELECT number
FROM company_identificationdocuments
WHERE updated_at > '2025-06-06'
  AND number IS NOT NULL
GROUP BY number
HAVING COUNT(DISTINCT employee_id) > 1;

SELECT id, employee_id, number, updated_at, type
FROM company_identificationdocuments
WHERE updated_at > '2025-06-06'
  AND number IN (
    SELECT number
    FROM company_identificationdocuments
    WHERE updated_at > '2025-06-06'
      AND number IS NOT NULL
    GROUP BY number
    HAVING COUNT(DISTINCT employee_id) > 1
  )
ORDER BY number, employee_id;

# Дубли по identification documents
SELECT id, employee_id, number
FROM company_identificationdocuments
WHERE number IN (
    SELECT number
    FROM company_identificationdocuments
    WHERE number IS NOT NULL AND number <> ''
    GROUP BY number
    HAVING COUNT(DISTINCT employee_id) > 1
)
ORDER BY number, employee_id;

# Работа по очистке:
truncate table company_availability; #
truncate table company_companymanifest; #
truncate table company_dispatchingstatus; #
truncate table company_drugtest; #
truncate table company_employmentpacket; #
truncate table company_identificationdocuments; #
truncate table company_iqccard; #
truncate table company_mspa; #
truncate table company_notes; #
truncate table company_rateofpay; #
truncate table company_interaction; #

DELETE FROM company_student
WHERE document IS NULL OR document = '';

UPDATE company_employees
SET document = NULL,
    document_modified_time = NULL
WHERE true;

SELECT
    e.id AS employee_id,
    e.email AS current_email,
    GROUP_CONCAT(DISTINCT spl.email SEPARATOR ', ') AS logged_emails
FROM company_employees e
JOIN synchronization_sync_parameters_logs spl
    ON spl.employee_id = e.id
WHERE spl.email IS NOT NULL
  AND e.email IS NOT NULL
  AND TRIM(LOWER(spl.email)) <> TRIM(LOWER(e.email))
GROUP BY e.id, e.email;



# список не совпадений параметра емеил с employees.email
SELECT e.id,
       e.email AS email_main,
       ep.value AS email_prop
FROM company_employees e
JOIN company_employees_parameters ep
  ON ep.employees_id = e.id
WHERE ep.contacts_prop_id = 129
  AND e.email IS NOT NULL
  AND ep.value IS NOT NULL
  AND TRIM(LOWER(e.email)) <> TRIM(LOWER(ep.value));

# Проверка логов на экста неординарные сообщения
select * from synchronization_sync_delivery_logs
         where body not like "%MultipleObjectsReturned%"
           and body not like "%Custom fields no matches%"
           AND JSON_LENGTH(body) > 0
            and status_code != "Multiple Contact Link"
;
select * from synchronization_sync_delivery_logs where body like "%MultipleObjectsReturned%";

DROP INDEX company_employees_parameters_contacts_prop_id_bb96e5ba ON company_employees_parameters;


DELETE from company_fire where id not in
(
17310,
17302,
17302,
17303,
16652,
16652,
17300,
17305,
17305,
17305,
17306,
17307,
17304,
17300,
17300,
17300,
17299,
17299,
17308,
17308,
17308,
17308,
17309,
17309,
17309,
17310,
17310,
17311,
17311,
17311,
17312,
17312
);



select * from privser_contacts_parameters where name="tags";

DESCRIBE company_employees;

ALTER TABLE core_cron_logs
    AUTO_INCREMENT = 1;
ALTER TABLE company_employees
    AUTO_INCREMENT = 1;



SELECT contact_id, COUNT(*)
FROM company_employees
GROUP BY contact_id
HAVING COUNT(*) > 1;


SELECT a.contact_id, a.email
FROM company_employees a
         JOIN (SELECT contact_id
               FROM company_employees
               GROUP BY contact_id
               HAVING COUNT(*) > 1) b ON a.contact_id = b.contact_id;



show create table company_employees;

SHOW INDEXES FROM company_employees;


ALTER TABLE privser_custom_fields
    ADD COLUMN exchange_property_id INT(11);

UPDATE exchange_contacts
SET status_code = 0
WHERE status_code = 19;
UPDATE exchange_contacts
SET changed_properties = '{}'
WHERE changed_properties is NULL;



SELECT *
from exchange_contacts_parameters
where value like "%none%";

UPDATE exchange_contacts_parameters
set value=null
where value like "%none%";
UPDATE exchange_contacts
SET changed_properties = '{}'
WHERE true;
SELECT updated_at
FROM exchange_contacts
where id = 22024;


SELECT *
FROM privser_contacts_parameters
ORDER BY CHAR_LENGTH(value) DESC;

SELECT a.contact_id, a.email, a.updated_at, a.created_at, a.id
FROM privser_contacts a
         JOIN (SELECT email
               FROM privser_contacts
               GROUP BY email
               HAVING COUNT(*) > 1) b ON a.email = b.email;

SELECT a.email
FROM synchronization_sync a
         JOIN (SELECT email
               FROM privser_contacts
               GROUP BY email
               HAVING COUNT(*) > 1) b ON a.email = b.email;


DELETE
FROM company_crew
WHERE true;
DELETE
FROM synchronization_sync_parameters
WHERE true;
DELETE
FROM synchronization_sync
WHERE true;
DELETE
FROM exchange_contacts
WHERE true;

select count(*)
from exchange_contacts_parameters;

SELECT *, CHAR_LENGTH(value) AS max_chars
FROM company_employees_parameters;

DELETE
from company_employees_parameters
where contacts_prop_id = 144;

SELECT employees_id, COUNT(*) as cnt
FROM company_employees_parameters
GROUP BY employees_id
ORDER BY cnt DESC
LIMIT 10;


SELECT employees_id, contacts_prop_id, COUNT(*) as cnt
FROM company_employees_parameters
GROUP BY employees_id, contacts_prop_id
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 10;

SELECT company_employees.id,
       company_employees.email,
       (SELECT U0.value
        FROM company_employees_parameters U0
                 INNER JOIN exchange_contacts_prop U1 ON (U0.contacts_prop_id = U1.id)
        WHERE (U1.property_name = 'Ranking 1 to 10' -- <--- кавычки!
            AND U0.employees_id = company_employees.id)
        LIMIT 1) AS cached_sort
FROM company_employees
ORDER BY cached_sort ASC;


UPDATE company_employees
SET middle_name = NULL
WHERE true;


SELECT cp.property_name,
       COUNT(ep.id)                                          AS total_with_value,
       COUNT(ep.value_date)                                  AS total_with_value_date,
       ROUND(100.0 * COUNT(ep.value_date) / COUNT(ep.id), 2) AS success_percent
FROM company_employees_parameters ep
         JOIN exchange_contacts_prop cp ON ep.contacts_prop_id = cp.id
WHERE cp.property_type = 'SystemTime'
  AND ep.value IS NOT NULL
  AND ep.value != ''
GROUP BY cp.property_name
ORDER BY total_with_value DESC;



SELECT e.id            AS employee_id,
       e.email         AS emp_email,
       ep_email.value  AS param_email
#        e.phone         AS emp_phone,
#        ep_phone.value  AS param_phone,
#        e.email AS emp_email,
#        ep_email.value AS param_email,
#        e.first_name    AS emp_first_name,
#        ep_first.value  AS param_first_name,
#        e.middle_name   AS emp_middle_name,
#        ep_middle.value AS param_middle_name,
#        e.last_name     AS emp_last_name,
#        ep_last.value   AS param_last_name,
#        e.job_title     AS emp_job_title,
#        ep_job.value    AS param_job_title
FROM company_employees e
        LEFT JOIN company_employees_parameters ep_email
          ON ep_email.employees_id = e.id AND ep_email.contacts_prop_id = (
              SELECT id FROM exchange_contacts_prop WHERE property_name = 'Email' LIMIT 1
        )
#          LEFT JOIN company_employees_parameters ep_phone
#                    ON ep_phone.employees_id = e.id AND ep_phone.contacts_prop_id = (SELECT id
#                                                                                     FROM exchange_contacts_prop
#                                                                                     WHERE property_name = 'MobilePhone'
#                                                                                     LIMIT 1)
#          LEFT JOIN company_employees_parameters ep_first
#                    ON ep_first.employees_id = e.id AND ep_first.contacts_prop_id = (SELECT id
#                                                                                     FROM exchange_contacts_prop
#                                                                                     WHERE property_name = 'given_name'
#                                                                                     LIMIT 1)
#          LEFT JOIN company_employees_parameters ep_middle
#                    ON ep_middle.employees_id = e.id AND ep_middle.contacts_prop_id = (SELECT id
#                                                                                       FROM exchange_contacts_prop
#                                                                                       WHERE property_name = 'middle_name'
#                                                                                       LIMIT 1)
#          LEFT JOIN company_employees_parameters ep_last
#                    ON ep_last.employees_id = e.id AND ep_last.contacts_prop_id = (SELECT id
#                                                                                   FROM exchange_contacts_prop
#                                                                                   WHERE property_name = 'surname'
#                                                                                   LIMIT 1)
#          LEFT JOIN company_employees_parameters ep_job
#                    ON ep_job.employees_id = e.id AND ep_job.contacts_prop_id = (SELECT id
#                                                                                 FROM exchange_contacts_prop
#                                                                                 WHERE property_name = 'job_title'
#                                                                                 LIMIT 1)
WHERE COALESCE(e.email, '')     <> COALESCE(ep_email.value, '')
#  COALESCE(TRIM(e.phone), '') <> COALESCE(TRIM(ep_phone.value), '')
#    OR COALESCE(TRIM(e.first_name), '') <> COALESCE(TRIM(ep_first.value), '')
#    OR COALESCE(TRIM(e.middle_name), '') <> COALESCE(TRIM(ep_middle.value), '')
#    OR COALESCE(TRIM(e.last_name), '') <> COALESCE(TRIM(ep_last.value), '')
#    OR COALESCE(TRIM(e.job_title), '') <> COALESCE(TRIM(ep_job.value), '')
;

SELECT cp.property_name,
       COUNT(ep.id)         AS total_with_value,
       COUNT(ep.value_date) AS total_with_value_date
FROM company_employees_parameters ep
         JOIN exchange_contacts_prop cp ON ep.contacts_prop_id = cp.id
WHERE cp.property_type = 'SystemTime'
  AND ep.value IS NOT NULL
  AND ep.value != ''
GROUP BY cp.property_name
ORDER BY total_with_value DESC;


SELECT employees_id
FROM company_employees_parameters
WHERE employees_id NOT IN (SELECT id
                           FROM company_employees);



DELETE
FROM company_employees_parameters
WHERE employees_id NOT IN (SELECT id
                           FROM company_employees);

SELECT employees_id, COUNT(*)
FROM company_employees_parameters
WHERE contacts_prop_id = 140
GROUP BY employees_id
HAVING COUNT(*) > 1



SELECT email, COUNT(*)
FROM company_employees
WHERE email IS NOT NULL
GROUP BY email
HAVING COUNT(*) > 1;


SELECT id, email
FROM privser_contacts
WHERE id IN (SELECT contacts_id
             FROM privser_contacts_parameters
             WHERE name = 'Et6He1FIsCiSDwZecZuQ');

SELECT `company_employees`.`id`,
       `company_employees`.`email`,
       `company_employees`.`type`,
       `company_employees`.`contact_id`,
       `company_employees`.`last_modified_name`,
       `company_employees`.`last_modified_time`,
       `company_employees`.`datetime_created`,
       `company_employees`.`status_code`,
       `company_employees`.`test`,
       `company_employees`.`first_name`,
       `company_employees`.`middle_name`,
       `company_employees`.`last_name`,
       `company_employees`.`job_title`,
       `company_employees`.`phone`,
       `company_employees`.`updated_at`,
       `company_employees`.`created_at`,
       `company_employees`.`fire_crew_id`,
       `company_employees`.`is_manifested`,
       `company_employees`.`document`,
       `company_employees`.`document_modified_time`,
       (SELECT U0.`date` FROM `company_companymanifest` U0 WHERE U0.`employee_id` = (`company_employees`.`id`) ORDER BY U0.`updated_at` DESC LIMIT 1) AS `latest_date`
FROM `company_employees`
WHERE `company_employees`.`id` = 7751


SELECT U0.`date` FROM `company_companymanifest` U0 WHERE U0.`employee_id` = 25842 ORDER BY U0.`updated_at` DESC LIMIT 1
SELECT * FROM company_identificationdocuments WHERE employee_id = 3892;




SHOW CREATE TABLE company_identificationdocuments;

ALTER TABLE company_identificationdocuments DROP FOREIGN KEY company_identificati_employee_id_b6d3cacc_fk_company_e;
ALTER TABLE company_identificationdocuments
ADD CONSTRAINT company_identificati_employee_id_b6d3cacc_fk_company_e
FOREIGN KEY (employee_id) REFERENCES company_employees(id)
ON DELETE CASCADE;


SELECT
    employees_id,
    contacts_prop_id,
    COUNT(*) as count
FROM
    company_employees_parameters
GROUP BY
    employees_id, contacts_prop_id
HAVING
    COUNT(*) > 1;

SELECT
    p.id,
    p.employees_id,
    p.contacts_prop_id,
    p.value,
    p.updated_at
FROM
    company_employees_parameters p
JOIN (
    SELECT
        employees_id,
        contacts_prop_id
    FROM
        company_employees_parameters
    GROUP BY
        employees_id, contacts_prop_id
    HAVING
        COUNT(*) > 1
) dup
ON p.employees_id = dup.employees_id AND p.contacts_prop_id = dup.contacts_prop_id
ORDER BY
    p.employees_id, p.contacts_prop_id, p.id;

DELETE FROM company_employees_parameters
WHERE id IN (
    SELECT id FROM (
        SELECT id
        FROM company_employees_parameters
        WHERE (employees_id, contacts_prop_id, value) IN (
            SELECT employees_id, contacts_prop_id, value
            FROM company_employees_parameters
            GROUP BY employees_id, contacts_prop_id, value
            HAVING COUNT(*) > 1
        )
        AND id NOT IN (
            SELECT MIN(id)
            FROM company_employees_parameters
            GROUP BY employees_id, contacts_prop_id, value
        )
    ) AS temp_ids
);


SELECT *
FROM privser_custom_fields
WHERE privser_id IN (
    SELECT privser_id
    FROM privser_custom_fields
    WHERE privser_id IS NOT NULL
    GROUP BY privser_id
    HAVING COUNT(*) > 1
);

SELECT
    e.id AS employee_id,
    t.name AS training_type_name,
    s.document
FROM company_student s
JOIN company_trainingclass tc ON s.training_class_id = tc.id
JOIN company_course c ON tc.course_id = c.id
JOIN company_trainingtype t ON c.training_type_id = t.id
WHERE s.employee_id = 42088


SELECT
    email,
    COUNT(*) AS count,
    GROUP_CONCAT(id ORDER BY id) AS employee_ids
FROM
    company_employees
WHERE
    email IS NOT NULL
    AND email != ''
GROUP BY
    email
HAVING
    COUNT(*) > 1
ORDER BY
    count DESC;

SELECT
    email,
    contact_id,
    COUNT(*) AS count,
    GROUP_CONCAT(id ORDER BY id) AS employee_ids
FROM
    company_employees
WHERE
    email IS NOT NULL AND email != ''
    AND contact_id IS NOT NULL AND contact_id != ''
GROUP BY
    email, contact_id
HAVING
    COUNT(*) > 1
ORDER BY
    count DESC;

SELECT email, contact_id, COUNT(*) AS cnt
FROM company_employees
GROUP BY email, contact_id
HAVING COUNT(*) > 1;

SELECT
    a.id AS id_a, b.id AS id_b,
    a.email AS email_a, b.email AS email_b,
    a.contact_id AS contact_id_a, b.contact_id AS contact_id_b
FROM company_employees a
JOIN company_employees b
    ON a.id < b.id
    AND a.email = b.email
    AND a.contact_id = b.contact_id
    AND a.id != b.id;

SELECT id, contact_id, LENGTH(contact_id) AS len, HEX(contact_id) AS hex
FROM company_employees
WHERE email = 'dariuslam04@gmail.com'
ORDER BY contact_id;


SELECT employee_id,
       COUNT(DISTINCT email) AS unique_emails
FROM synchronization_sync_parameters_logs
WHERE employee_id IS NOT NULL
  AND email IS NOT NULL
GROUP BY employee_id
HAVING COUNT(DISTINCT email) > 1
ORDER BY unique_emails DESC;

SELECT test, COUNT(*) AS value_count FROM company_employees GROUP BY test;

# Работа по очистке:
truncate table company_availability; #
truncate table company_companymanifest; #
truncate table company_dispatchingstatus; #
truncate table company_drugtest; #
truncate table company_employmentpacket; #
truncate table company_identificationdocuments; #
truncate table company_iqccard; #
truncate table company_mspa; #
truncate table company_notes; #
truncate table company_rateofpay; #
truncate table company_interaction; #

DELETE FROM company_student
WHERE document IS NULL OR document = '';

# SELECT * FROM company_student
# WHERE document IS NULL OR document = '';

truncate table company_student;  --- TODO documents
truncate table company_trainingclass; #
truncate table company_course; #


# Найти дубли по email
SELECT email, COUNT(*) AS count
FROM company_employees
WHERE email IS NOT NULL AND email != ''
GROUP BY email
HAVING COUNT(*) > 1
ORDER BY count DESC;


SELECT type, number
FROM company_identificationdocuments
WHERE updated_at > '2025-06-06'
  AND number IS NOT NULL
GROUP BY type, number
HAVING COUNT(DISTINCT employee_id) > 1;



SELECT id, employee_id, number, updated_at, type
FROM company_identificationdocuments
WHERE updated_at > '2025-06-06'
  AND number IN (
    SELECT number
    FROM company_identificationdocuments
    WHERE updated_at > '2025-06-06'
      AND number IS NOT NULL
    GROUP BY number
    HAVING COUNT(DISTINCT employee_id) > 1
  )
ORDER BY number, employee_id;

# Вот SQL-запрос, который покажет повторяющиеся number, назначенные разным employee, и при этом number не NULL и не пустая строка:
SELECT number, COUNT(DISTINCT employee_id) AS employee_count
FROM company_identificationdocuments
WHERE number IS NOT NULL AND number <> ''
GROUP BY number
HAVING COUNT(DISTINCT employee_id) > 1;

# Если хочешь сразу увидеть конкретные записи с такими дублями, то вот
SELECT id, employee_id, number
FROM company_identificationdocuments
WHERE number IN (
    SELECT number
    FROM company_identificationdocuments
    WHERE number IS NOT NULL AND number <> ''
    GROUP BY number
    HAVING COUNT(DISTINCT employee_id) > 1
)
ORDER BY number, employee_id;

# был какойто баг не мог транкейтнуть таблицу
# SELECT table_name, constraint_name
# FROM information_schema.key_column_usage
# WHERE referenced_table_name = 'company_availability';

# SHOW OPEN TABLES WHERE `Table` = 'company_availability';
# SHOW FULL PROCESSLIST;
#
# SET SESSION lock_wait_timeout = 2;
# DROP TABLE IF EXISTS company_availability;
# KILL 3526;
#
# SHOW OPEN TABLES WHERE `Table` = 'company_availability';
# SHOW ENGINE INNODB STATUS;
# SHOW FULL PROCESSLIST;

# список не совпадений параметра емеил с employees.email
SELECT e.id,
       e.email AS email_main,
       ep.value AS email_prop
FROM company_employees e
JOIN company_employees_parameters ep
  ON ep.employees_id = e.id
WHERE ep.contacts_prop_id = 129
  AND e.email IS NOT NULL
  AND ep.value IS NOT NULL
  AND TRIM(LOWER(e.email)) <> TRIM(LOWER(ep.value));


# Список возможно запоротых струдников
SELECT
    e.id AS employee_id,
    e.email AS current_email,
    GROUP_CONCAT(DISTINCT spl.email SEPARATOR ', ') AS logged_emails
FROM company_employees e
JOIN synchronization_sync_parameters_logs spl
    ON spl.employee_id = e.id
WHERE spl.email IS NOT NULL
  AND e.email IS NOT NULL
  AND TRIM(LOWER(spl.email)) <> TRIM(LOWER(e.email))
GROUP BY e.id, e.email;


SELECT
    e.id AS employee_id,
    e.email AS current_email,
    spl.email AS logged_email,
    spl.new_value AS new_email_from_exchange,
    spl.old_value AS old_email_in_system,
    spl.updated_at AS log_time
FROM synchronization_sync_parameters_logs spl
JOIN company_employees e ON spl.employee_id = e.id
WHERE spl.source_system = 'exchange'
  AND spl.status_code = 5  -- COMPLETED
  AND LOWER(spl.new_value) LIKE '%@%'
  AND LOWER(spl.new_value) <> LOWER(e.email)  -- подменили email на другой
  AND LOWER(spl.property_name) = 'email';




# Фикс связей
ALTER TABLE privser_contacts_parameters
DROP FOREIGN KEY privser_contacts_par_contacts_id_c449f046_fk_privser_c;

ALTER TABLE privser_contacts_parameters
ADD CONSTRAINT privser_contacts_par_contacts_id_c449f046_fk_privser_c
FOREIGN KEY (contacts_id)
REFERENCES privser_contacts(id)
ON DELETE CASCADE;


ALTER TABLE synchronization_sync_parameters_logs
DROP FOREIGN KEY synchronization_sync_contact_privser_id_b0c19d9f_fk_privser_c;

ALTER TABLE synchronization_sync_parameters_logs
ADD CONSTRAINT synchronization_sync_contact_privser_id_b0c19d9f_fk_privser_c
FOREIGN KEY (contact_privser_id)
REFERENCES privser_contacts(id)
ON DELETE CASCADE;


ALTER TABLE synchronization_sync
DROP FOREIGN KEY synchronization_sync_contact_privser_id_8a43a0ae_fk_privser_c;

ALTER TABLE synchronization_sync
ADD CONSTRAINT synchronization_sync_contact_privser_id_8a43a0ae_fk_privser_c
FOREIGN KEY (contact_privser_id)
REFERENCES privser_contacts(id)
ON DELETE CASCADE;


SELECT s.id, s.document, t.name
FROM company_student s
JOIN company_trainingclass tc ON s.training_class_id = tc.id
JOIN company_course c ON tc.course_id = c.id
JOIN company_trainingtype t ON c.training_type_id = t.id
WHERE t.name = 'RT-130';


SELECT *
FROM company_student s
JOIN company_trainingclass tc ON s.training_class_id = tc.id
JOIN company_course c ON tc.course_id = c.id
JOIN company_trainingtype t ON c.training_type_id = t.id
WHERE t.name = 'RT-130'
  AND (
    s.document IS NULL OR
    s.document = '' OR
    s.document NOT LIKE '%student/%'
  );


# fix email
# UPDATE company_employees
# SET email = CONCAT(SUBSTRING(email, LOCATE('AAA=__', email) + 6), '(', id, ')')
# WHERE LOCATE('AAA=__', email) > 0;
#
# UPDATE company_employees
# SET email = CONCAT(SUBSTRING(email, LOCATE('AAA==__', email) + 7), '(', id, ')')
# WHERE LOCATE('AAA==__', email) > 0;
#
# UPDATE company_employees
# SET email = CONCAT(SUBSTRING(email, LOCATE('QwAA__', email) + 6), '(', id, ')')
# WHERE LOCATE('QwAA__', email) > 0;
DROP INDEX company_employees_parameters_contacts_prop_id_bb96e5ba ON company_employees_parameters;

SELECT e.employees_id, e.value_bool
FROM company_employees_parameters e
JOIN exchange_contacts_prop c ON c.id = e.contacts_prop_id
WHERE c.property_name = 'Current trainee' AND e.employees_id = 49482;


# SELECT TRIM(fire_number) AS fire_number,
#        TRIM(incident_name) AS incident_name,
#        COUNT(*) AS cnt
# FROM company_fire
# GROUP BY TRIM(fire_number), TRIM(incident_name)
# HAVING COUNT(*) > 1;
#
# SELECT id, fire_number
# FROM company_fire
# WHERE fire_number IS NULL OR TRIM(fire_number) = '';
#
# UPDATE company_fire
# SET fire_number = CAST(id AS CHAR(100))
# WHERE fire_number IS NULL OR TRIM(fire_number) = '';




SHOW INDEX FROM company_fire;
ALTER TABLE company_fire DROP INDEX `uniq_fire_num_name`;


select count(*) from company_dayonfire where id>5909;
DELETE from company_dayonfire where id>5909;
