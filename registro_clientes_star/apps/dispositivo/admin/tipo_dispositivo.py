from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.dispositivo.models import TipoDispositivo


@admin.register(TipoDispositivo)
class TipoDispositivoAdmin(admin.ModelAdmin):
    """
    Administración del catálogo de tipos de dispositivos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "nombre",
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
    # CAMPOS DE SOLO LECTURA
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