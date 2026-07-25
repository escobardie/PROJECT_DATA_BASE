from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    PROJECT_DETAIL_CODE_PREFIX,
    MAX_DESCRIPTION_LENGTH,
)

from apps.dispositivo.models import ModeloDispositivo

from .proyecto import Proyecto


class DetalleProyecto(CodeModel):
    """
    Detalle de equipos y cantidades requeridas dentro de un proyecto.

    Representa la planificación de materiales/equipos,
    no equipos físicos instalados.

    Ejemplo:

        Proyecto:
            Instalación CCTV Planta Norte

        Detalle:
            10 x Cámara Hikvision DS-2CD2043G0-I
            1 x DVR Dahua XVR5108HS
    """

    CODE_PREFIX = PROJECT_DETAIL_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name=_("Proyecto"),
    )

    modelo_dispositivo = models.ForeignKey(
        ModeloDispositivo,
        on_delete=models.PROTECT,
        related_name="detalles_proyecto",
        verbose_name=_("Modelo de dispositivo"),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Cantidad"),
    )

    descripcion = models.CharField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        verbose_name=_("Descripción"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    class Meta:
        verbose_name = _("Detalle de proyecto")
        verbose_name_plural = _("Detalles de proyecto")

        ordering = (
            "proyecto",
            "modelo_dispositivo",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proyecto",
                    "modelo_dispositivo",
                ],
                name="unique_modelo_por_proyecto",
            )
        ]

    def __str__(self):
        return (
            f"{self.proyecto} - "
            f"{self.modelo_dispositivo} "
            f"({self.cantidad})"
        )