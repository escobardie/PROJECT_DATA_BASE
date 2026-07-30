from django.contrib import admin

from apps.instalacion.models import InstalacionTecnico


class InstalacionTecnicoInline(admin.TabularInline):
    """
    Técnicos asignados a una instalación.
    """

    model = InstalacionTecnico

    extra = 0

    autocomplete_fields = (
        "usuario",
    )

    fields = (
        "usuario",
        "rol",
        "es_responsable",
        "observaciones",
    )

    ordering = (
        "-es_responsable",
        "usuario",
    )

    show_change_link = True