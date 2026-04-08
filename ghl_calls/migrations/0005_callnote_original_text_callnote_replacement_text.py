from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ghl_calls", "0004_ghlcall_prompt_spec"),
    ]

    operations = [
        migrations.AddField(
            model_name="callnote",
            name="original_text",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="callnote",
            name="replacement_text",
            field=models.TextField(blank=True),
        ),
    ]
