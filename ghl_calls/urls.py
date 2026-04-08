from django.urls import path

from .views import (
    ghl_call_bulk_edit,
    ghl_call_review,
    ghl_call_review_create_note,
    ghl_question_grouping_review,
    ghl_call_webhook,
    ghl_transcript_webhook,
)

urlpatterns = [
    path("", ghl_call_webhook, name="ghl_call_webhook"),
    path("transcript/", ghl_transcript_webhook, name="ghl_transcript_webhook"),
    path("bulk-edit/", ghl_call_bulk_edit, name="ghl_call_bulk_edit"),
    path("grouping/questions/", ghl_question_grouping_review, name="ghl_question_grouping_review"),
    path("review/<int:call_id>/", ghl_call_review, name="ghl_call_review"),
    path("review/<int:call_id>/notes/", ghl_call_review_create_note, name="ghl_call_review_create_note"),
]
