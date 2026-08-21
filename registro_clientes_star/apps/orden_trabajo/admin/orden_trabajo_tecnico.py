from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import OrdenTrabajoTecnico

from apps.usuarios.permissions import (
    puede_ver_tecnico_ot,
)


# ======================================================
# INLINE
# ======================================================

class OrdenTrabajoTecnicoInline(admin.TabularInline):
    """
    Historial y estado actual del equipo técnico
    asignado a una orden de trabajo.

    Este inline es exclusivamente informativo.

    Las asignaciones se administran mediante:

        OrdenTrabajoAdmin
            ↓
        Permissions
            ↓
        Services
            ↓
        OrdenTrabajoTecnico

    No se crean, modifican ni eliminan registros
    directamente desde el inline.
    """

    model = OrdenTrabajoTecnico

    extra = 0

    fields = (
        "tecnico",
        "es_principal",
        "is_active",
        "fecha_asignacion",
        "usuario_asignacion",
        "fecha_desasignacion",
        "usuario_desasignacion",
        "observaciones",
    )

    readonly_fields = (
        "tecnico",
        "es_principal",
        "is_active",
        "fecha_asignacion",
        "usuario_asignacion",
        "fecha_desasignacion",
        "usuario_desasignacion",
        "observaciones",
    )

    ordering = (
        "-is_active",
        "-es_principal",
        "tecnico",
    )

    show_change_link = True

    can_delete = False

    verbose_name = _(
        "Técnico asignado"
    )

    verbose_name_plural = _(
        "Técnicos asignados"
    )

    # ==================================================
    # PERMISOS INLINE
    # ==================================================

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        """
        Impide crear asignaciones directamente
        desde el inline.

        La asignación se realizará mediante
        una acción controlada de OrdenTrabajoAdmin.
        """

        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        El inline puede visualizarse, pero
        sus registros no se modifican directamente.
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
        Una asignación nunca se elimina físicamente.

        Para quitar un técnico se utiliza
        desasignar_tecnico_ot().
        """

        return False


# ======================================================
# ADMIN INDIVIDUAL
# ======================================================

@admin.register(OrdenTrabajoTecnico)
class OrdenTrabajoTecnicoAdmin(admin.ModelAdmin):
    """
    Consulta administrativa del historial
    de asignaciones técnicas.

    Este administrador es de solo lectura.

    Toda operación funcional debe originarse
    desde la Orden de Trabajo y pasar por services.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "orden_trabajo",
        "tecnico",
        "es_principal",
        "is_active",
        "fecha_asignacion",
        "usuario_asignacion",
        "fecha_desasignacion",
        "usuario_desasignacion",
    )

    list_display_links = (
        "orden_trabajo",
        "tecnico",
    )

    list_filter = (
        "is_active",
        "es_principal",
        "orden_trabajo__estado",
        "orden_trabajo__prioridad",
    )

    search_fields = (
        # OT
        "orden_trabajo__codigo",
        "orden_trabajo__titulo",

        # Técnico
        "tecnico__username",
        "tecnico__email",
        "tecnico__first_name",
        "tecnico__last_name",

        # Auditoría
        "usuario_asignacion__username",
        "usuario_asignacion__email",
        "usuario_desasignacion__username",
        "usuario_desasignacion__email",

        # Información
        "observaciones",
    )

    ordering = (
        "-is_active",
        "orden_trabajo",
        "-es_principal",
        "tecnico",
    )

    empty_value_display = "-"

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(
        self,
        request,
    ):
        """
        Optimiza las relaciones utilizadas
        por el administrador.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "orden_trabajo",
                "tecnico",
                "usuario_asignacion",
                "usuario_desasignacion",
            )
        )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "orden_trabajo",
        "tecnico",
        "es_principal",
        "is_active",
        "fecha_asignacion",
        "usuario_asignacion",
        "fecha_desasignacion",
        "usuario_desasignacion",
        "observaciones",
        "created_at",
        "updated_at",
    )

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (
        (
            _("Asignación"),
            {
                "fields": (
                    "orden_trabajo",
                    "tecnico",
                    (
                        "es_principal",
                        "is_active",
                    ),
                ),
            },
        ),

        (
            _("Registro de asignación"),
            {
                "fields": (
                    (
                        "fecha_asignacion",
                        "usuario_asignacion",
                    ),
                ),
            },
        ),

        (
            _("Registro de desasignación"),
            {
                "fields": (
                    (
                        "fecha_desasignacion",
                        "usuario_desasignacion",
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
    # PERMISOS
    # ======================================================

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        """
        Controla la consulta de una asignación concreta.
        """

        if obj is None:
            return super().has_view_permission(
                request,
                obj,
            )

        return puede_ver_tecnico_ot(
            request.user,
            obj,
        )

    def has_add_permission(
        self,
        request,
    ):
        """
        No permite crear asignaciones desde
        el ModelAdmin individual.
        """

        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        El formulario solamente permite consulta.

        Se retorna permiso de visualización para que Django
        pueda mostrar el detalle del objeto, pero todos los
        campos permanecen readonly.
        """

        if obj is None:
            return False

        return puede_ver_tecnico_ot(
            request.user,
            obj,
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        Nunca se eliminan asignaciones físicamente.
        """

        return False

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()