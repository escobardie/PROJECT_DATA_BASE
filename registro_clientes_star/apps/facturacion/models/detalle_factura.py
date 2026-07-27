from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
)

from apps.servicio.models import ServicioContratado

from .factura import Factura


class DetalleFactura(CodeModel):
    """
    Representa un concepto dentro de una factura.

    Guarda una copia histórica del servicio facturado,
    evitando que cambios futuros afecten facturas anteriores.
    """

    # ======================================================
    # RELACIONES
    # ======================================================

    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name=_("Factura"),
    )

    servicio_contratado = models.ForeignKey(
        ServicioContratado,
        on_delete=models.PROTECT,
        related_name="detalles_facturacion",
        verbose_name=_("Servicio contratado"),
    )

    # ======================================================
    # INFORMACIÓN HISTÓRICA
    # ======================================================

    descripcion = models.CharField(
        max_length=200,
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción del concepto facturado."
        ),
    )

    # ======================================================
    # IMPORTES
    # ======================================================

    cantidad = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=1,
        verbose_name=_("Cantidad"),
    )

    precio_unitario = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        verbose_name=_("Precio unitario"),
    )

    descuento = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=0,
        verbose_name=_("Descuento"),
    )

    subtotal = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        verbose_name=_("Subtotal"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Detalle de factura")
        verbose_name_plural = _("Detalles de factura")
        ordering = ("id",)

    # ======================================================
    # CREACIÓN
    # ======================================================

    def save(self, *args, **kwargs):
        """
        Calcula automáticamente el subtotal.
        """

        self.subtotal = (
            self.cantidad * self.precio_unitario
            - self.descuento
        )

        super().save(*args, **kwargs)

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return self.descripcion