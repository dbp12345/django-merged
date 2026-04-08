from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contacts", "0009_alter_contact_privser_contact_id_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="GHLCall",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ghl_call_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("ghl_contact_id", models.CharField(blank=True, db_index=True, max_length=128)),
                ("ghl_location_id", models.CharField(blank=True, db_index=True, max_length=128)),
                ("direction", models.CharField(choices=[("inbound", "Inbound"), ("outbound", "Outbound"), ("unknown", "Unknown")], default="unknown", max_length=20)),
                ("status", models.CharField(blank=True, db_index=True, max_length=64)),
                ("from_number", models.CharField(blank=True, db_index=True, max_length=50)),
                ("to_number", models.CharField(blank=True, db_index=True, max_length=50)),
                ("recording_url", models.URLField(blank=True, max_length=1000)),
                ("recording_file", models.FileField(blank=True, null=True, upload_to="ghl_calls/recordings/")),
                ("recording_duration_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("processing_status", models.CharField(choices=[("pending", "Pending"), ("downloaded", "Downloaded"), ("transcribed", "Transcribed"), ("failed", "Failed")], db_index=True, default="pending", max_length=20)),
                ("transcription_model", models.CharField(blank=True, max_length=100)),
                ("transcript_text", models.TextField(blank=True)),
                ("transcript_language", models.CharField(blank=True, max_length=32)),
                ("transcription_error", models.TextField(blank=True)),
                ("raw_transcription_response", models.JSONField(blank=True, default=dict)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("raw_recording_metadata", models.JSONField(blank=True, default=dict)),
                ("last_webhook_received_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("contact", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ghl_calls", to="contacts.contact")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="GHLCallWebhookEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(db_index=True, max_length=128)),
                ("event_id", models.CharField(blank=True, db_index=True, max_length=128)),
                ("signature", models.CharField(blank=True, max_length=255)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("received_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("processing_error", models.TextField(blank=True)),
                ("call", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="webhook_events", to="ghl_calls.ghlcall")),
            ],
            options={
                "ordering": ["-received_at"],
            },
        ),
    ]
