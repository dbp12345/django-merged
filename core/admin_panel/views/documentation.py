from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from core.models import Documentation_Page
@staff_member_required
def documentation_view(request, slug):
    page = get_object_or_404(Documentation_Page, slug=slug)
    pages = Documentation_Page.objects.values("title", "slug")

    urls = {
        page["title"]: reverse("documentation", kwargs={"slug": page["slug"]})
        for page in pages
    }

    return render(request, "documentation.html", {"title": page.title, "page": page, "urls": urls})