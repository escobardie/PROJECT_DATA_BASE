from django.contrib import admin

from apps.proyecto.models import Proyecto

from .inlines import ProyectoRequerimientoInline


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    """
    Administración de proyectos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "titulo",
        "sucursal",
        "estado",
        "fecha_planificada_inicio",
        "fecha_planificada_finalizacion",
    )

    list_display_links = (
        "codigo",
        "titulo",
    )

    list_filter = (
        "estado",
        "sucursal",
    )

    search_fields = (
        "codigo",
        "titulo",
        "descripcion",
        "sucursal__nombre",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "sucursal",
    )

    empty_value_display = "-"

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "sucursal",
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
            "Información general",
            {
                "fields": (
                    "codigo",
                    "sucursal",
                    "titulo",
                    "descripcion",
                ),
            },
        ),

        (
            "Clasificación",
            {
                "fields": (
                    "estado",
                ),
            },
        ),

        (
            "Planificación",
            {
                "fields": (
                    (
                        "fecha_planificada_inicio",
                        "fecha_planificada_finalizacion",
                    ),
                ),
            },
        ),

        (
            "Ejecución",
            {
                "fields": (
                    (
                        "fecha_inicio",
                        "fecha_finalizacion",
                    ),
                ),
            },
        ),

        (
            "Observaciones",
            {
                "fields": (
                    "observaciones",
                ),
            },
        ),

        (
            "Auditoría",
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
        ProyectoRequerimientoInline,
    )