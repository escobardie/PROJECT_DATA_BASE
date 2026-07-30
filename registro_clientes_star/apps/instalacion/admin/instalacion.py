from django.contrib import admin

from apps.instalacion.models import Instalacion

from .instalacion_dispositivo import InstalacionDispositivoInline
from .instalacion_tecnico import InstalacionTecnicoInline


@admin.register(Instalacion)
class InstalacionAdmin(admin.ModelAdmin):
    """
    Administración de instalaciones.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "servicio_contratado",
        "estado",
        "prioridad",
        "fecha_programada",
        "responsable",
        "created_at",
        "is_active",
    )

    list_display_links = (
        "codigo",
        "servicio_contratado",
    )

    # ======================================================
    # BÚSQUEDA
    # ======================================================

    search_fields = (
        "codigo",
        "servicio_contratado__codigo",
        "servicio_contratado__nombre_comercial",
    )

    # ======================================================
    # FILTROS
    # ======================================================

    list_filter = (
        "estado",
        "prioridad",
        "fecha_programada",
        "is_active",
    )

    # ======================================================
    # ORDENAMIENTO
    # ======================================================

    ordering = (
        "-fecha_programada",
        "-created_at",
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
                    "servicio_contratado",
                    "estado",
                    "prioridad",
                ),
            },
        ),
        (
            "Planificación",
            {
                "fields": (
                    "fecha_programada",
                    "duracion_estimada",
                ),
            },
        ),
        (
            "Ejecución",
            {
                "fields": (
                    "fecha_inicio",
                    "fecha_finalizacion",
                ),
            },
        ),
        (
            "Conformidad",
            {
                "fields": (
                    "recibido_por",
                    "fecha_conformidad",
                    "observaciones_conformidad",
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
    )

    readonly_fields = (
        "codigo",
    )

    inlines = (
        InstalacionTecnicoInline,
        InstalacionDispositivoInline,
    )

    # ======================================================
    # OPTIMIZACIÓN
    # ======================================================

    autocomplete_fields = (
        "servicio_contratado",
    )

    list_select_related = (
        "servicio_contratado",
    )

    # ======================================================
    # MÉTODOS
    # ======================================================

    @admin.display(
        description="Responsable",
        ordering="tecnicos__usuario",
    )
    def responsable(self, obj):
        """
        Devuelve el técnico responsable de la instalación.
        """

        responsable = (
            obj.tecnicos
            .filter(es_responsable=True)
            .select_related("usuario")
            .first()
        )

        if responsable:
            return responsable.usuario

        return "-"