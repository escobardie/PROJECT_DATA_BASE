from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.constants import (
    DEVICE_BRAND_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)

from apps.common.models import CodeModel


class Marca(CodeModel):
    """
    Catálogo de marcas de dispositivos.

    Representa el fabricante o marca comercial de un dispositivo.

    Ejemplos:

    - Hikvision
    - Dahua
    - TP-Link
    - Mikrotik
    - Ubiquiti
    - Intelbras
    - DSC
    """

    CODE_PREFIX = DEVICE_BRAND_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        db_index=True,
        verbose_name=_("Nombre"),
        help_text=_(
            "Nombre de la marca."
        ),
    )
    sitio_web = models.URLField(
        blank=True,
        verbose_name=_("Sitio web"),
        help_text=_(
            "Sitio web de la marca."
        ),
    )

    descripcion = models.TextField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción opcional de la marca."
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
            "Orden utilizado para mostrar la marca."
        ),
    )

    # ======================================================
    # META
    # ======================================================

    class Meta:
        verbose_name = _("Marca")
        verbose_name_plural = _("Marcas")

        ordering = (
            "orden",
            "nombre",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "nombre",
                ],
                name="unique_marca_nombre",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "orden",
                    "nombre",
                ],
                name="idx_marca_orden_nombre",
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return self.nombre