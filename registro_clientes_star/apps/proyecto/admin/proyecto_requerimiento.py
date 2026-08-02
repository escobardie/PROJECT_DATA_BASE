from django.contrib import admin

from apps.proyecto.models import ProyectoRequerimiento


@admin.register(ProyectoRequerimiento)
class ProyectoRequerimientoAdmin(admin.ModelAdmin):
    """
    Administración de los requerimientos técnicos de los proyectos.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "proyecto",
        "dispositivo",
        "cantidad",
        "created_at",
    )

    list_display_links = (
        "codigo",
        "dispositivo",
    )

    list_filter = (
        "proyecto__sucursal",
        "proyecto",
    )

    search_fields = (
        "codigo",
        "proyecto__codigo",
        "proyecto__titulo",
        "dispositivo__codigo",
        "dispositivo__nombre",
        "descripcion",
    )

    ordering = (
        "proyecto",
        "dispositivo",
        "codigo",
    )

    # date_hierarchy = "created_at"

    list_select_related = (
        "proyecto",
        "dispositivo",
    )

    empty_value_display = "-"

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
                    "proyecto",
                    "dispositivo",
                    "cantidad",
                    "descripcion",
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

