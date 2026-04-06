from django.core.cache import cache
from core.models import Task_Toggle

def is_task_enabled(task_name: str) -> bool:
    cache_key = f"task_toggle:{task_name}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        toggle = Task_Toggle.objects.get(name=task_name)
        cache.set(cache_key, toggle.is_enabled, timeout=60)  # кэш на минуту
        return toggle.is_enabled
    except Task_Toggle.DoesNotExist:
        cache.set(cache_key, True, timeout=60)
        return True  # по умолчанию включено
