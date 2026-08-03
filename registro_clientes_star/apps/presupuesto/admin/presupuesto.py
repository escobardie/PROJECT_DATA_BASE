from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.presupuesto.models import Presupuesto

from .inlines import PresupuestoItemInline


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    """
    Administración de presupuestos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "titulo",
        "sucursal",
        "vendedor",
        "estado",
        "fecha_emision",
        "fecha_vencimiento",
        "moneda",
        "total",
    )

    list_display_links = (
        "codigo",
        "titulo",
    )

    list_filter = (
        "estado",
        "moneda",
        "vendedor",
        "sucursal",
    )

    search_fields = (
        "codigo",
        "titulo",
        "descripcion",
        "sucursal__nombre",
        "sucursal__cuenta_cliente__nombre",
        "vendedor__username",
        "vendedor__first_name",
        "vendedor__last_name",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "fecha_emision"

    list_select_related = (
        "sucursal",
        "vendedor",
    )

    empty_value_display = "-"

    save_on_top = True

    save_as = True

    list_per_page = 25

    show_full_result_count = False

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
                "sucursal",
                "vendedor",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "sucursal",
        "vendedor",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "subtotal",
        "descuento_total",
        "impuestos",
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
                    "sucursal",
                    "vendedor",
                    "titulo",
                    "descripcion",
                ),
            },
        ),

        (
            _("Condiciones comerciales"),
            {
                "fields": (
                    "moneda",
                ),
            },
        ),

        (
            _("Fechas"),
            {
                "fields": (
                    (
                        "fecha_emision",
                        "dias_validez",
                        "fecha_vencimiento",
                    ),
                ),
            },
        ),

        (
            _("Estado"),
            {
                "fields": (
                    "estado",
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
            _("Resumen económico"),
            {
                "fields": (
                    (
                        "subtotal",
                        "descuento_total",
                    ),
                    (
                        "impuestos",
                        "total",
                    ),
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
    # INLINES
    # ======================================================

    inlines = (
        PresupuestoItemInline,
    )

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()