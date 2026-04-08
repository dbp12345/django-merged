from django.db import migrations


DEFAULT_SEGMENTATION_PROMPT = (
    "Break the call transcript into ordered segments. Classify each segment as exactly one of: "
    "question, answer, or statement. Keep speaker attribution when available. If a sentence is a "
    "question, it becomes a question. The direct response to the most recent unresolved question "
    "becomes an answer. Everything else becomes a statement. Preserve the original wording. "
    "For unified nodes, group semantically equivalent questions together even when phrased "
    "differently, and do the same for answers and statements. Reuse the same unified node when "
    "the meaning matches. If two segments are materially different in meaning, they must not be "
    "placed in the same unified node."
)


def seed_default_prompt_spec(apps, schema_editor):
    PromptSpec = apps.get_model("ghl_calls", "PromptSpec")

    active_prompt = PromptSpec.objects.filter(is_active=True).order_by("-updated_at", "-id").first()
    if active_prompt:
        return

    existing_prompt = PromptSpec.objects.order_by("-updated_at", "-id").first()
    if existing_prompt:
        existing_prompt.is_active = True
        if not existing_prompt.name:
            existing_prompt.name = existing_prompt.prompt[:80]
        existing_prompt.save(update_fields=["is_active", "name", "updated_at"])
        return

    PromptSpec.objects.create(
        name="Default call segmentation prompt",
        prompt=DEFAULT_SEGMENTATION_PROMPT,
        is_active=True,
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ghl_calls", "0010_promptspec_is_active_promptspec_name"),
    ]

    operations = [
        migrations.RunPython(seed_default_prompt_spec, noop_reverse),
    ]
