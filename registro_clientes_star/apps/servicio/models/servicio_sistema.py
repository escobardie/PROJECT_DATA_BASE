from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.sistema.models import Sistema

from .servicio import Servicio


class ServicioSistema(BaseModel):
    """
    Relaciona un servicio con uno o varios sistemas.

    Permite definir qué sistemas tecnológicos
    forman parte de un servicio comercial.
    """

    # ======================================================
    # RELACIONES
    # ======================================================

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name="servicio_sistemas",
        verbose_name=_("Servicio"),
    )

    sistema = models.ForeignKey(
        Sistema,
        on_delete=models.PROTECT,
        related_name="servicio_sistemas",
        verbose_name=_("Sistema"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    principal = models.BooleanField(
        default=False,
        verbose_name=_("Sistema principal"),
        help_text=_(
            "Indica si este es el sistema principal del servicio."
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
        verbose_name = _("Sistema del servicio")
        verbose_name_plural = _("Sistemas del servicio")

        ordering = (
            "servicio",
            "-principal",
            "sistema",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "servicio",
                    "sistema",
                ],
                name="unique_servicio_sistema",
            ),
        ]

    def __str__(self):
        return f"{self.servicio} → {self.sistema}"