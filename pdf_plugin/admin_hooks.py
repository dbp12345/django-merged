from .models import PDFTemplate


def pdf_plugin_admin_notice(request):
    if PDFTemplate.objects.exists():
        return None
    return {
        "level": "warning",
        "message": (
            "PDF Plugin is installed but not configured. "
            "Run <code>python manage.py pdf_plugin_install</code> "
            "or add a PDF Template in Admin."
        ),
    }
