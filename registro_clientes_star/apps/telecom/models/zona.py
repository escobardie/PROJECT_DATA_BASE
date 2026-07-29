from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    ZONE_TELECOM_CODE_PREFIX,
    MAX_SHORT_NAME_LENGTH,
    MAX_PROVINCE_LENGTH,
    MAX_CITY_LENGTH,
    MAX_PERCENTAGE_DIGITS,
    PERCENTAGE_DECIMAL_PLACES,
)


class ZonaTelecom(CodeModel):
    """
    Zona de trabajo utilizada para calcular el costo de
    mano de obra de telecom según la provincia.

    El factor multiplicador se aplica sobre el subtotal
    de mano de obra de un presupuesto (nunca sobre
    materiales), tomando como referencia la distancia
    entre la ciudad cabecera de la zona y el sitio de
    obra.
    """

    CODE_PREFIX = ZONE_TELECOM_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    region = models.CharField(
        max_length=MAX_SHORT_NAME_LENGTH,
        blank=True,
        verbose_name=_("Región"),
        help_text=_(
            "Agrupación informativa de la zona "
            "(por ejemplo: NOA, SUR, Litoral)."
        ),
    )

    provincia = models.CharField(
        max_length=MAX_PROVINCE_LENGTH,
        unique=True,
        verbose_name=_("Provincia"),
    )

    ciudad_cabecera = models.CharField(
        max_length=MAX_CITY_LENGTH,
        verbose_name=_("Ciudad cabecera"),
        help_text=_(
            "Ciudad de referencia para calcular la "
            "distancia por ruta hasta el sitio de obra."
        ),
    )

    # ======================================================
    # INFORMACIÓN COMERCIAL
    # ======================================================

    factor_multiplicador = models.DecimalField(
        max_digits=MAX_PERCENTAGE_DIGITS,
        decimal_places=PERCENTAGE_DECIMAL_PLACES,
        default=Decimal("1.00"),
        verbose_name=_("Factor multiplicador"),
        help_text=_(
            "Multiplica el subtotal de mano de obra "
            "del presupuesto (1.00 = sin ajuste)."
        ),
    )

    class Meta:
        verbose_name = _("Zona de telecom")
        verbose_name_plural = _("Zonas de telecom")

        ordering = (
            "provincia",
        )

    def __str__(self):
        return f"{self.provincia} ({self.factor_multiplicador}x)"
