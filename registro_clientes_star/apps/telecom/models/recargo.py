from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    SURCHARGE_TELECOM_CODE_PREFIX,
    MAX_PERCENTAGE_DIGITS,
    PERCENTAGE_DECIMAL_PLACES,
)
from apps.common.choices import TipoRecargoTelecomChoices


class RecargoTelecom(CodeModel):
    """
    Recargo porcentual aplicable a la mano de obra de un
    presupuesto de telecom, según turno, distancia o día
    de la semana.

    Se modela como catálogo editable (en vez de porcentajes
    fijos en el código) para que los valores puedan
    ajustarse desde el admin sin tocar código.
    """

    CODE_PREFIX = SURCHARGE_TELECOM_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    tipo = models.CharField(
        max_length=40,
        choices=TipoRecargoTelecomChoices.choices,
        unique=True,
        verbose_name=_("Tipo de recargo"),
    )

    factor = models.DecimalField(
        max_digits=MAX_PERCENTAGE_DIGITS,
        decimal_places=PERCENTAGE_DECIMAL_PLACES,
        default=Decimal("1.00"),
        verbose_name=_("Factor"),
        help_text=_(
            "Multiplica el subtotal de mano de obra "
            "(1.20 = recargo del 20%)."
        ),
    )

    class Meta:
        verbose_name = _("Recargo de telecom")
        verbose_name_plural = _("Recargos de telecom")

        ordering = (
            "tipo",
        )

    def __str__(self):
        return f"{self.get_tipo_display()} ({self.factor}x)"
