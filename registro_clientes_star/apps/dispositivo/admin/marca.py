from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.dispositivo.models import Marca


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    """
    Administración del catálogo de marcas
    de dispositivos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "nombre",
        "sitio_web",
        "orden",
        "is_active",
        "created_at",
    )

    list_display_links = (
        "codigo",
        "nombre",
    )

    # ======================================================
    # BÚSQUEDA
    # ======================================================

    search_fields = (
        "codigo",
        "nombre",
        "descripcion",
        "sitio_web",
    )

    # ======================================================
    # FILTROS
    # ======================================================

    list_filter = (
        "is_active",
        "created_at",
    )

    # ======================================================
    # ORDENAMIENTO
    # ======================================================

    ordering = (
        "orden",
        "nombre",
    )

    # ======================================================
    # PAGINACIÓN
    # ======================================================

    list_per_page = 25

    # ======================================================
    # CAMPOS SOLO LECTURA
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
                    "sitio_web",
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