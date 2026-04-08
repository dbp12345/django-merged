import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ghl_calls", "0003_call_analysis_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="ghlcall",
            name="prompt_spec",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="calls",
                to="ghl_calls.promptspec",
            ),
        ),
    ]
