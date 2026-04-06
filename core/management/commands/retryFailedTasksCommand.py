import json
from django.core.management.base import BaseCommand
from django_celery_results.models import TaskResult

# python manage.py retryFailedTasksCommand
class Command(BaseCommand):
    help = "Повторный запуск задач"

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            type=str,
            help="json",
        )

    def handle(self, *args, **options):
        # json = options.get("json")
        print("-=start=-")

        # from core.tasks.privser_tasks import update_from_privser_task
        from core.tasks.exchange_tasks import update_from_exchange_task
        failed_tasks = TaskResult.objects.filter(status="STARTED", task_name="update_from_exchange")
        for task in failed_tasks:
            print("id", task.id)
            print("task_kwargs", task.task_kwargs)
            json_string = task.task_kwargs.strip('"').replace("'", '"').replace("True", "true")
            print("json_string", json_string)
            print("type(json_string)", type(json_string))
            data = json.loads(json_string)
            print(data)
            update_from_exchange_task.apply_async(
                kwargs={
                    "offset": data.get("offset"),
                    "batch_size": data.get("batch_size"),
                    "ignore_diff_properties": data.get("ignore_diff_properties"),
                }
            )

            # update_from_exchange_task.apply_async(**data)

            # или так
            # update_from_privser_task.apply_async(**data)
