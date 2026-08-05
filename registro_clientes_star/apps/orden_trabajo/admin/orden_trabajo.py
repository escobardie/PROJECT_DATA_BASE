from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
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

        # Sucursal
        "sucursal__nombre",

        # Proyecto
        "proyecto__codigo",
        "proyecto__nombre",

        # Servicio contratado
        "servicio_contratado__codigo",

        # Presupuesto Telecom
        "presupuesto_telecom__codigo",

        # Instalación generada
        "instalacion__codigo",

        # Instalación preexistente relacionada
        "instalacion_relacionada__codigo",

        # Responsable
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
        Indica si la orden generó una instalación.
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
    # INFORMACIÓN DERIVADA
    # ======================================================

    @admin.display(
        description=_("Instalación generada"),
    )
    def instalacion_generada(self, obj):
        """
        Devuelve la instalación generada por esta orden.

        La relación se obtiene de forma inversa desde
        Instalacion.orden_trabajo.
        """

        if not obj or not obj.pk:
            return "-"

        try:
            return obj.instalacion
        except ObjectDoesNotExist:
            return "-"

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
                # Origen
                "sucursal",
                "proyecto",
                "servicio_contratado",
                "presupuesto_telecom",

                # Instalaciones
                "instalacion",
                "instalacion_relacionada",

                # Responsables y trazabilidad
                "responsable",
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
        "instalacion_generada",
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
            _("Origen de la orden"),
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
                    "instalacion_generada",
                    "instalacion_relacionada",
                ),
                "description": _(
                    "La instalación generada es el resultado técnico "
                    "de esta orden. La instalación relacionada es una "
                    "instalación preexistente sobre la cual se ejecuta "
                    "el trabajo."
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