from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def cabinet_view(request):
    return render(request, "frontend/cabinet/cabinet.html")
