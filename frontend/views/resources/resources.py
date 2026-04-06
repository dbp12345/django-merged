from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from core.models import Documentation_Page


@login_required
def resources_view(request):
    pages = Documentation_Page.objects.values("title", "slug")

    urls = {
        page["title"]: reverse("front_documentation", kwargs={"slug": page["slug"]})
        for page in pages
    }
    return render(request, "frontend/resources/resources.html", {"urls": urls})
