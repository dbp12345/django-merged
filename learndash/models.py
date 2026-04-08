from django.db import models


class LearndashStudent(models.Model):
    wp_user_id = models.BigIntegerField(unique=True, db_index=True)
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.wp_user_id} - {self.email}"


class LearndashCourse(models.Model):
    wp_course_id = models.BigIntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class LearndashLesson(models.Model):
    wp_lesson_id = models.BigIntegerField(db_index=True)
    student = models.ForeignKey(LearndashStudent, on_delete=models.CASCADE)
    course = models.ForeignKey(LearndashCourse, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("wp_lesson_id", "student")

    def __str__(self):
        return f"{self.title} ({self.student})"
