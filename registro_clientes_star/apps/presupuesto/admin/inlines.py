from django.contrib import admin

from apps.presupuesto.models import PresupuestoItem
from django.utils.translation import gettext_lazy as _


class PresupuestoItemInline(admin.TabularInline):
    """
    Conceptos comerciales del presupuesto.
    """

    model = PresupuestoItem

    extra = 1

    classes = (
        "tabular",
    )

    verbose_name = _("Concepto")
    verbose_name_plural = _("Conceptos")

    fields = (
        "orden",
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
    )

    show_change_link = True