from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    PAYMENT_CODE_PREFIX,
)

from .factura import Factura
from apps.common.choices import MedioPagoChoices


class Pago(CodeModel):
    """
    Representa un pago realizado sobre una factura.

    Los pagos son movimientos independientes.
    La factura calcula automáticamente su estado
    en función de estos registros.
    """

    CODE_PREFIX = PAYMENT_CODE_PREFIX
    
    # ======================================================
    # RELACIÓN
    # ======================================================

    factura = models.ForeignKey(
        Factura,
        on_delete=models.PROTECT,
        related_name="pagos",
        verbose_name=_("Factura"),
    )

    # ======================================================
    # INFORMACIÓN DEL PAGO
    # ======================================================

    fecha = models.DateField(
        default=timezone.localdate,
        verbose_name=_("Fecha de pago"),
    )

    importe = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        verbose_name=_("Importe"),
    )

    medio_pago = models.CharField(
        max_length=30,
        choices=MedioPagoChoices.choices,
        verbose_name=_("Medio de pago"),
    )

    numero_comprobante = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Número de comprobante"),
        help_text=_(
            "Referencia externa del pago "
            "(transferencia, operación, cheque, etc.)."
        ),
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
        verbose_name = _("Pago")
        verbose_name_plural = _("Pagos")
        ordering = (
            "-fecha",
        )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.factura.numero_formateado} - "
            f"{self.importe}"
        )