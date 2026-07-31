from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    MAX_NAME_LENGTH,
)

from apps.common.constants import (
    ORDER_CODE_PREFIX,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_OBSERVATION_LENGTH,
)

from apps.common.choices import (
    TipoOrdenTrabajoChoices,
    EstadoOrdenTrabajoChoices,
    PrioridadOrdenTrabajoChoices,
)

from apps.proyecto.models import Proyecto
from apps.instalacion.models import Instalacion
from apps.usuarios.models import Usuario


class OrdenTrabajo(CodeModel):
    """
    Representa una orden de trabajo operativa.

    Gestiona la ejecución de trabajos técnicos
    relacionados con un proyecto.

    No contiene información económica.
    """

    CODE_PREFIX = ORDER_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        verbose_name=_("Proyecto"),
    )

    instalacion = models.ForeignKey(
        Instalacion,
        on_delete=models.SET_NULL,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Instalación"),
        help_text=_(
            "Instalación relacionada si corresponde."
        ),
    )

    responsable = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_responsables",
        verbose_name=_("Responsable"),
        help_text=_(
            "Usuario responsable de coordinar la orden."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    titulo = models.CharField(
        max_length=MAX_TITLE_LENGTH,
        verbose_name=_("Título"),
    )

    descripcion = models.CharField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Descripción"),
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    tipo = models.CharField(
        max_length=30,
        choices=TipoOrdenTrabajoChoices.choices,
        default=TipoOrdenTrabajoChoices.INSTALACION,
        db_index=True,
        verbose_name=_("Tipo"),
    )

    estado = models.CharField(
        max_length=30,
        choices=EstadoOrdenTrabajoChoices.choices,
        default=EstadoOrdenTrabajoChoices.BORRADOR,
        db_index=True,
        verbose_name=_("Estado"),
    )

    prioridad = models.CharField(
        max_length=20,
        choices=PrioridadOrdenTrabajoChoices.choices,
        default=PrioridadOrdenTrabajoChoices.MEDIA,
        db_index=True,
        verbose_name=_("Prioridad"),
    )

    # ======================================================
    # FECHAS
    # ======================================================

    fecha_programada = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha programada"),
    )

    fecha_inicio = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha inicio"),
    )

    fecha_finalizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha finalización"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        max_length=MAX_OBSERVATION_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Orden de trabajo")
        verbose_name_plural = _("Órdenes de trabajo")

        ordering = (
            "-created_at",
        )

        indexes = [

            models.Index(
                fields=[
                    "estado",
                    "prioridad",
                ],
                name="idx_ot_estado_prioridad",
            ),

            models.Index(
                fields=[
                    "fecha_programada",
                ],
                name="idx_ot_fecha_prog",
            ),

            models.Index(
                fields=[
                    "proyecto",
                ],
                name="idx_ot_proyecto",
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

        if (
            self.fecha_finalizacion
            and self.fecha_inicio
            and self.fecha_finalizacion < self.fecha_inicio
        ):
            raise ValidationError(
                {
                    "fecha_finalizacion": _(
                        "La fecha de finalización "
                        "no puede ser anterior al inicio."
                    )
                }
            )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        return (
            f"{self.codigo} - "
            f"{self.titulo}"
        )