from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    CONTRACTED_SERVICE_CODE_PREFIX,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
)

from apps.cuenta_cliente.models import (
    CuentaCliente,
    Sucursal,
)

from .numerador_factura import NumeradorFactura


class Factura(CodeModel):
    """
    Representa una factura emitida a un cliente.

    La factura conserva una fotografía histórica del momento
    de emisión.

    El estado, saldo y pagos se calculan dinámicamente.
    """

    CODE_PREFIX = "FAC"

    # ======================================================
    # RELACIONES
    # ======================================================

    cuenta_cliente = models.ForeignKey(
        CuentaCliente,
        on_delete=models.PROTECT,
        related_name="facturas",
        verbose_name=_("Cuenta cliente"),
    )

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="facturas",
        verbose_name=_("Sucursal"),
    )

    # ======================================================
    # IDENTIFICACIÓN FACTURA
    # ======================================================

    punto_venta = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Punto de venta"),
    )

    numero = models.PositiveIntegerField(
        editable=False,
        verbose_name=_("Número"),
    )

    # ======================================================
    # FECHAS
    # ======================================================

    fecha_emision = models.DateField(
        default=timezone.localdate,
        verbose_name=_("Fecha de emisión"),
    )

    fecha_vencimiento = models.DateField(
        verbose_name=_("Fecha de vencimiento"),
    )

    # ======================================================
    # INFORMACIÓN ECONÓMICA
    # ======================================================

    total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=0,
        verbose_name=_("Total"),
    )

    # ======================================================
    # ANULACIÓN
    # ======================================================

    fecha_anulacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de anulación"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Factura")
        verbose_name_plural = _("Facturas")
        ordering = (
            "-fecha_emision",
            "-numero",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "punto_venta",
                    "numero",
                ],
                name="unique_numero_factura_por_punto",
            )
        ]

    # ======================================================
    # CREACIÓN
    # ======================================================

    def save(self, *args, **kwargs):
        """
        Asigna automáticamente el número de factura.
        """

        if not self.numero:

            self.numero = (
                NumeradorFactura
                .obtener_siguiente_numero(
                    self.punto_venta
                )
            )

        super().save(*args, **kwargs)

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return self.numero_formateado

    # ======================================================
    # PROPIEDADES CALCULADAS
    # ======================================================

    @property
    def numero_formateado(self):
        """
        Número visible de factura.
        """

        return (
            f"{self.punto_venta:04d}-"
            f"{self.numero:08d}"
        )

    @property
    def total_pagado(self):
        """
        Total abonado por el cliente.
        """

        return (
            self.pagos.aggregate(
                total=models.Sum("importe")
            )["total"]
            or 0
        )

    @property
    def saldo_pendiente(self):
        """
        Importe restante a pagar.
        """

        return self.total - self.total_pagado

    @property
    def esta_anulada(self):
        """
        Indica si la factura fue anulada.
        """

        return self.fecha_anulacion is not None

    @property
    def esta_vencida(self):
        """
        Determina si la factura está vencida.
        """

        return (
            not self.esta_anulada
            and self.saldo_pendiente > 0
            and self.fecha_vencimiento
            < timezone.localdate()
        )

    @property
    def fecha_ultimo_pago(self):
        """
        Fecha del último pago registrado.
        """

        ultimo_pago = (
            self.pagos
            .order_by("-fecha")
            .first()
        )

        return (
            ultimo_pago.fecha
            if ultimo_pago
            else None
        )

    @property
    def estado(self):
        """
        Estado actual calculado de la factura.
        """

        if self.esta_anulada:
            return "Anulada"

        if self.esta_vencida:
            return "Vencida"

        if self.saldo_pendiente <= 0:
            return "Pagada"

        if self.total_pagado > 0:
            return "Parcial"

        return "Pendiente"