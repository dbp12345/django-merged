from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ghl_calls", "0007_alter_callnote_negative_impact_score"),
    ]

    operations = [
        migrations.AddField(
            model_name="ghlcall",
            name="call_sid",
            field=models.CharField(blank=True, db_index=True, max_length=128),
        ),
    ]
