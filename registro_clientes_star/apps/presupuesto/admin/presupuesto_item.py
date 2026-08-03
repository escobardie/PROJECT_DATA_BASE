from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.presupuesto.models import PresupuestoItem


@admin.register(PresupuestoItem)
class PresupuestoItemAdmin(admin.ModelAdmin):
    """
    Administración de los conceptos comerciales de los presupuestos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "presupuesto",
        "presupuesto_estado",
        "orden",
        "descripcion",
        "cantidad",
        "unidad",
        "precio_unitario",
        "total",
    )

    list_display_links = (
        "codigo",
        "descripcion",
    )

    list_filter = (
        "unidad",
        "presupuesto__estado",
        "presupuesto__sucursal",
    )

    search_fields = (
        "codigo",
        "descripcion",
        "presupuesto__codigo",
        "presupuesto__titulo",
    )

    ordering = (
        "presupuesto",
        "orden",
    )

    list_select_related = (
        "presupuesto",
    )

    empty_value_display = "-"

    save_on_top = True

    save_as = True

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Estado"),
        ordering="presupuesto__estado",
    )
    def presupuesto_estado(self, obj):
        return obj.presupuesto.estado

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las consultas utilizadas por el administrador.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "presupuesto",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "presupuesto",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "subtotal",
        "total",
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
                    "codigo",
                    "presupuesto",
                    "orden",
                    "descripcion",
                ),
            },
        ),

        (
            _("Cantidades"),
            {
                "fields": (
                    (
                        "cantidad",
                        "unidad",
                    ),
                ),
            },
        ),

        (
            _("Importes"),
            {
                "fields": (
                    (
                        "precio_unitario",
                        "descuento_importe",
                    ),
                    (
                        "impuestos_importe",
                        "subtotal",
                    ),
                    (
                        "total",
                    ),
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