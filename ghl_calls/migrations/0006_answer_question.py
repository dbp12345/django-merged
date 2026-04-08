from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ghl_calls", "0005_callnote_original_text_callnote_replacement_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="answer",
            name="question",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="answers",
                to="ghl_calls.question",
            ),
        ),
    ]
