from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    PROJECT_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)

from apps.cuenta_cliente.models.sucursal import Sucursal
from apps.common.choices import EstadoProyectoChoices


class Proyecto(CodeModel):
    """
    Representa un proyecto o trabajo realizado
    para una sucursal.

    Ejemplo:
        Instalación CCTV Planta Norte.
    """

    CODE_PREFIX = PROJECT_CODE_PREFIX


    # ======================================================
    # RELACIONES
    # ======================================================

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="proyectos",
        verbose_name=_("Sucursal"),
    )


    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Nombre"),
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
    )


    # ======================================================
    # ESTADO
    # ======================================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoProyectoChoices.choices,
        default=EstadoProyectoChoices.PLANIFICADO,
        verbose_name=_("Estado"),
    )


    # ======================================================
    # FECHAS
    # ======================================================

    fecha_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de inicio"),
    )

    fecha_finalizacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de finalización"),
    )


    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )


    class Meta:
        verbose_name = _("Proyecto")
        verbose_name_plural = _("Proyectos")

        ordering = (
            "-created_at",
        )


    def __str__(self):
        return (
            f"{self.codigo} - "
            f"{self.nombre} "
            f"({self.sucursal.nombre})"
        )