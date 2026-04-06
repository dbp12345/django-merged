from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.utils.cache import patch_cache_control
from django.views.decorators.csrf import csrf_exempt
import json

from company.models import Course, TrainingClass
from core.models import Saved_Chart


@staff_member_required
def metrics_charts(request):
    title = "Metrics and Charts"
    saved_charts = Saved_Chart.objects.all().order_by("-dashboard", "-display_order", "-created_at")

    return render(request, "admin/charts/layout.html", {
        "dashboard": False,
        "title": title,
        "saved_charts": saved_charts,
        "filter_chart": None
    })

@staff_member_required
def metrics_charts_dashboard(request):
    saved_charts = Saved_Chart.objects.filter(dashboard=True).order_by("-display_order", "-created_at")

    return render(request, "admin/charts/chart_content.html", {
        "dashboard": True,
        "saved_charts": saved_charts,
        "filter_chart": None
    })


@staff_member_required
def metrics_charts_settings(request, chart_id=None):
    title = "Metrics and Charts Settings"
    courses = Course.objects.values("id", "training_type__name")

    years = (
        TrainingClass.objects
        .filter(date__year__gte=2010, date__year__lte=2030)
        .exclude(date__isnull=True)
        .dates("date", "year")
        .values_list("date__year", flat=True)
    )
    available_years = sorted(set(years))

    chart = None
    if chart_id:
        chart = Saved_Chart.objects.filter(id=chart_id).first()

    return render(request, "admin/charts/layout.html", {
        "dashboard": False,
        "title": title,
        "courses": courses,
        "available_years": available_years,
        "selected_course": str(chart.course_id) if chart else "",
        "selected_year_from": str(chart.year_from) if chart else "",
        "selected_year_to": str(chart.year_to) if chart else "",
        "selected_chart_type": str(chart.chart_type) if chart else "bar",
        "selected_dashboard": chart.dashboard if chart else False,
        "saved_chart": chart,
    })


@cache_page(60 * 60 * 2)  # Cache 2 hours
def metrics_charts_data(request):
    course_id = request.GET.get("course_id")
    year_from = request.GET.get("year_from")
    year_to = request.GET.get("year_to")
    data_type = request.GET.get("data_type")

    course_id = int(course_id) if course_id and course_id.isdigit() else None
    year_from = int(year_from) if year_from and year_from.isdigit() else None
    year_to = int(year_to) if year_to and year_to.isdigit() else None

    query = TrainingClass.objects.annotate(
        year=ExtractYear("date"),
        month=ExtractMonth("date")
    )

    if course_id:
        query = query.filter(course_id=course_id)

    if year_from:
        query = query.filter(year__gte=int(year_from))
    if year_to:
        query = query.filter(year__lte=int(year_to))

    data = (
        query.values("year", "month")
        .annotate(count=Count("id"))
        .order_by("year", "month")
    )

    years = sorted(set(entry["year"] for entry in data if entry["year"]))
    data_by_year = {year: [0] * 15 for year in years}
    cumulative_data_by_year = {year: [0] * 15 for year in years}

    for entry in data:
        year, month, count = entry["year"], entry["month"], entry["count"]
        if year not in data_by_year:
            continue

        # Заполняем данные для текущего года со сдвигом на 3 месяца
        shifted_index = (month + 2) % 15
        data_by_year[year][shifted_index] = count

        # Если это октябрь, ноябрь или декабрь, добавляем их в начало следующего года
        if month in [10, 11, 12]:
            next_year = year + 1
            if next_year in data_by_year:
                next_year_index = month - 10  # 10 -> 0, 11 -> 1, 12 -> 2
                data_by_year[next_year][next_year_index] = count


        # Формируем накопительные данные
        for year in cumulative_data_by_year:
            cumulative_sum = 0
            for i in range(15):
                cumulative_sum += data_by_year[year][i]  # Накопительное суммирование
                cumulative_data_by_year[year][i] = cumulative_sum

    response = None
    if data_type == "data":
        for year in data_by_year:
            data_by_year[year] = data_by_year[year][:-2]
        response = JsonResponse(data_by_year)
    if data_type == "cumulative":
        for year in cumulative_data_by_year:
            cumulative_data_by_year[year] = cumulative_data_by_year[year][:-2]
        response = JsonResponse(cumulative_data_by_year)

    patch_cache_control(response, public=True, max_age=60 * 60 * 2)

    return response


@csrf_exempt
def save_chart(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            chart_id = data.get("chart_id")
            course_id = data.get("course_id") or None
            name = data.get("name")
            year_from = data.get("year_from") or None
            year_to = data.get("year_to") or None
            chart_type = data.get("chart_type")
            data_type = data.get("data_type")
            display_order = data.get("display_order", 0)
            dashboard = bool(data.get("dashboard", False))

            if not name:
                course = Course.objects.filter(id=course_id).first() if course_id else None
                course_name = course.training_type.name if course else "All Courses"
                name = f"{course_name} ({year_from or '..'} - {year_to or '..'})"

            if chart_id:
                saved_chart = Saved_Chart.objects.filter(id=chart_id).first()
                if saved_chart:
                    saved_chart.name = name
                    saved_chart.course_id = course_id
                    saved_chart.year_from = year_from
                    saved_chart.year_to = year_to
                    saved_chart.chart_type = chart_type
                    saved_chart.data_type = data_type
                    saved_chart.display_order = display_order
                    saved_chart.dashboard = dashboard
                    saved_chart.save()
                    return JsonResponse({"status": "success", "chart_id": saved_chart.id, "redirect_url": reverse("metrics_charts")})
                else:
                    return JsonResponse({"status": "error", "message": "Chart not found"}, status=404)
            else:
                saved_chart = Saved_Chart.objects.create(
                    name=name,
                    course_id=course_id,
                    year_from=year_from,
                    year_to=year_to,
                    chart_type=chart_type,
                    data_type=data_type,
                    display_order=display_order,
                    dashboard=dashboard
                )
                return JsonResponse({"status": "success", "chart_id": saved_chart.id, "redirect_url": reverse("metrics_charts")})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@staff_member_required
def delete_chart(request, chart_id):
    chart = get_object_or_404(Saved_Chart, id=chart_id)
    chart.delete()
    return redirect("metrics_charts")
