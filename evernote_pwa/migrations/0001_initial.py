from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EvernoteConnection",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("access_token", models.TextField(blank=True)),
                ("username", models.CharField(blank=True, max_length=255)),
                ("edam_user_id", models.BigIntegerField(blank=True, null=True)),
                ("shard_id", models.CharField(blank=True, max_length=64)),
                ("connected_at", models.DateTimeField(blank=True, null=True)),
                ("last_pulled_at", models.DateTimeField(blank=True, null=True)),
                ("last_pushed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Evernote connection",
                "verbose_name_plural": "Evernote connection",
            },
        ),
        migrations.CreateModel(
            name="Notebook",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("guid", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("stack", models.CharField(blank=True, max_length=255)),
                ("update_sequence_num", models.BigIntegerField(default=0)),
                ("is_default", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("last_seen_remote_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name", "id"],
            },
        ),
        migrations.CreateModel(
            name="Note",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("evernote_guid", models.CharField(blank=True, max_length=64, null=True, unique=True)),
                ("title", models.CharField(blank=True, max_length=255)),
                ("content", models.TextField(blank=True)),
                ("content_enml", models.TextField(blank=True)),
                (
                    "source",
                    models.CharField(
                        choices=[("imported", "Imported"), ("local", "Local")],
                        default="local",
                        max_length=16,
                    ),
                ),
                ("allow_push_to_evernote", models.BooleanField(default=False)),
                ("needs_push", models.BooleanField(default=False)),
                ("is_deleted_remote", models.BooleanField(default=False)),
                ("remote_created_at", models.DateTimeField(blank=True, null=True)),
                ("remote_updated_at", models.DateTimeField(blank=True, null=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "notebook",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notes",
                        to="evernote_pwa.notebook",
                    ),
                ),
            ],
            options={
                "ordering": ["title", "-updated_at", "id"],
            },
        ),
    ]
