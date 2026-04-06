from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "cleanStudentDuplicatesCommand"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"Run cleanStudentDuplicatesCommand."))

        # clean_student_duplicates
        from company.models import Student
        from django.db.models import Count

        # Для каждого employee, training_class, test_score ищем дубликаты
        dupes = (
            Student.objects
            .values("employee", "training_class")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for d in dupes:
            students = (
                Student.objects
                .filter(
                    employee=d["employee"],
                    training_class=d["training_class"],
                )
                .order_by("id")  # Или по updated_at — зависит от того, что считать "лучшим"
            )

            if len(students) > 1:
                # Оставить одну с document, если есть. Если нет — просто первую.
                keep_one = next((s for s in students if s.document), students[0])

                for s in students:
                    if s != keep_one:
                        # if s.employee.id == 3759:
                        #     print("deleting", s.employee.id, s.training_class, s.document)
                        #     s.delete()
                        print("deleting", s.employee.id, s.training_class, s.document)
                        s.delete()

        self.stdout.write(self.style.SUCCESS(f"End cleanStudentDuplicatesCommand."))
