from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.proyecto.models import ProyectoDetalle


@admin.register(ProyectoDetalle)
class ProyectoDetalleAdmin(admin.ModelAdmin):
    """
    Administración de los detalles de los proyectos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "proyecto",
        "proyecto_estado",
        "orden",
        "tipo",
        "dispositivo",
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
        "tipo",
        "proyecto__estado",
        "proyecto__sucursal",
        "dispositivo__modelo__marca",
    )

    search_fields = (
        "codigo",
        "descripcion",
        "proyecto__codigo",
        "proyecto__nombre",
        "dispositivo__codigo",
        "dispositivo__nombre_comercial",
        "dispositivo__modelo__nombre",
    )

    ordering = (
        "proyecto",
        "orden",
    )

    list_select_related = (
        "proyecto",
        "dispositivo",
        "dispositivo__modelo",
        "dispositivo__modelo__marca",
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
        ordering="proyecto__estado",
    )
    def proyecto_estado(self, obj):
        return obj.proyecto.estado

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las consultas del administrador.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "proyecto",
                "dispositivo",
                "dispositivo__modelo",
                "dispositivo__modelo__marca",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "proyecto",
        "dispositivo",
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
                    "proyecto",
                    "orden",
                    "tipo",
                    "dispositivo",
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
                    "total",
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