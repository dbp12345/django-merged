from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ghl_calls", "0008_ghlcall_call_sid"),
    ]

    operations = [
        migrations.AddField(
            model_name="ghlcall",
            name="raw_ended_at",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="ghlcall",
            name="raw_started_at",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
