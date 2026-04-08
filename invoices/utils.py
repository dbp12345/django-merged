from django.apps import apps


def get_all_model_labels():
    """
    Returns labels like:
    ['invoices.Invoice', 'jobs.Job', 'contacts.Contact', ...]
    """
    labels = []
    for model in apps.get_models():
        meta = model._meta
        # meta.model_name is lowercase; class name is meta.object_name
        labels.append(f"{meta.app_label}.{meta.object_name}")
    return sorted(labels)


def get_model_field_names(model_label):
    """
    Given 'app_label.ModelName', return that model's field names.
    """
    try:
        app_label, model_name = model_label.split('.')
        model = apps.get_model(app_label, model_name)
    except (ValueError, LookupError):
        return []

    return [
        field.name
        for field in model._meta.fields
        if field.name not in ('id', 'created_at')
    ]
