from django.contrib import admin

from apps.orden_trabajo.models import OrdenTrabajoSeguimiento


class OrdenTrabajoSeguimientoInline(admin.TabularInline):
    """
    Seguimientos registrados en una orden de trabajo.
    """

    model = OrdenTrabajoSeguimiento

    extra = 1

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

    ordering = (
        "-created_at",
    )

    show_change_link = True