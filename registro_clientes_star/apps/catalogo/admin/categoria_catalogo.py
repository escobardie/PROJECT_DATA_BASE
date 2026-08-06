from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.catalogo.models import (
    CategoriaCatalogo,
    ItemCatalogo,
)


class ItemCatalogoInline(admin.TabularInline):
    """
    Ítems pertenecientes a una categoría del catálogo.
    """

    model = ItemCatalogo

    extra = 1

    fields = (
        "orden",
        "tipo",
        "nombre",
        "unidad",
        "costo",
        "precio_venta",
        "controla_stock",
        "is_active",
    )

    ordering = (
        "orden",
        "nombre",
    )

    show_change_link = True


@admin.register(CategoriaCatalogo)
class CategoriaCatalogoAdmin(admin.ModelAdmin):
    """
    Administración de categorías del catálogo general.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "nombre",
        "orden",
        "cantidad_items",
        "created_at",
        "is_active",
    )

    list_display_links = (
        "codigo",
        "nombre",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "codigo",
        "nombre",
        "descripcion",
        "items__codigo",
        "items__nombre",
    )

    ordering = (
        "orden",
        "nombre",
    )

    empty_value_display = "-"

    save_on_top = True

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Ítems"),
    )
    def cantidad_items(self, obj):
        """
        Devuelve la cantidad de ítems pertenecientes
        a la categoría.
        """

        return obj.items.count()

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
            .prefetch_related(
                "items",
            )
            .distinct()
        )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
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
                    "nombre",
                    "descripcion",
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
    # INLINES
    # ======================================================

    inlines = (
        ItemCatalogoInline,
    )

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()