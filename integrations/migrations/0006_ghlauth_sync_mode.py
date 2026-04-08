from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0005_alter_ghlauth_location_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="ghlauth",
            name="sync_mode",
            field=models.CharField(
                choices=[("read_write", "Read / Write"), ("read_only", "Read Only")],
                default="read_write",
                max_length=20,
            ),
        ),
    ]
