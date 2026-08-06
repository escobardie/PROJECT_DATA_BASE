from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.catalogo.models import ItemCatalogo


@admin.register(ItemCatalogo)
class ItemCatalogoAdmin(admin.ModelAdmin):
    """
    Administración de ítems valorizados del catálogo general.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "nombre",
        "categoria",
        "tipo",
        "unidad",
        "costo",
        "precio_venta",
        "mostrar_margen_bruto",
        "mostrar_porcentaje_margen",
        "controla_stock",
        "orden",
        "is_active",
    )

    list_display_links = (
        "codigo",
        "nombre",
    )

    list_filter = (
        "tipo",
        "categoria",
        "unidad",
        "controla_stock",
        "is_active",
    )

    search_fields = (
        "codigo",
        "nombre",
        "descripcion",
        "categoria__nombre",
    )

    ordering = (
        "categoria",
        "orden",
        "nombre",
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
        description=_("Margen bruto"),
    )
    def mostrar_margen_bruto(self, obj):
        """
        Devuelve la diferencia entre el precio
        de venta y el costo.
        """

        return obj.margen_bruto

    @admin.display(
        description=_("Margen %"),
    )
    def mostrar_porcentaje_margen(self, obj):
        """
        Devuelve el porcentaje de margen calculado
        sobre el costo.
        """

        return f"{obj.porcentaje_margen:.2f} %"

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
                "categoria",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "categoria",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "mostrar_margen_bruto",
        "mostrar_porcentaje_margen",
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
                    "categoria",
                    "tipo",
                    "nombre",
                    "descripcion",
                    "unidad",
                ),
            },
        ),
        (
            _("Información económica"),
            {
                "fields": (
                    (
                        "costo",
                        "precio_venta",
                    ),
                    (
                        "mostrar_margen_bruto",
                        "mostrar_porcentaje_margen",
                    ),
                ),
            },
        ),
        (
            _("Inventario"),
            {
                "fields": (
                    "controla_stock",
                ),
                "description": _(
                    "El control de stock solamente puede utilizarse "
                    "en materiales e insumos."
                ),
            },
        ),
        (
            _("Organización"),
            {
                "fields": (
                    "orden",
                    "is_active",
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