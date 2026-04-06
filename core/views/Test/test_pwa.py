from django.shortcuts import render
from django.views import View


class PWAView(View):

    def get(self, request):
        return render(request, "admin/pwa/index.html", {})