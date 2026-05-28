from django.contrib import admin
from .models import (
    LearndashUser,
    LearndashCourse,
    LearndashLessonCompletion,
    LearndashCourseCompletion,
)


@admin.register(LearndashUser)
class LearndashUserAdmin(admin.ModelAdmin):
    list_display = ("wp_user_id", "email", "created_at")
    search_fields = ("wp_user_id", "email")


@admin.register(LearndashCourse)
class LearndashCourseAdmin(admin.ModelAdmin):
    list_display = ("wp_course_id", "name", "created_at")
    search_fields = ("wp_course_id", "name")


@admin.register(LearndashLessonCompletion)
class LearndashLessonCompletionAdmin(admin.ModelAdmin):
    list_display = ("wp_lesson_id", "lesson_name", "user", "course", "completed_at")
    list_filter = ("course",)
    search_fields = ("wp_lesson_id", "lesson_name", "user__email", "course__name")


@admin.register(LearndashCourseCompletion)
class LearndashCourseCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "completed_at")
    list_filter = ("course",)
    search_fields = ("user__email", "course__name")
