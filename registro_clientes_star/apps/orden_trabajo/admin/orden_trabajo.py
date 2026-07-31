from django.contrib import admin


from apps.orden_trabajo.models import OrdenTrabajo


from .orden_trabajo_tecnico import OrdenTrabajoTecnicoInline
from .orden_trabajo_seguimiento import OrdenTrabajoSeguimientoInline
from .orden_trabajo_archivo import OrdenTrabajoArchivoInline



@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    """
    Administración de órdenes de trabajo.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "titulo",
        "proyecto",
        "tipo",
        "estado",
        "prioridad",
        "fecha_programada",
        "responsable",
        "created_at",
    )


    search_fields = (
        "codigo",
        "titulo",
        "proyecto__nombre",
        "responsable__username",
    )


    list_filter = (
        "tipo",
        "estado",
        "prioridad",
        "fecha_programada",
    )


    ordering = (
        "-created_at",
    )


    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "proyecto",
        "instalacion",
        "responsable",
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
                    "titulo",
                    "descripcion",
                    "proyecto",
                    "instalacion",
                )
            },
        ),


        (
            "Clasificación",
            {
                "fields": (
                    "tipo",
                    "estado",
                    "prioridad",
                )
            },
        ),


        (
            "Responsable y fechas",
            {
                "fields": (
                    "responsable",
                    "fecha_programada",
                    "fecha_inicio",
                    "fecha_finalizacion",
                )
            },
        ),


        (
            "Observaciones",
            {
                "fields": (
                    "observaciones",
                )
            },
        ),

        (
            "Auditoría",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),

    )


    readonly_fields = (
        "codigo",
        "created_at",
        "updated_at",
    )


    # ======================================================
    # INLINES
    # ======================================================

    inlines = (
        OrdenTrabajoTecnicoInline,
        OrdenTrabajoSeguimientoInline,
        OrdenTrabajoArchivoInline,
    )