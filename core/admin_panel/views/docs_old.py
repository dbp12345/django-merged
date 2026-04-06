from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
import markdown
import os
from django.conf import settings
from django.urls import reverse


@staff_member_required
def docs_view(request, filename=None):
    if filename is None:
        return redirect("docs_old", filename="manual")

    file_list = os.listdir(settings.MANUALS_DIR)

    md_files_without_extension = [file[:-3] for file in file_list if file.endswith(".md")]
    urls = {}
    for filen in md_files_without_extension:
        urls[filen] = reverse("docs_old", kwargs={"filename": filen})

    markdown_file = os.path.join(settings.MANUALS_DIR, f"{filename}.md")

    if not os.path.exists(markdown_file):
        return redirect("docs_old", filename="manual")

    with open(markdown_file, "r") as f:
        md_content = f.read()

    context = {
        "title": "Docs",
        "html_content": markdown.markdown(md_content),
        "urls": urls
    }
    return render(request, "docs_old.html", context)
