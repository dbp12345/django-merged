from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0004_ghlsyncstate_ghlcontactsyncmeta"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ghlauth",
            name="location_id",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
    ]
