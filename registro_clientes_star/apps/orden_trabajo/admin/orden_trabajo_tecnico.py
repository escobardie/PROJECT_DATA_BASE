from django.contrib import admin

from apps.orden_trabajo.models import OrdenTrabajoTecnico


class OrdenTrabajoTecnicoInline(admin.TabularInline):
    """
    Técnicos asignados a una orden de trabajo.
    """

    model = OrdenTrabajoTecnico

    extra = 0

    autocomplete_fields = (
        "tecnico",
    )

    fields = (
        "tecnico",
        "es_principal",
        "observaciones",
    )

    ordering = (
        "-es_principal",
        "tecnico",
    )

    show_change_link = True