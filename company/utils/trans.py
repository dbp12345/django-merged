F_L = {
    "IQC_card_entries": "IQC",
    "IQC_card_entries__position": "IQC position",
    "student_entries": "Students",
    "training_class__course__training_type__updated_at": "Class-Course-Type updated at",
    "training_class__course__training_type__name": "Class-Course-Type name",
    "training_class__course__governing_body": "Class-Course governing_body",
    "training_class__course__inperson_required": "Class-Course inperson_required",
    "training_class__course__updated_at": "Class-Course updated at",
    "training_class__date": "Class date",
    "training_class__location": "Class location",
    "training_class__test_score": "Class test score",
    "training_class__updated_at": "Class updated at",
    "Identification Documents": "ID",
    "Course": "Course ",
    "employees": "Employees",
    "employees_parameters_entries": "Employees parameters",
    "employees_parameters_entries__contacts_prop__property_name": "property_name ",
    "test_score": "Score",
    "updated_at": "updated at",
    "company_workers_as_employees": "Company Workers",
    "fire_crew": "FireCrew",
    "fire_run_entries": "FireRun",
    "fire_run_entries_as_crwb": "FireRun_CRWB",
}


def trans(k):
    return F_L.get(k, k)
