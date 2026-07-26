from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    DEVICE_CODE_PREFIX,
    MAX_NAME_LENGTH,
)

from apps.common.choices import EstadoDispositivoChoices

from apps.servicio.models.servicio_contratado import ServicioContratado

from .modelo_dispositivo import ModeloDispositivo


class Dispositivo(CodeModel):
    """
    Representa un equipo físico instalado dentro
    de un servicio contratado.
    """

    CODE_PREFIX = DEVICE_CODE_PREFIX


    # ======================================================
    # RELACIONES
    # ======================================================

    servicio_contratado = models.ForeignKey(
        ServicioContratado,
        on_delete=models.PROTECT,
        related_name="dispositivos",
        verbose_name=_("Servicio contratado"),
    )

    modelo = models.ForeignKey(
        ModeloDispositivo,
        on_delete=models.PROTECT,
        related_name="dispositivos",
        verbose_name=_("Modelo"),
    )


    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    numero_serie = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        verbose_name=_("Número de serie"),
    )

    codigo_interno = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Código interno"),
    )


    # ======================================================
    # INSTALACIÓN
    # ======================================================

    fecha_instalacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de instalación"),
    )

    fecha_retiro = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de retiro"),
    )

    ubicacion = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Ubicación"),
    )


    # ======================================================
    # ESTADO
    # ======================================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoDispositivoChoices.choices,
        default=EstadoDispositivoChoices.ACTIVO,
        verbose_name=_("Estado"),
    )


    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )


    class Meta:
        verbose_name = _("Dispositivo")
        verbose_name_plural = _("Dispositivos")

        ordering = (
            "modelo",
            "numero_serie",
        )


    def __str__(self):
        return f"{self.modelo} - {self.numero_serie}"