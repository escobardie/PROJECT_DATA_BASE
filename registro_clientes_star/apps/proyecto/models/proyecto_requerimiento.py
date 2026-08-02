from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    PROJECT_REQUIREMENT_CODE_PREFIX,
    MAX_DESCRIPTION_LENGTH,
)

from apps.dispositivo.models import ModeloDispositivo

from .proyecto import Proyecto


class ProyectoRequerimiento(CodeModel):
    """
    Representa un requerimiento técnico previsto para un proyecto.

    Define los equipos o recursos necesarios para ejecutar un proyecto.
    No representa equipos instalados ni órdenes de trabajo.

    La ejecución real se obtiene a través de las Órdenes de Trabajo,
    Instalaciones y Dispositivos instalados.
    """

    CODE_PREFIX = PROJECT_REQUIREMENT_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="requerimientos",
        verbose_name=_("Proyecto"),
    )

    dispositivo = models.ForeignKey(
        ModeloDispositivo,
        on_delete=models.PROTECT,
        related_name="requerimientos_proyecto",
        verbose_name=_("Dispositivo"),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
        ],
        verbose_name=_("Cantidad"),
        help_text=_(
            "Cantidad prevista para este proyecto."
        ),
    )

    descripcion = models.CharField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción adicional del requerimiento."
        ),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Requerimiento del proyecto")
        verbose_name_plural = _("Requerimientos del proyecto")

        ordering = (
            "proyecto",
            "dispositivo",
        )

        indexes = [
            models.Index(
                fields=[
                    "proyecto",
                ],
                name="idx_req_proyecto",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proyecto",
                    "dispositivo",
                ],
                name="unique_req_proyecto",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Validaciones de negocio.
        """

        super().clean()

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.cantidad} × "
            f"{self.dispositivo}"
        )