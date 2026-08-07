from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.proyecto.forms import ProyectoDetalleForm
from apps.proyecto.models import ProyectoDetalle

from apps.usuarios.permissions import (
    puede_editar_proyecto,
    puede_ver_proyecto,
)

from apps.usuarios.services.permisos import (
    puede_crear_proyectos,
    puede_ver_costos_proyecto,
)

from apps.usuarios.services.roles import (
    es_auditor,
    es_superadmin,
    es_usuario_cliente,
)


class ProyectoDetalleInline(admin.TabularInline):
    """
    Detalles comerciales y técnicos incluidos
    dentro de un proyecto.
    """

    model = ProyectoDetalle

    form = ProyectoDetalleForm

    extra = 1

    autocomplete_fields = (
        "dispositivo",
        "item_catalogo",
    )

    ordering = (
        "orden",
        "codigo",
    )

    show_change_link = True

    verbose_name = _("Detalle del proyecto")
    verbose_name_plural = _("Detalles del proyecto")

    # ======================================================
    # DEFINICIÓN DE CAMPOS
    # ======================================================

    CAMPOS_COMPLETOS = (
        "orden",
        "tipo",
        "dispositivo",
        "item_catalogo",
        "descripcion",
        "cantidad",
        "unidad",
        "precio_unitario",
        "descuento_importe",
        "impuestos_importe",
        "subtotal",
        "total",
        "observaciones",
    )

    CAMPOS_SIN_COSTOS = (
        "orden",
        "tipo",
        "dispositivo",
        "item_catalogo",
        "descripcion",
        "cantidad",
        "unidad",
        "observaciones",
    )

    CAMPOS_AUTOMATICOS = (
        "tipo",
        "unidad",
        "subtotal",
        "total",
    )

    # ======================================================
    # VISIBILIDAD
    # ======================================================

    def get_fields(self, request, obj=None):
        """
        Define los campos visibles según el permiso
        para consultar información económica.
        """

        if puede_ver_costos_proyecto(
            request.user
        ):
            return self.CAMPOS_COMPLETOS

        return self.CAMPOS_SIN_COSTOS

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):
        """
        Define los campos que no pueden editarse.
        """

        campos_visibles = self.get_fields(
            request,
            obj,
        )

        if (
            es_auditor(request.user)
            or es_usuario_cliente(request.user)
        ):
            return tuple(campos_visibles)

        if (
            obj is not None
            and not puede_editar_proyecto(
                request.user,
                obj,
            )
        ):
            return tuple(campos_visibles)

        if (
            obj is None
            and not puede_crear_proyectos(
                request.user,
            )
        ):
            return tuple(campos_visibles)

        return tuple(
            campo
            for campo in self.CAMPOS_AUTOMATICOS
            if campo in campos_visibles
        )

    # ======================================================
    # FILAS VACÍAS
    # ======================================================

    def get_extra(
        self,
        request,
        obj=None,
        **kwargs,
    ):
        if self.has_add_permission(
            request,
            obj,
        ):
            return 1

        return 0

    # ======================================================
    # PERMISOS
    # ======================================================

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
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
            obj,
        )

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        if not super().has_add_permission(
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
            return puede_crear_proyectos(
                request.user,
            )

        return puede_editar_proyecto(
            request.user,
            obj,
        )

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
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
            obj,
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
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

        tiene_permiso = request.user.has_perm(
            "proyecto.delete_proyectodetalle"
        )

        if obj is None:
            return bool(
                es_superadmin(request.user)
                or tiene_permiso
            )

        return bool(
            tiene_permiso
            and puede_editar_proyecto(
                request.user,
                obj,
            )
        )