from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    DEVICE_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)

from apps.common.choices import EstadoDispositivoChoices

from apps.servicio.models import ServicioContratado

from .modelo_dispositivo import ModeloDispositivo


class Dispositivo(CodeModel):
    """
    Representa un equipo físico instalado dentro de un servicio contratado.

    Ejemplo:
        Cámara Hikvision DS-2CD2043G0-I
        instalada en una sucursal específica.
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
        help_text=_(
            "Identificador interno utilizado por la empresa."
        ),
    )

    # ======================================================
    # INSTALACIÓN
    # ======================================================

    fecha_instalacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de instalación"),
    )

    ubicacion = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Ubicación"),
        help_text=_(
            "Lugar físico donde está instalado el dispositivo."
        ),
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