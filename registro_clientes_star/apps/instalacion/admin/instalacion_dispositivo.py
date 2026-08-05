from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.instalacion.models import InstalacionDispositivo


class InstalacionDispositivoInline(admin.TabularInline):
    """
    Dispositivos físicos asociados a una instalación.
    """

    model = InstalacionDispositivo

    extra = 1

    autocomplete_fields = (
        "dispositivo",
    )

    fields = (
        "dispositivo",
        "numero_serie",
        "direccion_mac",
        "direccion_ip",
        "ubicacion",
        "estado",
    )

    ordering = (
        "ubicacion",
        "codigo",
    )

    show_change_link = True


@admin.register(InstalacionDispositivo)
class InstalacionDispositivoAdmin(admin.ModelAdmin):
    """
    Administración de dispositivos físicos instalados.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "instalacion",
        "orden_trabajo",
        "dispositivo",
        "marca",
        "modelo",
        "numero_serie",
        "direccion_mac",
        "direccion_ip",
        "ubicacion",
        "estado",
        "mostrar_credenciales",
        "is_active",
    )

    list_display_links = (
        "codigo",
        "dispositivo",
    )

    list_filter = (
        "estado",
        "is_active",
        "dispositivo__modelo__marca",
        "dispositivo__modelo__tipo_dispositivo",
        "instalacion__estado",
        "instalacion__prioridad",
        "instalacion__orden_trabajo__tipo",
        "instalacion__orden_trabajo__estado",
    )

    search_fields = (
        "codigo",
        "numero_serie",
        "direccion_mac",
        "direccion_ip",
        "ubicacion",

        # Dispositivo del catálogo
        "dispositivo__codigo",
        "dispositivo__nombre_comercial",
        "dispositivo__modelo__nombre",
        "dispositivo__modelo__marca__nombre",
        "dispositivo__modelo__tipo_dispositivo__nombre",

        # Instalación
        "instalacion__codigo",

        # Orden de trabajo
        "instalacion__orden_trabajo__codigo",
        "instalacion__orden_trabajo__titulo",
        "instalacion__orden_trabajo__descripcion",

        # Sucursal
        "instalacion__orden_trabajo__sucursal__nombre",
        "instalacion__orden_trabajo__sucursal__cuenta_cliente__nombre",

        # Proyecto
        "instalacion__orden_trabajo__proyecto__codigo",
        "instalacion__orden_trabajo__proyecto__nombre",

        # Servicio contratado
        "instalacion__orden_trabajo__servicio_contratado__codigo",

        # Presupuesto Telecom
        "instalacion__orden_trabajo__presupuesto_telecom__codigo",
    )

    ordering = (
        "instalacion",
        "ubicacion",
        "codigo",
    )

    empty_value_display = "-"

    save_on_top = True

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Orden de trabajo"),
        ordering="instalacion__orden_trabajo__codigo",
    )
    def orden_trabajo(self, obj):
        """
        Devuelve la orden de trabajo que originó
        la instalación.
        """

        return obj.instalacion.orden_trabajo

    @admin.display(
        description=_("Marca"),
        ordering="dispositivo__modelo__marca__nombre",
    )
    def marca(self, obj):
        """
        Devuelve la marca del dispositivo instalado.
        """

        return obj.dispositivo.modelo.marca

    @admin.display(
        description=_("Modelo"),
        ordering="dispositivo__modelo__nombre",
    )
    def modelo(self, obj):
        """
        Devuelve el modelo técnico del dispositivo instalado.
        """

        return obj.dispositivo.modelo

    @admin.display(
        boolean=True,
        description=_("Credenciales"),
    )
    def mostrar_credenciales(self, obj):
        """
        Indica si el dispositivo tiene usuario y contraseña.
        """

        return obj.tiene_credenciales

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza todas las relaciones utilizadas
        en el listado del administrador.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "instalacion",
                "instalacion__orden_trabajo",
                "instalacion__orden_trabajo__sucursal",
                "instalacion__orden_trabajo__sucursal__cuenta_cliente",
                "instalacion__orden_trabajo__proyecto",
                "instalacion__orden_trabajo__servicio_contratado",
                "instalacion__orden_trabajo__presupuesto_telecom",
                "dispositivo",
                "dispositivo__modelo",
                "dispositivo__modelo__marca",
                "dispositivo__modelo__tipo_dispositivo",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "instalacion",
        "dispositivo",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "mostrar_orden_trabajo",
        "mostrar_sucursal",
        "mostrar_proyecto",
        "mostrar_servicio_contratado",
        "mostrar_presupuesto_telecom",
        "created_at",
        "updated_at",
    )

    # ======================================================
    # INFORMACIÓN DERIVADA
    # ======================================================

    @admin.display(
        description=_("Orden de trabajo"),
    )
    def mostrar_orden_trabajo(self, obj):
        if not obj.pk:
            return "-"

        return obj.instalacion.orden_trabajo

    @admin.display(
        description=_("Sucursal"),
    )
    def mostrar_sucursal(self, obj):
        if not obj.pk:
            return "-"

        return obj.instalacion.orden_trabajo.sucursal or "-"

    @admin.display(
        description=_("Proyecto"),
    )
    def mostrar_proyecto(self, obj):
        if not obj.pk:
            return "-"

        return obj.instalacion.orden_trabajo.proyecto or "-"

    @admin.display(
        description=_("Servicio contratado"),
    )
    def mostrar_servicio_contratado(self, obj):
        if not obj.pk:
            return "-"

        return (
            obj.instalacion
            .orden_trabajo
            .servicio_contratado
            or "-"
        )

    @admin.display(
        description=_("Presupuesto Telecom"),
    )
    def mostrar_presupuesto_telecom(self, obj):
        if not obj.pk:
            return "-"

        return (
            obj.instalacion
            .orden_trabajo
            .presupuesto_telecom
            or "-"
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
                    "instalacion",
                    "dispositivo",
                    "estado",
                    "is_active",
                ),
            },
        ),
        (
            _("Origen de la instalación"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "mostrar_orden_trabajo",
                    "mostrar_sucursal",
                    "mostrar_proyecto",
                    "mostrar_servicio_contratado",
                    "mostrar_presupuesto_telecom",
                ),
            },
        ),
        (
            _("Identificación del equipo"),
            {
                "fields": (
                    "numero_serie",
                ),
            },
        ),
        (
            _("Configuración de red"),
            {
                "fields": (
                    (
                        "direccion_mac",
                        "direccion_ip",
                    ),
                ),
            },
        ),
        (
            _("Credenciales"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    (
                        "usuario_acceso",
                        "contrasena_acceso",
                    ),
                ),
            },
        ),
        (
            _("Ubicación"),
            {
                "fields": (
                    "ubicacion",
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
    # ACCIONES
    # ======================================================

    actions = ()