from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.instalacion.models import InstalacionTecnico


class InstalacionTecnicoInline(admin.TabularInline):
    """
    Técnicos asignados a una instalación.
    """

    model = InstalacionTecnico
    extra = 1

    autocomplete_fields = (
        "usuario",
    )

    fields = (
        "usuario",
        "rol",
        "es_responsable",
        "observaciones",
    )

    ordering = (
        "-es_responsable",
        "usuario",
    )

    show_change_link = True


@admin.register(InstalacionTecnico)
class InstalacionTecnicoAdmin(admin.ModelAdmin):
    """
    Administración de técnicos asignados a instalaciones.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "instalacion",
        "usuario",
        "rol",
        "es_responsable",
        "created_at",
    )

    list_display_links = (
        "instalacion",
        "usuario",
    )

    list_filter = (
        "rol",
        "es_responsable",
        "instalacion__estado",
        "instalacion__prioridad",
    )

    search_fields = (
        "instalacion__codigo",
        "instalacion__orden_trabajo__codigo",
        "instalacion__orden_trabajo__titulo",
        "instalacion__orden_trabajo__servicio_contratado__codigo",
        "instalacion__orden_trabajo__proyecto__codigo",
        "instalacion__orden_trabajo__proyecto__nombre",
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "observaciones",
    )

    ordering = (
        "instalacion",
        "-es_responsable",
        "usuario",
    )

    empty_value_display = "-"
    save_on_top = True
    list_per_page = 25
    show_full_result_count = False

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las relaciones utilizadas en el listado.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "instalacion",
                "instalacion__orden_trabajo",
                "instalacion__orden_trabajo__sucursal",
                "instalacion__orden_trabajo__proyecto",
                "instalacion__orden_trabajo__servicio_contratado",
                "instalacion__orden_trabajo__presupuesto_telecom",
                "usuario",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "instalacion",
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
            _("Asignación"),
            {
                "fields": (
                    "instalacion",
                    "usuario",
                    "rol",
                    "es_responsable",
                ),
            },
        ),
        (
            _("Observaciones"),
            {
                "fields": (
                    "observaciones",
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