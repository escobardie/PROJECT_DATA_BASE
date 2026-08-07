from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.proyecto.models import ProyectoDetalle

from apps.proyecto.services import (
    actualizar_detalle_proyecto,
    crear_detalle_proyecto,
    eliminar_detalle_proyecto,
)

from apps.usuarios.permissions import (
    puede_editar_proyecto,
    puede_ver_costos_del_proyecto,
    puede_ver_proyecto,
)

from apps.usuarios.services.permisos import (
    puede_crear_proyectos,
    puede_ver_costos_proyecto,
    puede_ver_proyectos,
)

from apps.usuarios.services.querysets import (
    filtrar_detalles_proyecto,
)

from apps.usuarios.services.roles import (
    es_auditor,
    es_superadmin,
    es_usuario_cliente,
)


@admin.register(ProyectoDetalle)
class ProyectoDetalleAdmin(admin.ModelAdmin):
    """
    Administración de los detalles comerciales
    y técnicos de los proyectos.

    Las operaciones de creación, modificación y eliminación
    se realizan mediante los servicios de la app proyecto.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "proyecto",
        "proyecto_estado",
        "orden",
        "tipo",
        "mostrar_origen",
        "descripcion",
        "cantidad",
        "unidad",
        "precio_unitario",
        "total",
        "is_active",
    )

    list_display_links = (
        "codigo",
        "descripcion",
    )

    list_filter = (
        "tipo",
        "proyecto__estado",
        "proyecto__sucursal",
        "item_catalogo__categoria",
        "item_catalogo__controla_stock",
        "dispositivo__modelo__marca",
        "is_active",
    )

    search_fields = (
        # Detalle
        "codigo",
        "descripcion",

        # Proyecto
        "proyecto__codigo",
        "proyecto__nombre",

        # Dispositivo
        "dispositivo__codigo",
        "dispositivo__nombre_comercial",
        "dispositivo__modelo__nombre",
        "dispositivo__modelo__marca__nombre",

        # Ítem del catálogo
        "item_catalogo__codigo",
        "item_catalogo__nombre",
        "item_catalogo__descripcion",
        "item_catalogo__categoria__codigo",
        "item_catalogo__categoria__nombre",
    )

    ordering = (
        "proyecto",
        "orden",
        "codigo",
    )

    empty_value_display = "-"

    save_on_top = True
    save_as = True
    list_per_page = 25
    show_full_result_count = False

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "proyecto",
        "dispositivo",
        "item_catalogo",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "tipo",
        "unidad",
        "mostrar_origen",
        "subtotal",
        "total",
        "created_at",
        "updated_at",
    )

    # ======================================================
    # FORMULARIO
    # ======================================================

    FIELDSETS_COMPLETOS = (
        (
            _("Información general"),
            {
                "fields": (
                    "codigo",
                    "proyecto",
                    (
                        "orden",
                        "tipo",
                    ),
                    (
                        "dispositivo",
                        "item_catalogo",
                    ),
                    "mostrar_origen",
                    "descripcion",
                    "is_active",
                ),
            },
        ),
        (
            _("Cantidades"),
            {
                "fields": (
                    (
                        "cantidad",
                        "unidad",
                    ),
                ),
            },
        ),
        (
            _("Importes"),
            {
                "fields": (
                    (
                        "precio_unitario",
                        "descuento_importe",
                    ),
                    (
                        "impuestos_importe",
                        "subtotal",
                    ),
                    "total",
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

    FIELDSETS_SIN_IMPORTES = (
        (
            _("Información general"),
            {
                "fields": (
                    "codigo",
                    "proyecto",
                    (
                        "orden",
                        "tipo",
                    ),
                    (
                        "dispositivo",
                        "item_catalogo",
                    ),
                    "mostrar_origen",
                    "descripcion",
                    "is_active",
                ),
            },
        ),
        (
            _("Cantidades"),
            {
                "fields": (
                    (
                        "cantidad",
                        "unidad",
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
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Estado"),
        ordering="proyecto__estado",
    )
    def proyecto_estado(self, obj):
        """
        Devuelve el estado del proyecto asociado.
        """

        return obj.proyecto.get_estado_display()

    @admin.display(
        description=_("Origen"),
    )
    def mostrar_origen(self, obj):
        """
        Devuelve el dispositivo o ítem de catálogo
        asociado al detalle.
        """

        if obj.dispositivo_id:
            return obj.dispositivo

        if obj.item_catalogo_id:
            return obj.item_catalogo

        return "-"

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las relaciones y limita los registros
        visibles según el alcance del usuario.
        """

        queryset = (
            super()
            .get_queryset(request)
            .select_related(
                "proyecto",
                "proyecto__sucursal",
                "proyecto__sucursal__cuenta_cliente",
                "dispositivo",
                "dispositivo__modelo",
                "dispositivo__modelo__marca",
                "item_catalogo",
                "item_catalogo__categoria",
            )
        )

        return filtrar_detalles_proyecto(
            request.user,
            queryset,
        )

    # ======================================================
    # CAMPOS DINÁMICOS
    # ======================================================

    def get_list_display(self, request):
        """
        Oculta las columnas económicas cuando el usuario
        no tiene autorización para consultar importes.
        """

        columnas = list(
            super().get_list_display(request)
        )

        if not puede_ver_costos_proyecto(request.user):
            columnas = [
                columna
                for columna in columnas
                if columna not in {
                    "precio_unitario",
                    "total",
                }
            ]

        return tuple(columnas)

    def get_fieldsets(self, request, obj=None):
        """
        Define el formulario visible según el permiso
        para consultar información económica.
        """

        puede_ver_importes = (
            puede_ver_costos_del_proyecto(
                request.user,
                obj.proyecto,
            )
            if obj
            else puede_ver_costos_proyecto(
                request.user,
            )
        )

        if puede_ver_importes:
            return self.FIELDSETS_COMPLETOS

        return self.FIELDSETS_SIN_IMPORTES

    # ======================================================
    # PERMISOS DEL ADMIN
    # ======================================================

    def has_module_permission(self, request):
        """
        Controla la aparición del módulo en el Admin.
        """

        return puede_ver_proyectos(
            request.user,
        )

    def has_view_permission(self, request, obj=None):
        """
        Controla la visualización general y por objeto.
        """

        if not super().has_view_permission(
            request,
            obj,
        ):
            return False

        if obj is None:
            return request.user.has_perm(
                "proyecto.view_proyectodetalle"
            )

        return puede_ver_proyecto(
            request.user,
            obj.proyecto,
        )

    def has_add_permission(self, request):
        """
        Controla la creación de detalles.
        """

        if not super().has_add_permission(request):
            return False

        if (
            es_auditor(request.user)
            or es_usuario_cliente(request.user)
        ):
            return False

        return puede_crear_proyectos(
            request.user,
        )

    def has_change_permission(self, request, obj=None):
        """
        Controla la modificación general y por objeto.
        """

        if not super().has_change_permission(
            request,
            obj,
        ):
            return False

        if (
            es_auditor(request.user)
            or es_usuario_cliente(request.user)
        ):
            return False

        if obj is None:
            return request.user.has_perm(
                "proyecto.change_proyectodetalle"
            )

        return puede_editar_proyecto(
            request.user,
            obj.proyecto,
        )

    def has_delete_permission(self, request, obj=None):
        """
        Controla la eliminación general y por objeto.
        """

        if not super().has_delete_permission(
            request,
            obj,
        ):
            return False

        if (
            es_auditor(request.user)
            or es_usuario_cliente(request.user)
        ):
            return False

        if obj is None:
            return bool(
                es_superadmin(request.user)
                or request.user.has_perm(
                    "proyecto.delete_proyectodetalle"
                )
            )

        return bool(
            puede_editar_proyecto(
                request.user,
                obj.proyecto,
            )
            and request.user.has_perm(
                "proyecto.delete_proyectodetalle"
            )
        )

    # ======================================================
    # GUARDADO MEDIANTE SERVICES
    # ======================================================

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        """
        Crea o actualiza el detalle mediante
        los servicios de la app proyecto.

        No se llama a super().save_model(), porque
        la persistencia ya fue realizada por el servicio.
        """

        if change:
            detalle_guardado = (
                actualizar_detalle_proyecto(
                    detalle=obj,
                    dispositivo=obj.dispositivo,
                    item_catalogo=obj.item_catalogo,
                    descripcion=obj.descripcion,
                    orden=obj.orden,
                    cantidad=obj.cantidad,
                    precio_unitario=obj.precio_unitario,
                    descuento_importe=(
                        obj.descuento_importe
                    ),
                    impuestos_importe=(
                        obj.impuestos_importe
                    ),
                    observaciones=obj.observaciones,
                    is_active=obj.is_active,
                )
            )

        else:
            detalle_guardado = (
                crear_detalle_proyecto(
                    proyecto=obj.proyecto,
                    dispositivo=obj.dispositivo,
                    item_catalogo=obj.item_catalogo,
                    descripcion=obj.descripcion,
                    orden=obj.orden,
                    cantidad=obj.cantidad,
                    precio_unitario=obj.precio_unitario,
                    descuento_importe=(
                        obj.descuento_importe
                    ),
                    impuestos_importe=(
                        obj.impuestos_importe
                    ),
                    observaciones=obj.observaciones,
                    is_active=obj.is_active,
                )
            )

        self._sincronizar_instancia(
            destino=obj,
            origen=detalle_guardado,
        )

    # ======================================================
    # ELIMINACIÓN MEDIANTE SERVICES
    # ======================================================

    def delete_model(
        self,
        request,
        obj,
    ):
        """
        Elimina un detalle mediante el servicio
        correspondiente.
        """

        eliminar_detalle_proyecto(
            detalle=obj,
        )

    def delete_queryset(
        self,
        request,
        queryset,
    ):
        """
        Elimina cada detalle mediante el servicio para
        mantener actualizados los totales de los proyectos.

        Actualmente las acciones masivas están deshabilitadas,
        pero el método queda preparado para futuras acciones.
        """

        detalles = list(
            queryset.select_related(
                "proyecto",
            )
        )

        for detalle in detalles:
            eliminar_detalle_proyecto(
                detalle=detalle,
            )

    # ======================================================
    # FUNCIONES INTERNAS
    # ======================================================

    @staticmethod
    def _sincronizar_instancia(
        *,
        destino: ProyectoDetalle,
        origen: ProyectoDetalle,
    ) -> None:
        """
        Sincroniza la instancia utilizada por el Admin
        con la instancia creada o actualizada por el servicio.

        Esto permite que Django Admin registre correctamente
        el objeto, su clave primaria y su código.
        """

        destino.pk = origen.pk
        destino.id = origen.id
        destino.codigo = origen.codigo

        destino.proyecto = origen.proyecto
        destino.dispositivo = origen.dispositivo
        destino.item_catalogo = origen.item_catalogo

        destino.tipo = origen.tipo
        destino.descripcion = origen.descripcion
        destino.orden = origen.orden
        destino.cantidad = origen.cantidad
        destino.unidad = origen.unidad

        destino.precio_unitario = origen.precio_unitario
        destino.descuento_importe = (
            origen.descuento_importe
        )
        destino.impuestos_importe = (
            origen.impuestos_importe
        )
        destino.subtotal = origen.subtotal
        destino.total = origen.total

        destino.observaciones = origen.observaciones
        destino.is_active = origen.is_active
        destino.created_at = origen.created_at
        destino.updated_at = origen.updated_at

        destino._state.adding = False
        destino._state.db = origen._state.db

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()