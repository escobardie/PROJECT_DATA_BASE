from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.proyecto.models import ProyectoDetalle


@admin.register(ProyectoDetalle)
class ProyectoDetalleAdmin(admin.ModelAdmin):
    """
    Administración de los detalles comerciales
    y técnicos de los proyectos.
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
        "mostrar_origen",
        "descripcion",
        "cantidad",
        "unidad",
        "precio_unitario",
        "total",
        "is_active",
    )

    list_display_links = (
        "codigo",
        "descripcion",
    )

    list_filter = (
        "tipo",
        "proyecto__estado",
        "proyecto__sucursal",
        "item_catalogo__categoria",
        "item_catalogo__controla_stock",
        "dispositivo__modelo__marca",
        "is_active",
    )

    search_fields = (
        # Detalle
        "codigo",
        "descripcion",

        # Proyecto
        "proyecto__codigo",
        "proyecto__nombre",

        # Dispositivo
        "dispositivo__codigo",
        "dispositivo__nombre_comercial",
        "dispositivo__modelo__nombre",
        "dispositivo__modelo__marca__nombre",

        # Ítem del catálogo
        "item_catalogo__codigo",
        "item_catalogo__nombre",
        "item_catalogo__descripcion",
        "item_catalogo__categoria__codigo",
        "item_catalogo__categoria__nombre",
    )

    ordering = (
        "proyecto",
        "orden",
        "codigo",
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
        """
        Devuelve el estado del proyecto asociado.
        """

        return obj.proyecto.estado

    @admin.display(
        description=_("Origen"),
    )
    def mostrar_origen(self, obj):
        """
        Devuelve el dispositivo o ítem de catálogo
        asociado al detalle.
        """

        if obj.dispositivo_id:
            return obj.dispositivo

        if obj.item_catalogo_id:
            return obj.item_catalogo

        return "-"

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las relaciones utilizadas
        en el listado del administrador.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "proyecto",
                "proyecto__sucursal",
                "dispositivo",
                "dispositivo__modelo",
                "dispositivo__modelo__marca",
                "item_catalogo",
                "item_catalogo__categoria",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "proyecto",
        "dispositivo",
        "item_catalogo",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "mostrar_origen",
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
                    (
                        "orden",
                        "tipo",
                    ),
                    (
                        "dispositivo",
                        "item_catalogo",
                    ),
                    "mostrar_origen",
                    "descripcion",
                    "is_active",
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