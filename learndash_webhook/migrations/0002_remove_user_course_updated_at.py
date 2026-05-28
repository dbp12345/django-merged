from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("learndash_webhook", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="learndashcourse",
            name="updated_at",
        ),
        migrations.RemoveField(
            model_name="learndashuser",
            name="updated_at",
        ),
    ]
