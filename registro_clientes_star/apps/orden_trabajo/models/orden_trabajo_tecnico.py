from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


from apps.common.models import BaseModel

from apps.usuarios.models import Usuario

from .orden_trabajo import OrdenTrabajo


class OrdenTrabajoTecnico(BaseModel):
    """
    Técnicos asignados a una orden de trabajo.

    Permite asociar uno o varios usuarios
    responsables de ejecutar una OT.
    """

    # ======================================================
    # RELACIONES
    # ======================================================

    orden_trabajo = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="tecnicos",
        verbose_name=_("Orden de trabajo"),
    )

    tecnico = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_asignadas",
        verbose_name=_("Técnico"),
    )

    # ======================================================
    # INFORMACIÓN
    # ======================================================

    es_principal = models.BooleanField(
        default=False,
        verbose_name=_("Técnico principal"),
        help_text=_(
            "Indica si es el técnico principal "
            "de la orden."
        ),
    )

    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _(
            "Técnico asignado"
        )

        verbose_name_plural = _(
            "Técnicos asignados"
        )

        ordering = (
            "-es_principal",
            "tecnico",
        )

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "orden_trabajo",
                    "tecnico",
                ],
                name=(
                    "unique_ot_tecnico"
                ),
            ),

        ]

        indexes = [

            models.Index(
                fields=[
                    "orden_trabajo",
                ],
                name=(
                    "idx_ot_tecnico_ot"
                ),
            ),

            models.Index(
                fields=[
                    "tecnico",
                ],
                name=(
                    "idx_ot_tecnico_usuario"
                ),
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

        if self.es_principal:

            existe_principal = (
                OrdenTrabajoTecnico.objects
                .filter(
                    orden_trabajo=self.orden_trabajo,
                    es_principal=True,
                )
                .exclude(
                    pk=self.pk,
                )
                .exists()
            )

            if existe_principal:
                raise ValidationError(
                    {
                        "es_principal": _(
                            "La orden de trabajo "
                            "ya tiene un técnico principal."
                        )
                    }
                )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        return (
            f"{self.orden_trabajo.codigo} - "
            f"{self.tecnico}"
        )