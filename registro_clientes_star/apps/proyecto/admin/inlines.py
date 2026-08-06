from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.proyecto.models import ProyectoDetalle


class ProyectoDetalleInline(admin.TabularInline):
    """
    Detalles comerciales y técnicos incluidos
    dentro de un proyecto.
    """

    model = ProyectoDetalle

    extra = 1

    autocomplete_fields = (
        "dispositivo",
        "item_catalogo",
    )

    fields = (
        "orden",
        "tipo",
        "dispositivo",
        "item_catalogo",
        "descripcion",
        "cantidad",
        "unidad",
        "precio_unitario",
        "descuento_importe",
        "impuestos_importe",
        "subtotal",
        "total",
    )

    readonly_fields = (
        "subtotal",
        "total",
    )

    ordering = (
        "orden",
        "codigo",
    )

    show_change_link = True

    verbose_name = _("Detalle del proyecto")
    verbose_name_plural = _("Detalles del proyecto")