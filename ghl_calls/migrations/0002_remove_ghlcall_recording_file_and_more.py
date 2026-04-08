from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ghl_calls", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ghlcall",
            name="recording_file",
        ),
        migrations.RemoveField(
            model_name="ghlcall",
            name="transcript_language",
        ),
    ]
