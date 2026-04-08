from __future__ import annotations

from django.db import models


class LearndashUser(models.Model):
    """
    Represents a LearnDash/WP user on the Django side.
    """
    wp_user_id = models.PositiveBigIntegerField(unique=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.email or f"WP User {self.wp_user_id}"


class LearndashCourse(models.Model):
    """
    Courses table:
    - wp_course_id is the stable unique identity
    - name is NOT unique (names can change or collide)
    """
    wp_course_id = models.PositiveBigIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name or f"Course {self.wp_course_id}"


class LearndashLessonCompletion(models.Model):
    """
    Lesson completions:
    - many completions per user
    - many completions per course
    - first completion only matters
    """
    user = models.ForeignKey(
        LearndashUser,
        on_delete=models.CASCADE,
        related_name="lesson_completions",
        db_index=True,
    )
    course = models.ForeignKey(
        LearndashCourse,
        on_delete=models.CASCADE,
        related_name="lesson_completions",
        db_index=True,
    )

    # Stable lesson id from WP/LearnDash
    wp_lesson_id = models.PositiveBigIntegerField(db_index=True)

    lesson_name = models.CharField(max_length=255, blank=True, default="")
    completed_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # ✅ One lesson completion per user per course per lesson
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course", "wp_lesson_id"],
                name="uniq_lesson_completion_user_course_lesson",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["user", "wp_lesson_id"]),
            models.Index(fields=["course", "completed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.lesson_name or self.wp_lesson_id} ({self.course})"


class LearndashCourseCompletion(models.Model):
    """
    Course completions:
    - first completion only matters
    """
    user = models.ForeignKey(
        LearndashUser,
        on_delete=models.CASCADE,
        related_name="course_completions",
        db_index=True,
    )
    course = models.ForeignKey(
        LearndashCourse,
        on_delete=models.CASCADE,
        related_name="course_completions",
        db_index=True,
    )

    completed_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # ✅ One course completion per user per course
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="uniq_course_completion_user_course",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["course", "completed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.course}"
