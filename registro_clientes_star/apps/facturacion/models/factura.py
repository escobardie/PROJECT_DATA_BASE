from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.constants import (
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    INVOICE_CODE_PREFIX,
)
from apps.common.exceptions import FacturaEmitidaError
from apps.common.models import CodeModel

from apps.cuenta_cliente.models import CuentaCliente, Sucursal

from .numerador_factura import NumeradorFactura


class Factura(CodeModel):
    """
    Representa una factura emitida a un cliente.

    La factura puede permanecer como borrador hasta ser emitida.
    Una vez emitida, su contenido deja de ser modificable.

    El estado, saldo y pagos se calculan dinámicamente.
    """

    CODE_PREFIX = INVOICE_CODE_PREFIX

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
    # IDENTIFICACIÓN
    # ======================================================

    punto_venta = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Punto de venta"),
    )

    numero = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Número"),
    )

    # ======================================================
    # FECHAS
    # ======================================================

    fecha_emision = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de emisión"),
    )

    fecha_vencimiento = models.DateField(
        db_index=True,
        verbose_name=_("Fecha de vencimiento"),
    )

    fecha_anulacion = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Fecha de anulación"),
    )

    # ======================================================
    # INFORMACIÓN ECONÓMICA
    # ======================================================

    total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Total"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    motivo_anulacion = models.TextField(
        blank=True,
        verbose_name=_("Motivo de anulación"),
    )

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
        ordering = ("-created_at",)

        constraints = [
            models.UniqueConstraint(
                fields=("punto_venta", "numero"),
                name="unique_numero_factura_por_punto",
            )
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return self.numero_formateado

    # ======================================================
    # MÉTODOS DE NEGOCIO
    # ======================================================

    def actualizar_total(self, commit: bool = True):
        """
        Recalcula el total de la factura a partir de sus detalles.
        """

        if self.emitida:
            raise FacturaEmitidaError()

        self.total = (
            self.detalles.aggregate(
                total=Sum("subtotal")
            )["total"]
            or Decimal("0.00")
        )

        if commit:
            self.save(update_fields=["total"])

    def emitir(self, commit: bool = True):
        """
        Emite definitivamente la factura.
        """

        if self.emitida:
            raise FacturaEmitidaError()

        if self.pk is None:
            raise ValueError(
                "La factura debe guardarse antes de emitirse."
            )

        with transaction.atomic():

            self.actualizar_total(commit=False)

            self.numero = NumeradorFactura.obtener_siguiente_numero(
                self.punto_venta
            )

            self.fecha_emision = timezone.now()

            if commit:
                self.save(
                    update_fields=[
                        "numero",
                        "total",
                        "fecha_emision",
                    ]
                )

    def anular(self, motivo: str = "", commit: bool = True):
        """
        Marca la factura como anulada.
        """

        if self.esta_anulada:
            return

        self.fecha_anulacion = timezone.now()
        self.motivo_anulacion = motivo

        if commit:
            self.save(
                update_fields=[
                    "fecha_anulacion",
                    "motivo_anulacion",
                ]
            )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def emitida(self) -> bool:
        return self.fecha_emision is not None

    @property
    def editable(self) -> bool:
        return (
            not self.emitida
            and not self.esta_anulada
        )

    @property
    def numero_formateado(self) -> str:
        if self.numero is None:
            return "BORRADOR"

        return f"{self.punto_venta:04d}-{self.numero:08d}"

    @property
    def total_pagado(self):
        return (
            self.pagos.aggregate(
                total=Sum("importe")
            )["total"]
            or Decimal("0.00")
        )

    @property
    def saldo_pendiente(self):
        return self.total - self.total_pagado

    @property
    def esta_anulada(self) -> bool:
        return self.fecha_anulacion is not None

    @property
    def esta_vencida(self) -> bool:
        return (
            self.emitida
            and not self.esta_anulada
            and self.saldo_pendiente > 0
            and self.fecha_vencimiento < timezone.localdate()
        )

    @property
    def fecha_ultimo_pago(self):
        ultimo = (
            self.pagos
            .order_by("-fecha")
            .first()
        )

        return ultimo.fecha if ultimo else None

    @property
    def estado(self) -> str:

        if self.esta_anulada:
            return "Anulada"

        if not self.emitida:
            return "Borrador"

        if self.saldo_pendiente <= 0:
            return "Pagada"

        if self.total_pagado > 0:
            return "Parcial"

        if self.esta_vencida:
            return "Vencida"

        return "Pendiente"