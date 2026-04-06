from django.contrib import admin
from django import forms
from django.db.models import F, Count, OuterRef, Subquery, IntegerField, Value
from django.db.models.functions import Coalesce
from django.utils.html import format_html
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from core.models import Task, Category, HelpTicket
from pdf_plugin.admin_mixin import PDFGenerateMixin


class TaskInline(admin.TabularInline):
    model = Task
    autocomplete_fields = ("completed_by",)
    # raw_id_fields = ("completed_by",)
    fields = (
        "name",
        "category",
        "quantity",
        "time",
        "completed_by",
        "status",
        "file",
        # "created_at"
    )
    readonly_fields = ("created_at",)
    extra = 0
    show_change_link = True
    ordering = ("-created_at",)


class HelpTicketInline(admin.TabularInline):
    model = HelpTicket

    def get_attached_display(self, obj):
        name, instance = obj.get_attached()
        if not name:
            return "—"
        return name

    get_attached_display.short_description = "Attached"

    # autocomplete_fields = (
    #     "created_by",
    #     "created_for",
    #     "assigned_to",
    # )

    fields = (
        "title",
        "created_for",
        "assigned_to",
        "get_attached_display",
        "status",
        "priority",
        "document_preview",
        "created_by",
        "created_by_admin",
    )
    readonly_fields = (
        "title",
        "created_for",
        "assigned_to",
        "get_attached_display",
        "status",
        "priority",
        "document_preview",
        "created_by",
        "created_by_admin",
    )
    
    def has_add_permission(self, request, obj=None):
        return False

    extra = 0
    show_change_link = True
    can_delete = False
    ordering = ("priority", "-updated_at",)


class CategoryTreeFilter(admin.SimpleListFilter):
    title = "Category (tree)"
    parameter_name = "category_tree"

    def lookups(self, request, model_admin):
        def walk(nodes, prefix=""):
            for n in nodes:
                yield (str(n.pk), f"{prefix}{n.name}")
                yield from walk(n.get_children().order_by("path"), prefix + "— ")

        return [("__none__", "---------")] + list(walk(Category.get_root_nodes().order_by("path")))

    def queryset(self, request, queryset):
        v = self.value()
        if not v:
            return queryset
        if v == "__none__":
            return queryset.filter(category__isnull=True)
        try:
            node = Category.objects.get(pk=v)
        except Category.DoesNotExist:
            return queryset.none()
        descendant_ids = list(node.get_descendants().values_list("pk", flat=True))
        ids = descendant_ids + [node.pk]
        return queryset.filter(category_id__in=ids)


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{"— " * (obj.get_depth() - 1)}{obj.name}'


class TaskForm(forms.ModelForm):
    category = CategoryChoiceField(
        queryset=Category.objects.all().order_by("path"), required=False
    )

    class Meta:
        model = Task
        fields = "__all__"


class TaskStatusFilter(admin.SimpleListFilter):
    title = "Task status"
    parameter_name = "task_status"

    def lookups(self, request, model_admin):
        try:
            choices = dict(Task._meta.get_field("status").choices)
            return [(k, v) for k, v in choices.items()]
        except Exception:
            vals = Task.objects.order_by().values_list("status", flat=True).distinct()
            return [(v, v) for v in vals if v is not None]

    def queryset(self, request, queryset):
        return queryset


@admin.register(Task)
class TaskAdmin(PDFGenerateMixin, admin.ModelAdmin):
    list_per_page = 50
    form = TaskForm

    autocomplete_fields = ("completed_by",)
    # raw_id_fields = ("completed_by",)

    list_display = (
        "name",
        "category",
        "quantity",
        "time",
        "completed_by",
        "status",
        "file",
        "created_at"
    )
    list_filter = (
        CategoryTreeFilter,
        ("completed_by", admin.RelatedOnlyFieldListFilter),
        "status",
    )
    search_fields = (
        "name",
        "notes"
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_display = ("indented_name_with_count",)
    search_fields = ("name",)
    inlines = [
        TaskInline,
        HelpTicketInline
    ]
    list_filter = (
        # TaskStatusFilter, не можем теперь использовать статус, потому что статусы есть и в Task и в Help-тикетах
    )

    class Media:
        css = {"all": ("admin/css/category_admin.css",)}

    def get_queryset(self, request):
        # qs = super().get_queryset(request).order_by("path")
        # # status = request.GET.get("task_status")
        #
        # # считаем только элементы, привязанные непосредственно к категории
        # direct_task_condition = Q(tasks__category=F("pk"))
        # direct_help_condition = Q(help_ticket__category=F("pk"))
        #
        # # if status:
        # #     task_condition = direct_task_condition & Q(tasks__status=status)
        # #     help_condition = direct_help_condition & Q(help_ticket__status=status)
        # # else:
        # #     task_condition = direct_task_condition
        # #     help_condition = direct_help_condition
        #
        # # qs = qs.annotate(
        # #     tasks_count=Count("tasks", filter=task_condition, distinct=True),
        # #     help_count=Count("help_ticket", filter=help_condition, distinct=True),
        # # )
        #
        # qs = qs.annotate(
        #     tasks_count=Count("tasks", filter=direct_task_condition, distinct=True),
        #     help_count=Count("help_ticket", filter=direct_help_condition, distinct=True),
        # ).annotate(
        #     total_count=F('tasks_count') + F('help_count')
        # )
        # return qs

        qs = super().get_queryset(request).order_by("path")

        # Подзапросы, которые возвращают количество записей для категории
        task_subq = (
            Task.objects
            .filter(category=OuterRef("pk"))
            .order_by()
            .values("category")
            .annotate(c=Count("pk"))
            .values("c")
        )
        help_subq = (
            HelpTicket.objects
            .filter(category=OuterRef("pk"))
            .order_by()
            .values("category")
            .annotate(c=Count("pk"))
            .values("c")
        )

        qs = qs.annotate(
            tasks_count=Coalesce(Subquery(task_subq, output_field=IntegerField()), Value(0)),
            help_count=Coalesce(Subquery(help_subq, output_field=IntegerField()), Value(0)),
        ).annotate(
            total_count=F("tasks_count") + F("help_count")
        )

        return qs

    def indented_name_with_count(self, obj):
        # tasks_cnt = getattr(obj, "tasks_count", 0) or 0
        # help_cnt = getattr(obj, "help_count", 0) or 0
        total_count = getattr(obj, "total_count", 0) or 0
        return format_html(
            '<span class="category-name depth-{}">{}</span> <span style="color:#666">({})</span>',
            max(obj.get_depth() - 1, 0),
            obj.name,
            total_count,
        )
        # return format_html(
        #     '<span class="category-name depth-{}">{}</span> <span style="color:#666">({} tasks, {} tickets)</span>',
        #     max(obj.get_depth() - 1, 0),
        #     obj.name,
        #     tasks_cnt,
        #     help_cnt,
        # )

    indented_name_with_count.short_description = "Category (counts)"
    indented_name_with_count.admin_order_field = "total_count"
