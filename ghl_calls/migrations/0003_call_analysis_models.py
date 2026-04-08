import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ghl_calls", "0002_remove_ghlcall_recording_file_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ghlcall",
            name="audio_file",
            field=models.FileField(blank=True, null=True, upload_to="ghl_calls/audio/"),
        ),
        migrations.AddField(
            model_name="ghlcall",
            name="initiated_by",
            field=models.CharField(
                choices=[("employee", "Employee"), ("customer", "Customer"), ("unknown", "Unknown")],
                default="unknown",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="PromptSpec",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prompt", models.TextField()),
                ("score", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("response_time", models.FloatField(blank=True, null=True)),
                ("token_cost", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="UnifiedNodeAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="UnifiedNodeQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="UnifiedNodeStatement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Answer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("speaker_role", models.CharField(choices=[("employee", "Employee"), ("customer", "Customer"), ("unknown", "Unknown")], default="unknown", max_length=20)),
                ("text", models.TextField(blank=True)),
                ("ai_accuracy_score", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("human_accuracy_score", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("start_index", models.PositiveIntegerField(blank=True, null=True)),
                ("end_index", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("call", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="ghl_calls.ghlcall")),
                ("unified_answer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="ghl_calls.unifiednodeanswer")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("speaker_role", models.CharField(choices=[("employee", "Employee"), ("customer", "Customer"), ("unknown", "Unknown")], default="unknown", max_length=20)),
                ("text", models.TextField(blank=True)),
                ("ai_accuracy_score", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("human_accuracy_score", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("start_index", models.PositiveIntegerField(blank=True, null=True)),
                ("end_index", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("call", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="ghl_calls.ghlcall")),
                ("unified_question", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="ghl_calls.unifiednodequestion")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.CreateModel(
            name="Statement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("speaker_role", models.CharField(choices=[("employee", "Employee"), ("customer", "Customer"), ("unknown", "Unknown")], default="unknown", max_length=20)),
                ("text", models.TextField(blank=True)),
                ("ai_accuracy_score", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("human_accuracy_score", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("start_index", models.PositiveIntegerField(blank=True, null=True)),
                ("end_index", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("call", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="statements", to="ghl_calls.ghlcall")),
                ("unified_statement", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="statements", to="ghl_calls.unifiednodestatement")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.CreateModel(
            name="CallNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_index", models.PositiveIntegerField(blank=True, null=True)),
                ("end_index", models.PositiveIntegerField(blank=True, null=True)),
                ("edit_option", models.CharField(choices=[("CHG", "Change / Replace"), ("DEL", "Delete / Remove"), ("ADD", "Add / Missing"), ("MOV", "Reorder / Move"), ("OK", "Perfect as is")], default="OK", max_length=3)),
                ("negative_impact_score", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("answer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="ghl_calls.answer")),
                ("call", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="ghl_calls.ghlcall")),
                ("question", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="ghl_calls.question")),
                ("statement", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="ghl_calls.statement")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
    ]
