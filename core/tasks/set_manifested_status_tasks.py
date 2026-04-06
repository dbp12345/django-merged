from celery import shared_task


@shared_task(
    name="manifested_status",
)
def set_manifested_status_tasks(**kwargs):
    from core.services.ManifestService import ManifestService
    return ManifestService.update_is_manifested_flags_from_all_dates()
