from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.constants import (
    DEFAULT_AMOUNT,
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    DETALLE_FACTURA_CODE_PREFIX,
)

from apps.common.exceptions import FacturaEmitidaError

from apps.servicio.models import ServicioContratado

from .factura import Factura


class DetalleFactura(models.Model):
    """
    Representa un concepto facturado.

    Conserva una copia histórica del servicio contratado
    para evitar que futuras modificaciones afecten
    facturas ya emitidas.
    """
    CODE_PREFIX = DETALLE_FACTURA_CODE_PREFIX

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
        related_name="detalles_factura",
        verbose_name=_("Servicio contratado"),
    )

    # ======================================================
    # INFORMACIÓN HISTÓRICA
    # ======================================================

    concepto = models.CharField(
        max_length=MAX_NAME_LENGTH,
        default="Sin concepto",
        verbose_name=_("Concepto"),
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
    )
    codigo_servicio = models.CharField(
        max_length=20,
        default="PENDIENTE",
        editable=False,
    )

    # ======================================================
    # INFORMACIÓN COMERCIAL
    # ======================================================

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        verbose_name=_("Cantidad"),
    )

    precio_unitario = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Precio unitario"),
    )

    descuento = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Descuento"),
    )

    subtotal = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        editable=False,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Subtotal"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    # ======================================================
    # META
    # ======================================================

    class Meta:
        verbose_name = _("Detalle de factura")
        verbose_name_plural = _("Detalles de factura")
        ordering = ("id",)

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return self.concepto

    # ======================================================
    # MÉTODOS PRIVADOS
    # ======================================================

    def _copiar_datos_del_servicio(self):
        """
        Copia la información del servicio contratado
        solamente cuando el detalle se crea.
        """

        if self.pk:
            return

        if not self.concepto:
            self.concepto = (
                self.servicio_contratado.servicio.nombre
            )

        if not self.descripcion:
            self.descripcion = (
                self.servicio_contratado.servicio.descripcion
            )

        if self.precio_unitario == DEFAULT_AMOUNT:
            self.precio_unitario = (
                self.servicio_contratado.precio_abono
            )

    def calcular_subtotal(self):
        """
        Calcula el subtotal del detalle.
        """

        subtotal = (
            (self.cantidad * self.precio_unitario)
            - self.descuento
        )

        return max(subtotal, Decimal("0.00"))

    # ======================================================
    # PERSISTENCIA
    # ======================================================

    def save(self, *args, **kwargs):

        if self.pk and not self.factura.editable:
            raise FacturaEmitidaError()

        self._copiar_datos_del_servicio()

        self.subtotal = self.calcular_subtotal()

        super().save(*args, **kwargs)

        self.factura.actualizar_total()

    def delete(self, *args, **kwargs):

        if not self.factura.editable:
            raise FacturaEmitidaError()

        factura = self.factura

        super().delete(*args, **kwargs)

        factura.actualizar_total()