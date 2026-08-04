from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import OrdenTrabajo

from .orden_trabajo_archivo import OrdenTrabajoArchivoInline
from .orden_trabajo_seguimiento import OrdenTrabajoSeguimientoInline
from .orden_trabajo_tecnico import OrdenTrabajoTecnicoInline


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    """
    Administración de las órdenes de trabajo.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "titulo",
        "estado",
        "prioridad",
        "tipo",
        "responsable",
        "proyecto",
        "servicio_contratado",
        "presupuesto_telecom",
        "fecha_programada",
        "mostrar_instalacion",
        "mostrar_facturada",
        "mostrar_cobrada",
    )

    list_display_links = (
        "codigo",
        "titulo",
    )

    list_filter = (
        "estado",
        "prioridad",
        "tipo",
        "responsable",
        "proyecto",
        "servicio_contratado",
        "presupuesto_telecom",
    )

    search_fields = (
        "codigo",
        "titulo",
        "descripcion",
        "sucursal__nombre",
        "proyecto__codigo",
        "proyecto__nombre",
        "servicio_contratado__codigo",
        "presupuesto_telecom__codigo",
        "responsable__username",
        "responsable__first_name",
        "responsable__last_name",
    )

    ordering = (
        "-created_at",
    )


    empty_value_display = "-"

    save_on_top = True
    save_as = True
    list_per_page = 25
    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        boolean=True,
        description=_("Inst."),
    )
    def mostrar_instalacion(self, obj):
        """
        Indica si la orden tiene una instalación asociada.
        """

        return obj.tiene_instalacion

    @admin.display(
        boolean=True,
        description=_("Fact."),
    )
    def mostrar_facturada(self, obj):
        """
        Indica si la orden fue facturada.
        """

        return obj.esta_facturada

    @admin.display(
        boolean=True,
        description=_("Cob."),
    )
    def mostrar_cobrada(self, obj):
        """
        Indica si la orden fue cobrada.
        """

        return obj.esta_cobrada

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las relaciones utilizadas en el listado
        del administrador.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "sucursal",
                "proyecto",
                "responsable",
                "servicio_contratado",
                "presupuesto_telecom",
                "instalacion",
                "instalacion_relacionada",
                "usuario_recepcion_solicitud",
                "usuario_inicio",
                "usuario_finalizacion",
                "usuario_envio_cliente",
                "usuario_aceptacion",
                "usuario_facturacion",
                "usuario_cobro",
            )
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
        "usuario_recepcion_solicitud",
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
            _("Información general"),
            {
                "fields": (
                    "codigo",
                    "titulo",
                    "descripcion",
                ),
            },
        ),
        (
            _("Relaciones"),
            {
                "fields": (
                    (
                        "sucursal",
                        "proyecto",
                    ),
                    (
                        "servicio_contratado",
                        "presupuesto_telecom",
                    ),
                ),
            },
        ),
        (
            _("Clasificación"),
            {
                "fields": (
                    (
                        "tipo",
                        "estado",
                        "prioridad",
                    ),
                ),
            },
        ),
        (
            _("Recepción de la solicitud"),
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
            _("Planificación y ejecución"),
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
            _("Instalaciones"),
            {
                "fields": (
                    "instalacion",
                    "instalacion_relacionada",
                ),
            },
        ),
        (
            _("Envío al cliente"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    (
                        "fecha_envio_cliente",
                        "usuario_envio_cliente",
                    ),
                ),
            },
        ),
        (
            _("Aceptación del cliente"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    (
                        "fecha_aceptacion",
                        "usuario_aceptacion",
                    ),
                ),
            },
        ),
        (
            _("Facturación"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    (
                        "fecha_facturacion",
                        "usuario_facturacion",
                    ),
                ),
            },
        ),
        (
            _("Cobro"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    (
                        "fecha_cobro",
                        "usuario_cobro",
                    ),
                ),
            },
        ),
        (
            _("Observaciones"),
            {
                "fields": (
                    "observaciones",
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
        OrdenTrabajoTecnicoInline,
        OrdenTrabajoSeguimientoInline,
        OrdenTrabajoArchivoInline,
    )

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()