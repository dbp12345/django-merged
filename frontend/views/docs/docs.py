from django.shortcuts import render, get_object_or_404
# from django.contrib.auth.decorators import login_required
from django.urls import reverse

from core.models import Documentation_Page


# @login_required
def docs_view(request, slug):
    page = get_object_or_404(Documentation_Page, slug=slug)
    pages = Documentation_Page.objects.values("title", "slug")

    urls = {
        page["title"]: reverse("front_documentation", kwargs={"slug": page["slug"]})
        for page in pages
    }

    return render(request, "frontend/docs/docs.html", {"title": page.title, "page": page, "urls": urls})
