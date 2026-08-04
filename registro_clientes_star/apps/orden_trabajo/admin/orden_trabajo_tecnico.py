from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import OrdenTrabajoTecnico


class OrdenTrabajoTecnicoInline(admin.TabularInline):
    """
    Técnicos asignados a una orden de trabajo.
    """

    model = OrdenTrabajoTecnico

    extra = 1

    autocomplete_fields = (
        "tecnico",
    )

    fields = (
        "tecnico",
        "es_principal",
        "observaciones",
    )

    ordering = (
        "-es_principal",
        "tecnico",
    )

    show_change_link = True


@admin.register(OrdenTrabajoTecnico)
class OrdenTrabajoTecnicoAdmin(admin.ModelAdmin):
    """
    Administración de técnicos asignados a órdenes de trabajo.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "orden_trabajo",
        "tecnico",
        "es_principal",
        "created_at",
    )

    list_display_links = (
        "orden_trabajo",
        "tecnico",
    )

    list_filter = (
        "es_principal",
        "orden_trabajo__estado",
        "orden_trabajo__prioridad",
    )

    search_fields = (
        "orden_trabajo__codigo",
        "orden_trabajo__titulo",
        "tecnico__username",
        "tecnico__first_name",
        "tecnico__last_name",
    )

    ordering = (
        "orden_trabajo",
        "-es_principal",
        "tecnico",
    )

    empty_value_display = "-"

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
                "orden_trabajo",
                "tecnico",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "orden_trabajo",
        "tecnico",
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
                    "orden_trabajo",
                    "tecnico",
                    "es_principal",
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