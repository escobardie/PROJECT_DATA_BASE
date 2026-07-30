from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.dispositivo.models import ModeloDispositivo


@admin.register(ModeloDispositivo)
class ModeloDispositivoAdmin(admin.ModelAdmin):
    """
    Administración del catálogo de modelos de dispositivos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "nombre",
        "marca",
        "tipo_dispositivo",
        "codigo_fabricante",
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
        "codigo_fabricante",
        "marca__nombre",
        "tipo_dispositivo__nombre",
    )

    # ======================================================
    # FILTROS
    # ======================================================

    list_filter = (
        "marca",
        "tipo_dispositivo",
        "is_active",
        "created_at",
    )

    # ======================================================
    # RELACIONES
    # ======================================================

    autocomplete_fields = (
        "marca",
        "tipo_dispositivo",
    )

    # ======================================================
    # ORDENAMIENTO
    # ======================================================

    ordering = (
        "marca__nombre",
        "nombre",
    )

    # ======================================================
    # PAGINACIÓN
    # ======================================================

    list_per_page = 30

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
            _("Identificación"),
            {
                "fields": (
                    "codigo",
                    "marca",
                    "tipo_dispositivo",
                    "nombre",
                    "codigo_fabricante",
                )
            },
        ),

        (
            _("Información técnica"),
            {
                "fields": (
                    "descripcion",
                    "especificaciones",
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