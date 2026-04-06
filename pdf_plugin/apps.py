from django.apps import AppConfig


class PdfPluginConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pdf_plugin"
    verbose_name = "PDF Plugin"

    def ready(self):
        from django.contrib import admin
        from .admin_hooks import pdf_plugin_admin_notice

        original_each_context = admin.site.each_context

        def wrapped_each_context(request):
            ctx = original_each_context(request)
            notice = pdf_plugin_admin_notice(request)
            if notice:
                ctx.setdefault("messages", [])
                ctx["messages"].append(notice)
            return ctx

        admin.site.each_context = wrapped_each_context
