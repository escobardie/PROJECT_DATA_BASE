from django.contrib import admin

from apps.orden_trabajo.models import OrdenTrabajoArchivo


class OrdenTrabajoArchivoInline(admin.TabularInline):
    """
    Archivos asociados a una orden de trabajo.
    """

    model = OrdenTrabajoArchivo

    extra = 1

    autocomplete_fields = (
        "usuario",
    )

    fields = (
        "archivo",
        "descripcion",
        "usuario",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    show_change_link = True