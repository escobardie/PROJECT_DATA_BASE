from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.dispositivo.models import Dispositivo


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    """
    Administración del catálogo comercial de dispositivos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "nombre_comercial",
        "modelo",
        "precio_mercado",
        "costo",
        "margen",
        "is_active",
        "created_at",
    )

    list_display_links = (
        "codigo",
        "nombre_comercial",
    )

    # ======================================================
    # BÚSQUEDA
    # ======================================================

    search_fields = (
        "codigo",
        "nombre_comercial",
        "modelo__nombre",
        "modelo__marca__nombre",
    )

    # ======================================================
    # FILTROS
    # ======================================================

    list_filter = (
        "modelo__marca",
        "modelo__tipo_dispositivo",
        "is_active",
        "created_at",
    )

    # ======================================================
    # RELACIONES
    # ======================================================

    autocomplete_fields = (
        "modelo",
    )

    # ======================================================
    # ORDENAMIENTO
    # ======================================================

    ordering = (
        "nombre_comercial",
    )

    # ======================================================
    # PAGINACIÓN
    # ======================================================

    list_per_page = 30

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "margen",
        "created_at",
        "updated_at",
    )

    # ======================================================
    # CAMPOS CALCULADOS
    # ======================================================

    @admin.display(
        description=_("Margen"),
        ordering="precio_mercado",
    )
    def margen(self, obj):
        """
        Calcula margen comercial estimado.
        """

        return obj.precio_mercado - obj.costo

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (
        (
            _("Identificación"),
            {
                "fields": (
                    "codigo",
                    "modelo",
                    "nombre_comercial",
                    "descripcion",
                )
            },
        ),

        (
            _("Información económica"),
            {
                "fields": (
                    "precio_mercado",
                    "costo",
                    "margen",
                )
            },
        ),

        (
            _("Configuración"),
            {
                "fields": (
                    "orden",
                    "is_active",
                )
            },
        ),

        (
            _("Auditoría"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )