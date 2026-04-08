from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ghl_calls", "0006_answer_question"),
    ]

    operations = [
        migrations.AlterField(
            model_name="callnote",
            name="negative_impact_score",
            field=models.IntegerField(
                blank=True,
                null=True,
                validators=[MinValueValidator(-100), MaxValueValidator(100)],
            ),
        ),
    ]
