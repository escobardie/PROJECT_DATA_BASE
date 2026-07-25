from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    CONTRACTED_SERVICE_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    MAX_PERCENTAGE_DIGITS,
    PERCENTAGE_DECIMAL_PLACES,
    DEFAULT_AMOUNT,
    DEFAULT_PERCENTAGE,
    MAX_STATUS_LENGTH,
)

from apps.cuenta_cliente.models import Sucursal

from apps.common.choices import EstadoServicioContratadoChoices
from .servicio import Servicio


class ServicioContratado(CodeModel):
    """
    Representa un servicio contratado por una sucursal.

    Es la entidad central del negocio y sobre ella se relacionan
    dispositivos, facturación, pagos, mantenimientos y demás
    operaciones del sistema.
    """

    CODE_PREFIX = CONTRACTED_SERVICE_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="servicios_contratados",
        verbose_name=_("Sucursal"),
        help_text=_("Sucursal donde se presta el servicio."),
    )

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name="servicios_contratados",
        verbose_name=_("Servicio"),
        help_text=_("Servicio contratado por la sucursal."),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre_comercial = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Nombre comercial"),
        help_text=_(
            "Nombre opcional para identificar este servicio dentro de la sucursal."
        ),
    )

    # ======================================================
    # INFORMACIÓN COMERCIAL
    # ======================================================

    precio_abono = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Precio del abono"),
    )

    descuento_porcentaje = models.DecimalField(
        max_digits=MAX_PERCENTAGE_DIGITS,
        decimal_places=PERCENTAGE_DECIMAL_PLACES,
        default=DEFAULT_PERCENTAGE,
        verbose_name=_("Descuento (%)"),
        help_text=_("Porcentaje de descuento aplicado al abono."),
    )

    # ======================================================
    # FECHAS
    # ======================================================

    fecha_alta = models.DateField(
        verbose_name=_("Fecha de alta"),
    )

    fecha_instalacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de instalación"),
    )

    fecha_baja = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de baja"),
    )

    # ======================================================
    # ESTADO
    # ======================================================

    estado = models.CharField(
        max_length=MAX_STATUS_LENGTH,
        choices=EstadoServicioContratadoChoices.choices,
        default=EstadoServicioContratadoChoices.PENDIENTE,
        verbose_name=_("Estado"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    renovacion_automatica = models.BooleanField(
        default=True,
        verbose_name=_("Renovación automática"),
    )

    facturar = models.BooleanField(
        default=True,
        verbose_name=_("Facturar"),
        help_text=_("Indica si este servicio debe incluirse en la facturación."),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    class Meta:
        verbose_name = _("Servicio contratado")
        verbose_name_plural = _("Servicios contratados")

        ordering = (
            "-fecha_alta",
            "nombre_comercial",
        )

    @property
    def importe_final(self):
        """
        Calcula el importe final luego de aplicar
        el descuento porcentual.
        """
        return self.precio_abono * (
            Decimal("1.00")
            - (self.descuento_porcentaje / Decimal("100"))
        )

    def __str__(self):
        if self.nombre_comercial:
            return f"{self.nombre_comercial} ({self.sucursal})"

        return f"{self.servicio} - {self.sucursal}"