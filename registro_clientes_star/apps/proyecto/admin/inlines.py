from django.contrib import admin

from apps.proyecto.models import ProyectoRequerimiento


class ProyectoRequerimientoInline(admin.TabularInline):
    """
    Requerimientos técnicos planificados para el proyecto.
    """

    model = ProyectoRequerimiento

    extra = 1

    autocomplete_fields = (
        "dispositivo",
    )

    fields = (
        "dispositivo",
        "cantidad",
        "descripcion",
    )

    ordering = (
        "dispositivo",
        "codigo",
    )

    show_change_link = True