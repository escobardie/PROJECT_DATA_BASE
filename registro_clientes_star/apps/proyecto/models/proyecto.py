from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    PROJECT_CODE_PREFIX,
    MAX_NAME_LENGTH,
)

from apps.common.choices import (
    EstadoProyectoChoices,
)

from apps.cuenta_cliente.models import Sucursal


class Proyecto(CodeModel):
    """
    Representa un proyecto desarrollado para una sucursal.

    Un proyecto constituye el marco general bajo el cual se organizan
    una o varias órdenes de trabajo necesarias para alcanzar un objetivo
    determinado.
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

    titulo = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Título"),
    )

    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Descripción"),
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoProyectoChoices.choices,
        default=EstadoProyectoChoices.PLANIFICADO,
        db_index=True,
        verbose_name=_("Estado"),
    )

    # ======================================================
    # PLANIFICACIÓN
    # ======================================================

    fecha_planificada_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha planificada de inicio"),
    )

    fecha_planificada_finalizacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha planificada de finalización"),
    )
    # ======================================================
    # EJECUCIÓN
    # ======================================================

    fecha_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de inicio"),
        help_text=_(
            "Fecha real en la que comenzó la ejecución del proyecto."
        ),
    )

    fecha_finalizacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de finalización"),
        help_text=_(
            "Fecha real en la que finalizó el proyecto."
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
        verbose_name = _("Proyecto")
        verbose_name_plural = _("Proyectos")

        ordering = (
            "-created_at",
        )

        indexes = [

            models.Index(
                fields=[
                    "estado",
                ],
                name="idx_proy_estado",
            ),

            models.Index(
                fields=[
                    "fecha_planificada_inicio",
                ],
                name="idx_proy_fec_ini",
            ),

            models.Index(
                fields=[
                    "fecha_planificada_finalizacion",
                ],
                name="idx_proy_fec_fin",
            ),

        ]
    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Validaciones de negocio del proyecto.
        """

        super().clean()

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.codigo} - "
            f"{self.titulo}"
        )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def planificado(self):
        """
        Indica si el proyecto se encuentra planificado.
        """

        return (
            self.estado
            == EstadoProyectoChoices.PLANIFICADO
        )

    @property
    def en_ejecucion(self):
        """
        Indica si el proyecto se encuentra en ejecución.
        """

        return (
            self.estado
            == EstadoProyectoChoices.EN_EJECUCION
        )

    @property
    def finalizado(self):
        """
        Indica si el proyecto se encuentra finalizado.
        """

        return (
            self.estado
            == EstadoProyectoChoices.FINALIZADO
        )

    @property
    def cancelado(self):
        """
        Indica si el proyecto fue cancelado.
        """

        return (
            self.estado
            == EstadoProyectoChoices.CANCELADO
        )

    @property
    def cantidad_ordenes_trabajo(self):
        """
        Devuelve la cantidad de órdenes de trabajo asociadas al proyecto.
        """

        return self.ordenes_trabajo.count()