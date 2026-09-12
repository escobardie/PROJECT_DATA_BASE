from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.proyecto.models import ProyectoArchivo

from apps.usuarios.permissions import (
    puede_ver_archivo_proyecto,
)


# ======================================================
# INLINE
# ======================================================


class ProyectoArchivoInline(admin.TabularInline):
    """
    Historial documental asociado a un Proyecto.

    Los documentos se muestran únicamente
    como información histórica dentro del Proyecto.

    Desde este inline:

    - no se adjuntan archivos;
    - no se modifican archivos;
    - no se reemplazan archivos;
    - no se eliminan archivos;
    - no se modifica el usuario de carga;
    - no se modifica la fecha documental;
    - no se modifica la información de retiro.

    Las operaciones funcionales se realizarán mediante:

        ProyectoAdmin
            ↓
        Permissions
            ↓
        Services
            ↓
        ProyectoArchivo
    """

    model = ProyectoArchivo

    extra = 0

    can_delete = False

    show_change_link = True

    # ==================================================
    # CAMPOS
    # ==================================================

    fields = (
        "mostrar_nombre_archivo",
        "fecha_documento",
        "usuario",
        "descripcion",
        "mostrar_estado",
        "fecha_retiro",
        "usuario_retiro",
        "motivo_retiro",
        "created_at",
    )

    readonly_fields = (
        "mostrar_nombre_archivo",
        "fecha_documento",
        "usuario",
        "descripcion",
        "mostrar_estado",
        "fecha_retiro",
        "usuario_retiro",
        "motivo_retiro",
        "created_at",
    )

    ordering = (
        "-is_active",
        "-fecha_documento",
        "-created_at",
    )

    verbose_name = _(
        "Archivo"
    )

    verbose_name_plural = _(
        "Historial documental"
    )

    # ==================================================
    # COLUMNAS
    # ==================================================

    @admin.display(
        description=_("Archivo"),
    )
    def mostrar_nombre_archivo(
        self,
        obj,
    ):
        """
        Muestra únicamente el nombre del archivo.

        La descarga protegida se implementará
        posteriormente desde ProyectoAdmin.
        """

        if (
            not obj
            or not obj.pk
        ):
            return "-"

        return obj.nombre_archivo

    @admin.display(
        description=_("Estado"),
        boolean=True,
    )
    def mostrar_estado(
        self,
        obj,
    ):
        """
        True:
            documento activo.

        False:
            documento retirado.
        """

        if (
            not obj
            or not obj.pk
        ):
            return None

        return bool(
            obj.is_active
        )

    # ==================================================
    # PERMISOS
    # ==================================================

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        """
        No se adjuntan documentos directamente
        desde el inline.

        Se utilizará Gestionar archivos.
        """

        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        El historial documental no se modifica
        desde el inline.
        """

        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        Los documentos no se eliminan.

        Cuando un documento deja de ser válido
        se realiza un retiro lógico.
        """

        return False

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        """
        La visibilidad general del inline queda
        subordinada al acceso al ProyectoAdmin.

        El detalle individual utiliza posteriormente
        puede_ver_archivo_proyecto().
        """

        return bool(
            request.user
            and request.user.is_active
        )


# ======================================================
# ADMIN INDIVIDUAL
# ======================================================


@admin.register(ProyectoArchivo)
class ProyectoArchivoAdmin(admin.ModelAdmin):
    """
    Administración de consulta del historial
    documental de Proyectos.

    Este ModelAdmin es de solo lectura.

    Un documento registrado no debe:

    - reemplazarse;
    - modificarse;
    - reasignarse a otro proyecto;
    - cambiar de usuario;
    - eliminarse físicamente.

    Si deja de ser válido se utiliza
    el retiro lógico mediante el service.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "proyecto",
        "mostrar_nombre_archivo",
        "fecha_documento",
        "usuario",
        "mostrar_estado",
        "descripcion_resumida",
        "created_at",
    )

    list_display_links = (
        "proyecto",
        "mostrar_nombre_archivo",
    )

    list_filter = (
        "is_active",
        "usuario",
        "proyecto__estado",
        "fecha_documento",
        "created_at",
    )

    search_fields = (
        # Proyecto
        "proyecto__codigo",
        "proyecto__nombre",
        "proyecto__descripcion",

        # Usuario de carga
        "usuario__username",
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",

        # Documento
        "archivo",
        "descripcion",

        # Retiro
        "usuario_retiro__username",
        "usuario_retiro__email",
        "usuario_retiro__first_name",
        "usuario_retiro__last_name",
        "motivo_retiro",
    )

    ordering = (
        "-is_active",
        "-fecha_documento",
        "-created_at",
    )

    empty_value_display = "-"

    list_per_page = 25

    show_full_result_count = False

    save_on_top = False

    actions = ()

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Archivo"),
        ordering="archivo",
    )
    def mostrar_nombre_archivo(
        self,
        obj,
    ):
        """
        Muestra únicamente el nombre
        del archivo registrado.
        """

        return obj.nombre_archivo

    @admin.display(
        description=_("Estado"),
        ordering="is_active",
        boolean=True,
    )
    def mostrar_estado(
        self,
        obj,
    ):
        """
        Indica si el documento continúa activo
        dentro del historial documental.
        """

        return bool(
            obj.is_active
        )

    @admin.display(
        description=_("Descripción"),
    )
    def descripcion_resumida(
        self,
        obj,
    ):
        """
        Muestra una versión resumida
        de la descripción en el listado.
        """

        descripcion = (
            obj.descripcion
            or ""
        ).strip()

        if not descripcion:
            return "-"

        if len(descripcion) <= 100:
            return descripcion

        return (
            f"{descripcion[:100]}..."
        )

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(
        self,
        request,
    ):
        """
        Optimiza las relaciones utilizadas
        por listado y detalle.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "proyecto",
                "usuario",
                "usuario_retiro",
            )
        )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "proyecto",
        "mostrar_archivo_registrado",
        "fecha_documento",
        "usuario",
        "descripcion",
        "is_active",
        "fecha_retiro",
        "usuario_retiro",
        "motivo_retiro",
        "created_at",
        "updated_at",
    )

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (
        (
            _("Documento"),
            {
                "fields": (
                    "proyecto",
                    "mostrar_archivo_registrado",
                    "fecha_documento",
                    "descripcion",
                ),
            },
        ),

        (
            _("Registro"),
            {
                "fields": (
                    "usuario",
                    "created_at",
                ),
            },
        ),

        (
            _("Estado documental"),
            {
                "fields": (
                    "is_active",
                    "fecha_retiro",
                    "usuario_retiro",
                    "motivo_retiro",
                ),
            },
        ),

        (
            _("Auditoría técnica"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "updated_at",
                ),
            },
        ),
    )

    # ======================================================
    # INFORMACIÓN DEL ARCHIVO
    # ======================================================

    @admin.display(
        description=_("Archivo"),
    )
    def mostrar_archivo_registrado(
        self,
        obj,
    ):
        """
        Muestra el nombre y la ruta interna
        del documento almacenado.

        No se utiliza archivo.url porque
        la descarga se implementará posteriormente
        mediante una vista protegida en ProyectoAdmin.
        """

        if (
            not obj
            or not obj.pk
            or not obj.archivo
        ):
            return "-"

        return format_html(
            "<strong>{}</strong>"
            "<br>"
            "<small>{}</small>",
            obj.nombre_archivo,
            obj.archivo.name,
        )

    # ======================================================
    # PERMISO DE MÓDULO
    # ======================================================

    def has_module_permission(
        self,
        request,
    ):
        """
        ProyectoArchivo no debe utilizarse como
        módulo independiente para administrar
        documentación.

        El listado global queda reservado
        al superusuario.

        El resto de los usuarios accederá a
        documentos desde el Proyecto correspondiente.
        """

        return bool(
            request.user.is_active
            and request.user.is_superuser
        )

    # ======================================================
    # VER
    # ======================================================

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        """
        Para el listado global se exige superusuario.

        Para un documento concreto se utiliza
        el permiso funcional del Proyecto.
        """

        if obj is None:
            return bool(
                request.user.is_active
                and request.user.is_superuser
            )

        return puede_ver_archivo_proyecto(
            request.user,
            obj,
        )

    # ======================================================
    # AGREGAR
    # ======================================================

    def has_add_permission(
        self,
        request,
    ):
        """
        Los documentos no se cargan desde
        ProyectoArchivoAdmin.

        Deben registrarse mediante
        Gestionar archivos dentro del Proyecto.
        """

        return False

    # ======================================================
    # MODIFICAR
    # ======================================================

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        Un documento registrado es inmutable
        desde el Admin estándar.
        """

        return False

    # ======================================================
    # ELIMINAR
    # ======================================================

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        Nunca se realiza DELETE desde
        el flujo funcional.

        Los documentos se retiran mediante
        retirar_archivo_proyecto().
        """

        return False