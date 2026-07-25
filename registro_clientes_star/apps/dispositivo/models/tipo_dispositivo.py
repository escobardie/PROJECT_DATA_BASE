from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    DEVICE_TYPE_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)


class TipoDispositivo(CodeModel):
    """
    Catálogo de tipos de dispositivos utilizados por la empresa.

    Ejemplos:
        - Cámara
        - DVR
        - NVR
        - Central de alarma
        - Sensor PIR
        - Switch
    """

    CODE_PREFIX = DEVICE_TYPE_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        verbose_name=_("Nombre"),
    )

    descripcion = models.CharField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        verbose_name=_("Descripción"),
    )

    class Meta:
        verbose_name = _("Tipo de dispositivo")
        verbose_name_plural = _("Tipos de dispositivos")
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre

