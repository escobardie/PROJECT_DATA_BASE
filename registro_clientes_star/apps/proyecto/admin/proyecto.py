from django.contrib import admin
from django.db.models import Count
from django.db import transaction
from django.utils.translation import gettext_lazy as _


from apps.proyecto.models import (
    Proyecto,
    ProyectoDetalle,
)
from apps.proyecto.services import (
    actualizar_detalle_proyecto,
    crear_detalle_proyecto,
    eliminar_detalle_proyecto,
)

from apps.usuarios.permissions import (
    puede_editar_proyecto,
    puede_eliminar_proyecto,
    puede_ver_costos_del_proyecto,
    puede_ver_proyecto,
)

from apps.usuarios.services.permisos import (
    puede_crear_proyectos,
    puede_ver_costos_proyecto,
    puede_ver_proyectos,
)

from apps.usuarios.services.querysets import (
    filtrar_proyectos,
)

from .inlines import ProyectoDetalleInline


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    """
    Administración de proyectos.

    La visibilidad y modificación de los registros se limita
    según los roles, permisos y alcance del usuario.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "nombre",
        "sucursal",
        "responsable",
        "estado",
        "cantidad_detalles",
        "cantidad_ordenes_trabajo",
        "fecha_creacion",
        "total",
    )

    list_display_links = (
        "codigo",
        "nombre",
    )

    list_filter = (
        "estado",
        "moneda",
        "responsable",
        "sucursal",
    )

    search_fields = (
        "codigo",
        "nombre",
        "descripcion",

        # Sucursal y cuenta
        "sucursal__codigo",
        "sucursal__nombre",
        "sucursal__cuenta_cliente__codigo",
        "sucursal__cuenta_cliente__nombre",

        # Responsable
        "responsable__email",
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
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "sucursal",
        "responsable",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "subtotal",
        "descuento_total",
        "impuestos",
        "total",
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
                    "sucursal",
                    "responsable",
                    "nombre",
                    "descripcion",
                ),
            },
        ),
        (
            _("Condiciones comerciales"),
            {
                "fields": (
                    "moneda",
                ),
            },
        ),
        (
            _("Fechas"),
            {
                "fields": (
                    (
                        "fecha_creacion",
                        "fecha_planificada",
                    ),
                    (
                        "fecha_inicio",
                        "fecha_finalizacion",
                    ),
                ),
            },
        ),
        (
            _("Estado"),
            {
                "fields": (
                    "estado",
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
            _("Resumen económico"),
            {
                "fields": (
                    (
                        "subtotal",
                        "descuento_total",
                    ),
                    (
                        "impuestos",
                        "total",
                    ),
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
        ProyectoDetalleInline,
    )

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza la consulta y limita los proyectos visibles
        según el alcance del usuario.
        """

        queryset = (
            super()
            .get_queryset(request)
            .select_related(
                "sucursal",
                "sucursal__cuenta_cliente",
                "responsable",
            )
            .annotate(
                _cantidad_detalles=Count(
                    "detalles",
                    distinct=True,
                ),
                _cantidad_ordenes_trabajo=Count(
                    "ordenes_trabajo",
                    distinct=True,
                ),
            )
        )

        return filtrar_proyectos(
            request.user,
            queryset,
        )

    # ======================================================
    # COLUMNAS DINÁMICAS
    # ======================================================

    def get_list_display(self, request):
        """
        Oculta los importes económicos para usuarios
        que no tienen autorización para consultarlos.
        """

        columnas = list(
            super().get_list_display(request)
        )

        if not puede_ver_costos_proyecto(request.user):
            columnas = [
                columna
                for columna in columnas
                if columna != "total"
            ]

        return tuple(columnas)

    # ======================================================
    # FIELDSETS DINÁMICOS
    # ======================================================

    def get_fieldsets(self, request, obj=None):
        """
        Retira el resumen económico cuando el usuario
        no está autorizado a consultar costos e importes.
        """

        fieldsets = list(
            super().get_fieldsets(
                request,
                obj,
            )
        )

        puede_ver_costos = (
            puede_ver_costos_del_proyecto(
                request.user,
                obj,
            )
            if obj
            else puede_ver_costos_proyecto(
                request.user,
            )
        )

        if not puede_ver_costos:
            fieldsets = [
                fieldset
                for fieldset in fieldsets
                if fieldset[0] != _("Resumen económico")
            ]

        return tuple(fieldsets)

    # ======================================================
    # PERMISOS DEL ADMIN
    # ======================================================

    def has_module_permission(self, request):
        """
        Controla si el módulo Proyecto aparece
        en el índice administrativo.
        """

        return puede_ver_proyectos(
            request.user,
        )

    def has_view_permission(self, request, obj=None):
        """
        Controla la visualización general y por objeto.
        """

        permiso_django = super().has_view_permission(
            request,
            obj,
        )

        if not permiso_django:
            return False

        if obj is None:
            return puede_ver_proyectos(
                request.user,
            )

        return puede_ver_proyecto(
            request.user,
            obj,
        )

    def has_add_permission(self, request):
        """
        Controla la creación de proyectos.
        """

        permiso_django = super().has_add_permission(
            request,
        )

        return bool(
            permiso_django
            and puede_crear_proyectos(
                request.user,
            )
        )

    def has_change_permission(self, request, obj=None):
        """
        Controla la modificación general y por objeto.
        """

        permiso_django = super().has_change_permission(
            request,
            obj,
        )

        if not permiso_django:
            return False

        if obj is None:
            return request.user.has_perm(
                "proyecto.change_proyecto"
            )

        return puede_editar_proyecto(
            request.user,
            obj,
        )

    def has_delete_permission(self, request, obj=None):
        """
        Solamente permite eliminar proyectos completos
        cuando la regla específica lo autoriza.
        """

        permiso_django = super().has_delete_permission(
            request,
            obj,
        )

        if not permiso_django:
            return False

        if obj is None:
            return bool(
                request.user.is_superuser
                and request.user.has_perm(
                    "proyecto.delete_proyecto"
                )
            )

        return puede_eliminar_proyecto(
            request.user,
            obj,
        )

    # ======================================================
    # GUARDADO DE INLINES MEDIANTE SERVICES
    # ======================================================

    @transaction.atomic
    def save_formset(
        self,
        request,
        form,
        formset,
        change,
    ):
        """
        Guarda los detalles del proyecto mediante
        los servicios de la app proyecto.

        Los formsets correspondientes a otros modelos
        conservan el comportamiento estándar de Django.
        """

        if formset.model is not ProyectoDetalle:
            super().save_formset(
                request,
                form,
                formset,
                change,
            )
            return

        # Obtiene instancias nuevas y modificadas sin
        # guardarlas ni eliminar automáticamente registros.
        instancias = formset.save(
            commit=False,
        )

        # ----------------------------------------------
        # ELIMINACIONES
        # ----------------------------------------------

        for detalle_eliminado in formset.deleted_objects:
            eliminar_detalle_proyecto(
                detalle=detalle_eliminado,
            )

        # ----------------------------------------------
        # ALTAS Y MODIFICACIONES
        # ----------------------------------------------

        for instancia in instancias:
            if instancia.pk:
                detalle_guardado = (
                    actualizar_detalle_proyecto(
                        detalle=instancia,
                        dispositivo=instancia.dispositivo,
                        item_catalogo=(
                            instancia.item_catalogo
                        ),
                        descripcion=instancia.descripcion,
                        orden=instancia.orden,
                        cantidad=instancia.cantidad,
                        precio_unitario=(
                            instancia.precio_unitario
                        ),
                        descuento_importe=(
                            instancia.descuento_importe
                        ),
                        impuestos_importe=(
                            instancia.impuestos_importe
                        ),
                        observaciones=(
                            instancia.observaciones
                        ),
                        is_active=instancia.is_active,
                    )
                )

            else:
                detalle_guardado = (
                    crear_detalle_proyecto(
                        proyecto=form.instance,
                        dispositivo=instancia.dispositivo,
                        item_catalogo=(
                            instancia.item_catalogo
                        ),
                        descripcion=instancia.descripcion,
                        orden=instancia.orden,
                        cantidad=instancia.cantidad,
                        precio_unitario=(
                            instancia.precio_unitario
                        ),
                        descuento_importe=(
                            instancia.descuento_importe
                        ),
                        impuestos_importe=(
                            instancia.impuestos_importe
                        ),
                        observaciones=(
                            instancia.observaciones
                        ),
                        is_active=instancia.is_active,
                    )
                )

            self._sincronizar_detalle_inline(
                destino=instancia,
                origen=detalle_guardado,
            )

        # Actualmente ProyectoDetalle no tiene relaciones
        # ManyToMany, pero se conserva el flujo estándar
        # por compatibilidad futura.
        formset.save_m2m()

    # ======================================================
    # SINCRONIZACIÓN DE INSTANCIAS DEL INLINE
    # ======================================================

    @staticmethod
    def _sincronizar_detalle_inline(
        *,
        destino: ProyectoDetalle,
        origen: ProyectoDetalle,
    ) -> None:
        """
        Sincroniza la instancia administrada por el formset
        con la instancia persistida por el servicio.
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
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Detalles"),
        ordering="_cantidad_detalles",
    )
    def cantidad_detalles(self, obj):
        """
        Devuelve la cantidad de detalles del proyecto
        sin generar una consulta adicional por cada fila.
        """

        return obj._cantidad_detalles

    @admin.display(
        description=_("OT"),
        ordering="_cantidad_ordenes_trabajo",
    )
    def cantidad_ordenes_trabajo(self, obj):
        """
        Devuelve la cantidad de órdenes relacionadas
        sin generar una consulta adicional por cada fila.
        """

        return obj._cantidad_ordenes_trabajo

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()