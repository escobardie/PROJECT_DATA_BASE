from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.constants import (
    DEVICE_TYPE_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)
from apps.common.models import CodeModel


class TipoDispositivo(CodeModel):
    """
    Catálogo de tipos de dispositivos.

    Este modelo permite clasificar los dispositivos disponibles
    dentro del sistema.

    Ejemplos:
        - Cámara
        - DVR
        - NVR
        - Sensor
        - Router
        - Switch
        - UPS
        - Servidor
    """

    CODE_PREFIX = DEVICE_TYPE_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        db_index=True,
        verbose_name=_("Nombre"),
        help_text=_("Nombre del tipo de dispositivo."),
    )

    descripcion = models.TextField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción opcional del tipo de dispositivo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    orden = models.PositiveSmallIntegerField(
        default=0,
        db_index=True,
        verbose_name=_("Orden"),
        help_text=_(
            "Orden utilizado para mostrar este registro."
        ),
    )

    # ======================================================
    # META
    # ======================================================

    class Meta:
        verbose_name = _("Tipo de dispositivo")
        verbose_name_plural = _("Tipos de dispositivos")

        ordering = (
            "orden",
            "nombre",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "nombre",
                ],
                name="unique_tipo_disp_nombre",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "orden",
                    "nombre",
                ],
                name="idx_tipo_disp_ord_nom",
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return self.nombre