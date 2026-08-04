from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.proyecto.models import ProyectoDetalle


class ProyectoDetalleInline(admin.TabularInline):
    """
    Detalles del proyecto.
    """

    model = ProyectoDetalle

    extra = 1

    classes = (
        "tabular",
    )

    verbose_name = _("Detalle")

    verbose_name_plural = _("Detalles")

    ordering = (
        "orden",
    )
    sortable_field_name = "orden"

    autocomplete_fields = (
        "dispositivo",
    )

    show_change_link = True

    fields = (
        "orden",
        "tipo",
        "dispositivo",
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