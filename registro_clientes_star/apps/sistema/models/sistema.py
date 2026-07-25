from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    SYSTEM_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)

from .categoria_sistema import CategoriaSistema


class Sistema(CodeModel):
    """
    Representa una solución tecnológica ofrecida por la empresa.

    Ejemplos:
        - CCTV IP Hikvision
        - Alarma DSC PowerSeries
        - Control de acceso biométrico
        - Red LAN empresarial
    """

    CODE_PREFIX = SYSTEM_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    categoria = models.ForeignKey(
        CategoriaSistema,
        on_delete=models.PROTECT,
        related_name="sistemas",
        verbose_name=_("Categoría"),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Nombre"),
    )

    descripcion = models.CharField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        verbose_name=_("Descripción"),
    )

    # ======================================================
    # ESTADO COMERCIAL
    # ======================================================

    disponible = models.BooleanField(
        default=True,
        verbose_name=_("Disponible"),
        help_text=_(
            "Indica si el sistema está disponible para nuevas instalaciones."
        ),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    class Meta:
        verbose_name = _("Sistema")
        verbose_name_plural = _("Sistemas")

        ordering = (
            "categoria__nombre",
            "nombre",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "categoria",
                    "nombre",
                ],
                name="unique_sistema_por_categoria",
            )
        ]

    def __str__(self):
        return f"{self.categoria} - {self.nombre}"