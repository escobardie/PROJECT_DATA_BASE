from django.contrib import admin
from django.db.models import Count, Prefetch
from django.utils.translation import gettext_lazy as _

from apps.instalacion.models import (
    Instalacion,
    InstalacionTecnico,
)

from .instalacion_dispositivo import InstalacionDispositivoInline
from .instalacion_tecnico import InstalacionTecnicoInline


@admin.register(Instalacion)
class InstalacionAdmin(admin.ModelAdmin):
    """
    Administración de instalaciones.

    Una instalación representa el resultado técnico
    de una orden de trabajo.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "orden_trabajo",
        "mostrar_origen",
        "estado",
        "prioridad",
        "fecha_programada",
        "responsable",
        "cantidad_dispositivos",
        "mostrar_vencida",
        "created_at",
        "is_active",
    )

    list_display_links = (
        "codigo",
        "orden_trabajo",
    )

    list_filter = (
        "estado",
        "prioridad",
        "fecha_programada",
        "orden_trabajo__tipo",
        "orden_trabajo__estado",
        "is_active",
    )

    search_fields = (
        "codigo",

        # Orden de trabajo
        "orden_trabajo__codigo",
        "orden_trabajo__titulo",
        "orden_trabajo__descripcion",

        # Sucursal
        "orden_trabajo__sucursal__nombre",
        "orden_trabajo__sucursal__cuenta_cliente__nombre",

        # Proyecto
        "orden_trabajo__proyecto__codigo",
        "orden_trabajo__proyecto__nombre",

        # Servicio contratado
        "orden_trabajo__servicio_contratado__codigo",

        # Presupuesto Telecom
        "orden_trabajo__presupuesto_telecom__codigo",

        # Técnicos
        "tecnicos__usuario__username",
        "tecnicos__usuario__first_name",
        "tecnicos__usuario__last_name",

        # Dispositivos físicos instalados
        "dispositivos__codigo",
        "dispositivos__numero_serie",
        "dispositivos__direccion_mac",
        "dispositivos__direccion_ip",
        "dispositivos__ubicacion",

        # Producto del catálogo
        "dispositivos__dispositivo__codigo",
        "dispositivos__dispositivo__nombre_comercial",
        "dispositivos__dispositivo__modelo__nombre",
        "dispositivos__dispositivo__modelo__marca__nombre",
    )

    ordering = (
        "-fecha_programada",
        "-created_at",
    )

    empty_value_display = "-"

    save_on_top = True

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Origen"),
    )
    def mostrar_origen(self, obj):
        """
        Muestra el origen principal de la orden de trabajo.
        """

        orden = obj.orden_trabajo

        if orden.proyecto_id:
            return orden.proyecto

        if orden.servicio_contratado_id:
            return orden.servicio_contratado

        if orden.presupuesto_telecom_id:
            return orden.presupuesto_telecom

        if orden.sucursal_id:
            return orden.sucursal

        return "-"

    @admin.display(
        description=_("Responsable"),
    )
    def responsable(self, obj):
        """
        Devuelve el técnico responsable principal
        de la instalación.
        """

        responsables = getattr(
            obj,
            "_responsables_prefetched",
            (),
        )

        if responsables:
            return responsables[0].usuario

        return "-"

    @admin.display(
        description=_("Dispositivos"),
        ordering="_cantidad_dispositivos",
    )
    def cantidad_dispositivos(self, obj):
        """
        Devuelve la cantidad de equipos físicos registrados.
        """

        return obj._cantidad_dispositivos

    @admin.display(
        boolean=True,
        description=_("Vencida"),
    )
    def mostrar_vencida(self, obj):
        """
        Indica si la instalación está vencida.
        """

        return obj.esta_vencida

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las relaciones y valores utilizados
        en el listado del administrador.
        """

        responsables = (
            InstalacionTecnico.objects
            .filter(
                es_responsable=True,
            )
            .select_related(
                "usuario",
            )
        )

        return (
            super()
            .get_queryset(request)
            .select_related(
                "orden_trabajo",
                "orden_trabajo__sucursal",
                "orden_trabajo__sucursal__cuenta_cliente",
                "orden_trabajo__proyecto",
                "orden_trabajo__servicio_contratado",
                "orden_trabajo__presupuesto_telecom",
                "orden_trabajo__responsable",
            )
            .prefetch_related(
                Prefetch(
                    "tecnicos",
                    queryset=responsables,
                    to_attr="_responsables_prefetched",
                ),
            )
            .annotate(
                _cantidad_dispositivos=Count(
                    "dispositivos",
                    distinct=True,
                ),
            )
            .distinct()
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "orden_trabajo",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "mostrar_proyecto",
        "mostrar_sucursal",
        "mostrar_servicio_contratado",
        "mostrar_presupuesto_telecom",
        "created_at",
        "updated_at",
    )

    # ======================================================
    # INFORMACIÓN DERIVADA
    # ======================================================

    @admin.display(
        description=_("Proyecto"),
    )
    def mostrar_proyecto(self, obj):
        if not obj.pk:
            return "-"

        return obj.proyecto or "-"

    @admin.display(
        description=_("Sucursal"),
    )
    def mostrar_sucursal(self, obj):
        if not obj.pk:
            return "-"

        return obj.sucursal or "-"

    @admin.display(
        description=_("Servicio contratado"),
    )
    def mostrar_servicio_contratado(self, obj):
        if not obj.pk:
            return "-"

        return obj.servicio_contratado or "-"

    @admin.display(
        description=_("Presupuesto Telecom"),
    )
    def mostrar_presupuesto_telecom(self, obj):
        if not obj.pk:
            return "-"

        return obj.presupuesto_telecom or "-"

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (
        (
            _("Información general"),
            {
                "fields": (
                    "codigo",
                    "orden_trabajo",
                    (
                        "estado",
                        "prioridad",
                    ),
                    "is_active",
                ),
            },
        ),
        (
            _("Origen de la orden"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "mostrar_proyecto",
                    "mostrar_sucursal",
                    "mostrar_servicio_contratado",
                    "mostrar_presupuesto_telecom",
                ),
            },
        ),
        (
            _("Planificación"),
            {
                "fields": (
                    (
                        "fecha_programada",
                        "duracion_estimada",
                    ),
                ),
            },
        ),
        (
            _("Ejecución"),
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
            _("Conformidad"),
            {
                "fields": (
                    "recibido_por",
                    "fecha_conformidad",
                    "observaciones_conformidad",
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
        InstalacionTecnicoInline,
        InstalacionDispositivoInline,
    )

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()