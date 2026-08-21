from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import (
    OrdenTrabajoSeguimiento,
)

from apps.usuarios.permissions import (
    puede_ver_seguimiento_ot,
)


# ======================================================
# INLINE
# ======================================================


class OrdenTrabajoSeguimientoInline(admin.TabularInline):
    """
    Historial de seguimientos de una Orden de Trabajo.

    Los seguimientos son registros históricos.

    Desde este inline:

    - no se crean;
    - no se modifican;
    - no se eliminan.

    Los nuevos seguimientos deben registrarse mediante:

        OrdenTrabajoAdmin
            ↓
        Permissions
            ↓
        Services
            ↓
        OrdenTrabajoSeguimiento
    """

    model = OrdenTrabajoSeguimiento

    extra = 0

    fields = (
        "fecha_seguimiento",
        "usuario",
        "comentario",
        "created_at",
    )

    readonly_fields = (
        "fecha_seguimiento",
        "usuario",
        "comentario",
        "created_at",
    )

    ordering = (
        "-fecha_seguimiento",
        "-created_at",
    )

    show_change_link = True

    can_delete = False

    verbose_name = _(
        "Seguimiento"
    )

    verbose_name_plural = _(
        "Historial de seguimientos"
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
        El seguimiento no se crea directamente
        desde el inline.

        Se utiliza la acción controlada
        Registrar seguimiento.
        """

        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        Permite mostrar los seguimientos asociados
        a la OT.

        Todos los campos son readonly.
        """

        if obj is None:
            return False

        return True

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        Los seguimientos no se eliminan.

        Una corrección debe registrarse mediante
        un nuevo seguimiento.
        """

        return False


# ======================================================
# ADMIN INDIVIDUAL
# ======================================================


@admin.register(OrdenTrabajoSeguimiento)
class OrdenTrabajoSeguimientoAdmin(admin.ModelAdmin):
    """
    Consulta administrativa de seguimientos.

    Un seguimiento representa un evento histórico.

    Una vez registrado:

    - usuario no cambia;
    - fecha funcional no cambia;
    - comentario no cambia;
    - el registro no se elimina.

    Cualquier corrección debe agregarse
    mediante un seguimiento nuevo.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "orden_trabajo",
        "fecha_seguimiento",
        "usuario",
        "comentario_resumido",
        "created_at",
    )

    list_display_links = (
        "orden_trabajo",
        "fecha_seguimiento",
    )

    list_filter = (
        "usuario",
        "orden_trabajo__estado",
        "orden_trabajo__prioridad",
        "fecha_seguimiento",
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

        # Seguimiento
        "comentario",
    )

    ordering = (
        "-fecha_seguimiento",
        "-created_at",
    )

    empty_value_display = "-"

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Comentario"),
    )
    def comentario_resumido(
        self,
        obj,
    ):
        """
        Muestra una versión resumida
        del seguimiento.
        """

        comentario = (
            obj.comentario
            or ""
        )

        if len(comentario) <= 100:
            return comentario

        return (
            f"{comentario[:100]}..."
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
        en la consulta.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "orden_trabajo",
                "usuario",
            )
        )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "orden_trabajo",
        "fecha_seguimiento",
        "usuario",
        "comentario",
        "created_at",
        "updated_at",
    )

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (
        (
            _("Seguimiento"),
            {
                "fields": (
                    "orden_trabajo",
                    "fecha_seguimiento",
                    "usuario",
                    "comentario",
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
    # PERMISOS
    # ======================================================

    def has_module_permission(
        self,
        request,
    ):
        """
        Evita utilizar Seguimientos como módulo
        independiente para la carga funcional.

        El listado general queda reservado
        al superusuario.

        La consulta de un seguimiento concreto
        continúa controlada mediante
        puede_ver_seguimiento_ot().
        """

        return bool(
            request.user.is_active
            and request.user.is_superuser
        )

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        """
        Controla el acceso de lectura.

        Para el changelist completo se exige
        superusuario para evitar exponer seguimientos
        de órdenes ajenas.

        Para un seguimiento concreto se utiliza
        la regla de permisos de la OT.
        """

        if obj is None:
            return bool(
                request.user.is_active
                and request.user.is_superuser
            )

        return puede_ver_seguimiento_ot(
            request.user,
            obj,
        )

    def has_add_permission(
        self,
        request,
    ):
        """
        No se crean seguimientos desde
        el ModelAdmin individual.
        """

        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        Se permite abrir el detalle únicamente
        como consulta.

        Los campos permanecen todos readonly.
        """

        if obj is None:
            return False

        return puede_ver_seguimiento_ot(
            request.user,
            obj,
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        Un seguimiento histórico nunca se elimina
        mediante el flujo funcional.
        """

        return False

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()