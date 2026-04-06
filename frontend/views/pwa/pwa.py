from django.shortcuts import render

def pwa_view(request):
    return render(request, "frontend/pwa/pwa.html")
