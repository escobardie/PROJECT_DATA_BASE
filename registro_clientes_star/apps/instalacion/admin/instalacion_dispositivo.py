from django.contrib import admin

from apps.instalacion.models import InstalacionDispositivo


class InstalacionDispositivoInline(admin.TabularInline):
    """
    Dispositivos instalados durante una instalación.

    Permite cargar y visualizar los equipos físicos
    asociados a una instalación.
    """

    model = InstalacionDispositivo

    extra = 0

    autocomplete_fields = (
        "dispositivo",
    )

    fields = (
        "dispositivo",
        "cantidad",
        "numero_serie",
        "direccion_ip",
        "ubicacion",
        "estado",
    )

    ordering = (
        "ubicacion",
        "codigo",
    )

    show_change_link = True