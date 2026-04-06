from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings


class Command(BaseCommand):
    help = "Clear all Django cache"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cache-name",
            type=str,
            help="Clear specific cache (default, axes, etc.). If not specified, clears all caches.",
        )

    def handle(self, *args, **options):
        cache_name = options.get("cache_name")
        
        if cache_name:
            # Clear specific cache
            from django.core.cache import caches
            try:
                specific_cache = caches[cache_name]
                specific_cache.clear()
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully cleared cache: {cache_name}")
                )
            except KeyError:
                self.stdout.write(
                    self.style.ERROR(f"Cache '{cache_name}' not found in CACHES settings")
                )
        else:
            # Clear all caches
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Successfully cleared default cache"))
            
            # Clear other caches if they exist
            if hasattr(settings, "CACHES"):
                for cache_key in settings.CACHES.keys():
                    if cache_key != "default":
                        try:
                            from django.core.cache import caches
                            caches[cache_key].clear()
                            self.stdout.write(
                                self.style.SUCCESS(f"Successfully cleared cache: {cache_key}")
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not clear cache '{cache_key}': {e}")
                            )
