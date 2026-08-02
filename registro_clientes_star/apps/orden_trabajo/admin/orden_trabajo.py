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
        "tipo",
        "estado",
        "prioridad",
        "fecha_programada",
        "sucursal",
        "responsable",
        "tiene_instalacion",
        "esta_finalizada",
    )

    list_filter = (
        "tipo",
        "estado",
        "prioridad",
        "responsable",
        "fecha_programada",
    )

    search_fields = (
        "codigo",
        "titulo",
        "descripcion",
        "sucursal__nombre",
        "proyecto__titulo",
        "servicio_contratado__nombre_comercial",
        "responsable__username",
        "responsable__first_name",
        "responsable__last_name",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "sucursal",
        "proyecto",
        "servicio_contratado",
        "presupuesto_telecom",
        "instalacion",
        "instalacion_relacionada",
        "responsable",
    )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "sucursal",
        "proyecto",
        "servicio_contratado",
        "presupuesto_telecom",
        "instalacion",
        "instalacion_relacionada",
        "responsable",
        "usuario_inicio",
        "usuario_finalizacion",
        "usuario_envio_cliente",
        "usuario_aceptacion",
        "usuario_facturacion",
        "usuario_cobro",
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
                    "titulo",
                    "descripcion",
                ),
            },
        ),

        (
            "Origen de la orden",
            {
                "fields": (
                    "sucursal",
                    "proyecto",
                    "servicio_contratado",
                    "presupuesto_telecom",
                    "instalacion",
                    "instalacion_relacionada",
                ),
            },
        ),

        (
            "Clasificación",
            {
                "fields": (
                    "tipo",
                    "estado",
                    "prioridad",
                ),
            },
        ),
        (
            "Recepción de la solicitud",
            {
                "fields": (
                    (
                        "fecha_recepcion_solicitud",
                        "usuario_recepcion_solicitud",
                    ),
                ),
            },
        ),

        (
            "Planificación",
            {
                "fields": (
                    "responsable",
                    "fecha_programada",
                    (
                        "fecha_inicio",
                        "usuario_inicio",
                    ),
                    (
                        "fecha_finalizacion",
                        "usuario_finalizacion",
                    ),
                ),
            },
        ),

        (
            "Trazabilidad",
            {
                "fields": (
                    (
                        "fecha_envio_cliente",
                        "usuario_envio_cliente",
                    ),
                    (
                        "fecha_aceptacion",
                        "usuario_aceptacion",
                    ),
                    (
                        "fecha_facturacion",
                        "usuario_facturacion",
                    ),
                    (
                        "fecha_cobro",
                        "usuario_cobro",
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
        OrdenTrabajoTecnicoInline,
        OrdenTrabajoSeguimientoInline,
        OrdenTrabajoArchivoInline,
    )