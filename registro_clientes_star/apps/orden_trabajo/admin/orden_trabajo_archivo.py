from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import (
    OrdenTrabajoArchivo,
)

from apps.usuarios.permissions import (
    puede_ver_archivo_ot,
)


# ======================================================
# INLINE
# ======================================================


class OrdenTrabajoArchivoInline(admin.TabularInline):
    """
    Historial documental asociado a una Orden de Trabajo.

    Los archivos se muestran únicamente como historial
    dentro de la OT.

    Desde este inline:

    - no se adjuntan archivos;
    - no se modifican archivos;
    - no se reemplazan archivos;
    - no se eliminan archivos;
    - no se modifica manualmente el usuario;
    - no se modifica información de retiro.

    Las operaciones funcionales se realizan mediante:

        OrdenTrabajoAdmin
            ↓
        Permissions
            ↓
        Services
            ↓
        OrdenTrabajoArchivo
    """

    model = OrdenTrabajoArchivo

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
        Muestra solamente el nombre del archivo.

        La descarga controlada se implementará
        posteriormente desde Gestionar archivos.
        """

        if not obj or not obj.pk:
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
        True  = archivo activo.
        False = archivo retirado.
        """

        if not obj or not obj.pk:
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
        Los archivos no se cargan directamente
        desde el inline.
        """

        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        Los archivos históricos no se modifican
        desde el inline.
        """

        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        No existe eliminación directa.

        Los documentos se retiran lógicamente
        mediante el service correspondiente.
        """

        return False

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        """
        Permite que el inline sea mostrado
        dentro de una OT accesible.
        """

        return bool(
            request.user
            and request.user.is_active
        )


# ======================================================
# ADMIN
# ======================================================


@admin.register(OrdenTrabajoArchivo)
class OrdenTrabajoArchivoAdmin(admin.ModelAdmin):
    """
    Consulta administrativa de archivos asociados
    a Órdenes de Trabajo.

    El ModelAdmin es únicamente de lectura.

    Un documento registrado forma parte
    del historial documental y no debe:

    - reemplazarse;
    - editarse;
    - eliminarse físicamente.

    Si deja de ser válido, debe utilizarse
    el flujo de retiro lógico.
    """

    # ==================================================
    # LISTADO
    # ==================================================

    list_display = (
        "orden_trabajo",
        "mostrar_nombre_archivo",
        "fecha_documento",
        "usuario",
        "mostrar_estado",
        "descripcion_resumida",
        "created_at",
    )

    list_display_links = (
        "orden_trabajo",
        "mostrar_nombre_archivo",
    )

    list_filter = (
        "is_active",
        "usuario",
        "orden_trabajo__estado",
        "orden_trabajo__prioridad",
        "fecha_documento",
        "created_at",
    )

    search_fields = (
        # OT
        "orden_trabajo__codigo",
        "orden_trabajo__titulo",

        # Usuario
        "usuario__username",
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",

        # Archivo
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

    # ==================================================
    # COLUMNAS PERSONALIZADAS
    # ==================================================

    @admin.display(
        description=_("Archivo"),
        ordering="archivo",
    )
    def mostrar_nombre_archivo(
        self,
        obj,
    ):
        """
        Muestra únicamente el nombre del archivo.

        El enlace seguro de descarga será gestionado
        desde la pantalla específica de archivos.
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
        Evita mostrar textos demasiado largos
        en el listado general.
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

    # ==================================================
    # QUERYSET
    # ==================================================

    def get_queryset(
        self,
        request,
    ):
        """
        Optimiza las relaciones utilizadas
        por el listado y formulario.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "orden_trabajo",
                "usuario",
                "usuario_retiro",
            )
        )

    # ==================================================
    # SOLO LECTURA
    # ==================================================

    readonly_fields = (
        "orden_trabajo",
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

    # ==================================================
    # FORMULARIO
    # ==================================================

    fieldsets = (
        (
            _("Documento"),
            {
                "fields": (
                    "orden_trabajo",
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

    # ==================================================
    # ARCHIVO
    # ==================================================

    @admin.display(
        description=_("Archivo"),
    )
    def mostrar_archivo_registrado(
        self,
        obj,
    ):
        """
        Muestra información del archivo registrado.

        De momento no construimos aquí una descarga
        protegida porque esa operación se implementará
        desde OrdenTrabajoAdmin con validación explícita
        de permisos.
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

    # ==================================================
    # PERMISOS DEL MÓDULO
    # ==================================================

    def has_module_permission(
        self,
        request,
    ):
        """
        El módulo independiente de archivos no debe
        convertirse en una vía alternativa para
        administrar documentos.

        El listado global queda reservado
        al superusuario.

        Los demás usuarios acceden a los archivos
        desde la OT correspondiente.
        """

        return bool(
            request.user.is_active
            and request.user.is_superuser
        )

    # ==================================================
    # VER
    # ==================================================

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        """
        Para un archivo concreto se reutiliza
        el permiso funcional de la OT.

        Para el listado global se exige superusuario
        para evitar mostrar archivos pertenecientes
        a órdenes fuera del alcance del usuario.
        """

        if obj is None:
            return bool(
                request.user.is_active
                and request.user.is_superuser
            )

        return puede_ver_archivo_ot(
            request.user,
            obj,
        )

    # ==================================================
    # AGREGAR
    # ==================================================

    def has_add_permission(
        self,
        request,
    ):
        """
        Los archivos no se crean desde
        el ModelAdmin individual.

        Deben cargarse desde Gestionar archivos
        dentro de la Orden de Trabajo.
        """

        return False

    # ==================================================
    # MODIFICAR
    # ==================================================

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        Los documentos registrados son inmutables
        desde el Admin estándar.

        Django puede utilizar has_view_permission()
        para mostrar el formulario en modo consulta.
        """

        return False

    # ==================================================
    # ELIMINAR
    # ==================================================

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        Nunca se realiza una eliminación directa.

        Si el documento deja de ser válido,
        debe utilizarse retirar_archivo_ot().
        """

        return False