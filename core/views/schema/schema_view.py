import sys
import subprocess
from pathlib import Path
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone

# Which apps to include in the diagram:
# APPS = ["company", "dispatch", "exchange"]
APPS = [
    "core",
    "more_admin_filters",
    "django_extensions",
    "dalf",
    "ajax_datatable",
    "exchange",
    "company",
    "attendance",
    "privser",
    "synchronization",
    "paychex",
    "dispatch",
    "frontend",
    "pwa_vehicle",
    "pwa_crwb",
    "pwa_notifications",
]


@staff_member_required
def schema_diagram_view(request):
    """
    Generates ER diagram via django-extensions graph_models and displays the image.

    On the server, Graphviz and Python packages are installed:
    sudo apt-get update && sudo apt-get install -y graphviz
    pip install django-extensions pydot pydotplus
    """
    out_dir = Path(settings.MEDIA_ROOT) / "diagrams"
    out_dir.mkdir(parents=True, exist_ok=True)
    img_path = out_dir / "schema_full.png"

    # Command to generate PNG (with fields). Remove --verbose-names if not needed.
    cmd = [
        sys.executable,
        "manage.py",
        "graph_models",
        *APPS,
        "-g",  # group-models
        "--verbose-names",
        "-o",
        str(img_path),
    ]

    try:
        # cwd=BASE_DIR ensures that manage.py will be found.
        subprocess.run(cmd, check=True, capture_output=True, cwd=settings.BASE_DIR)
    except subprocess.CalledProcessError as e:
        return render(
            request,
            "admin/schema/schema_diagram_error.html",
            {
                "title": "ER Diagram — build failed",
                "cmd": " ".join(cmd),
                "stdout": (e.stdout or b"").decode(errors="ignore"),
                "stderr": (e.stderr or b"").decode(errors="ignore"),
            },
            status=500,
        )

    # bust cache
    img_url = f"{settings.MEDIA_URL}diagrams/schema_full.png?ts={int(timezone.now().timestamp())}"
    return render(
        request,
        "admin/schema/schema_diagram.html",
        {"title": "ER Diagram", "img_url": img_url},
    )
