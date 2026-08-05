from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.usuarios.models import Usuario

from .orden_trabajo import OrdenTrabajo


class OrdenTrabajoTecnico(BaseModel):
    """
    Representa la asignación de un técnico a una orden de trabajo.

    Una orden puede tener varios técnicos asignados,
    pero solamente uno puede marcarse como principal.
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
    # INFORMACIÓN GENERAL
    # ======================================================

    es_principal = models.BooleanField(
        default=False,
        verbose_name=_("Técnico principal"),
        help_text=_(
            "Indica si el técnico es el responsable principal "
            "de ejecutar la orden."
        ),
    )

    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
        help_text=_(
            "Observaciones relacionadas con la participación "
            "del técnico en la orden de trabajo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Técnico asignado")
        verbose_name_plural = _("Técnicos asignados")

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
                name="unique_ot_tecnico",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida que una orden tenga como máximo
        un técnico principal.
        """

        super().clean()

        if not self.orden_trabajo_id or not self.es_principal:
            return

        existe_principal = (
            OrdenTrabajoTecnico.objects
            .filter(
                orden_trabajo_id=self.orden_trabajo_id,
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
                        "La orden de trabajo ya tiene "
                        "un técnico principal."
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