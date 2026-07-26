from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    DEVICE_BRAND_CODE_PREFIX,
    MAX_NAME_LENGTH,
)


class Marca(CodeModel):
    """
    Catálogo de fabricantes de dispositivos.

    Ejemplos:
        - Hikvision
        - Dahua
        - DSC
        - Ajax
        - MikroTik
    """

    CODE_PREFIX = DEVICE_BRAND_CODE_PREFIX


    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        verbose_name=_("Nombre"),
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
    )


    # ======================================================
    # INFORMACIÓN DEL FABRICANTE
    # ======================================================

    sitio_web = models.URLField(
        blank=True,
        verbose_name=_("Sitio web"),
    )


    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )


    class Meta:
        verbose_name = _("Marca")
        verbose_name_plural = _("Marcas")

        ordering = (
            "nombre",
        )


    def __str__(self):
        return self.nombre