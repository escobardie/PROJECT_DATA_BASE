from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel

from apps.common.choices import (
    RolTecnicoInstalacionChoices,
)

from apps.usuarios.models import Usuario

from .instalacion import Instalacion


class InstalacionTecnico(BaseModel):
    """
    Representa la asignación de un técnico a una instalación.

    Una instalación puede tener varios técnicos
    participantes, pero solamente uno puede ser
    el responsable principal.
    """

    # ======================================================
    # RELACIONES
    # ======================================================

    instalacion = models.ForeignKey(
        Instalacion,
        on_delete=models.CASCADE,
        related_name="tecnicos",
        verbose_name=_("Instalación"),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="instalaciones_asignadas",
        verbose_name=_("Técnico"),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    rol = models.CharField(
        max_length=20,
        choices=RolTecnicoInstalacionChoices.choices,
        default=RolTecnicoInstalacionChoices.AYUDANTE,
        verbose_name=_("Rol"),
        help_text=_(
            "Rol desempeñado por el técnico durante la instalación."
        ),
    )

    es_responsable = models.BooleanField(
        default=False,
        verbose_name=_("Responsable"),
        help_text=_(
            "Indica si este técnico es el responsable principal "
            "de la instalación."
        ),
    )

    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
        help_text=_(
            "Observaciones relacionadas con la participación "
            "del técnico."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Técnico de instalación")
        verbose_name_plural = _("Técnicos de instalación")

        ordering = (
            "-es_responsable",
            "usuario",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "instalacion",
                    "usuario",
                ],
                name="unique_instalacion_tecnico",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida que exista un único técnico responsable
        por instalación.
        """

        super().clean()

        if not self.instalacion_id:
            return

        if self.es_responsable:

            existe_responsable = (
                InstalacionTecnico.objects
                .filter(
                    instalacion_id=self.instalacion_id,
                    es_responsable=True,
                )
                .exclude(
                    pk=self.pk,
                )
                .exists()
            )

            if existe_responsable:
                raise ValidationError(
                    {
                        "es_responsable": _(
                            "La instalación ya tiene "
                            "un técnico responsable."
                        )
                    }
                )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.instalacion.codigo} - "
            f"{self.usuario}"
        )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def es_ayudante(self):
        return (
            self.rol
            == RolTecnicoInstalacionChoices.AYUDANTE
        )

    @property
    def es_supervisor(self):
        return (
            self.rol
            == RolTecnicoInstalacionChoices.SUPERVISOR
        )

    @property
    def es_principal(self):
        """
        Alias semántico de es_responsable.
        """

        return self.es_responsable