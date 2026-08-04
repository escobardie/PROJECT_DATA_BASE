from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import OrdenTrabajoArchivo


class OrdenTrabajoArchivoInline(admin.TabularInline):
    """
    Archivos asociados a una orden de trabajo.
    """

    model = OrdenTrabajoArchivo

    extra = 1

    autocomplete_fields = (
        "usuario",
    )

    fields = (
        "usuario",
        "archivo",
        "descripcion",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    show_change_link = True


@admin.register(OrdenTrabajoArchivo)
class OrdenTrabajoArchivoAdmin(admin.ModelAdmin):
    """
    Administración de archivos asociados a órdenes de trabajo.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "orden_trabajo",
        "usuario",
        "nombre_archivo",
        "descripcion",
        "created_at",
    )

    list_display_links = (
        "orden_trabajo",
        "nombre_archivo",
    )

    list_filter = (
        "created_at",
        "usuario",
        "orden_trabajo__estado",
    )

    search_fields = (
        "orden_trabajo__codigo",
        "orden_trabajo__titulo",
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "archivo",
        "descripcion",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "created_at"

    empty_value_display = "-"

    save_on_top = True

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Archivo"),
        ordering="archivo",
    )
    def nombre_archivo(self, obj):
        """
        Muestra solamente el nombre del archivo.
        """

        if not obj.archivo:
            return "-"

        return obj.archivo.name.rsplit("/", 1)[-1]

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las consultas utilizadas en el listado.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "orden_trabajo",
                "usuario",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "orden_trabajo",
        "usuario",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (
        (
            _("Información general"),
            {
                "fields": (
                    "orden_trabajo",
                    "usuario",
                    "archivo",
                    "descripcion",
                ),
            },
        ),
        (
            _("Auditoría"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()