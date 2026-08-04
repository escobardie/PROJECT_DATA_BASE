from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import OrdenTrabajoSeguimiento


class OrdenTrabajoSeguimientoInline(admin.TabularInline):
    """
    Seguimientos registrados sobre una orden de trabajo.
    """

    model = OrdenTrabajoSeguimiento

    extra = 1

    ordering = (
        "-created_at",
    )

    autocomplete_fields = (
        "usuario",
    )

    fields = (
        "usuario",
        "comentario",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    show_change_link = True


@admin.register(OrdenTrabajoSeguimiento)
class OrdenTrabajoSeguimientoAdmin(admin.ModelAdmin):
    """
    Administración de seguimientos de órdenes de trabajo.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "orden_trabajo",
        "usuario",
        "comentario_resumido",
        "created_at",
    )

    list_display_links = (
        "orden_trabajo",
        "usuario",
    )

    list_filter = (
        "created_at",
        "usuario",
        "orden_trabajo__estado",
    )

    search_fields = (
        "orden_trabajo__codigo",
        "orden_trabajo__titulo",
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "comentario",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "created_at"

    empty_value_display = "-"

    save_on_top = True

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Comentario"),
    )
    def comentario_resumido(self, obj):
        """
        Muestra un resumen del comentario.
        """

        if len(obj.comentario) <= 80:
            return obj.comentario

        return f"{obj.comentario[:80]}..."

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las consultas del administrador.
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
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "orden_trabajo",
        "usuario",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (

        (
            _("Información"),
            {
                "fields": (
                    "orden_trabajo",
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
    # ACCIONES
    # ======================================================

    actions = ()