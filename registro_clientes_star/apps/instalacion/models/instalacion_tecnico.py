from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    INSTALLATION_TECHNICIAN_CODE_PREFIX,
)

from apps.common.choices import (
    RolTecnicoInstalacionChoices,
)

from apps.usuarios.models import Usuario

from .instalacion import Instalacion


class InstalacionTecnico(CodeModel):
    """
    Representa la participación de un técnico en una instalación.

    Una instalación puede tener uno o varios técnicos participantes.
    Cada técnico cumple un rol determinado dentro del trabajo realizado.
    """

    CODE_PREFIX = INSTALLATION_TECHNICIAN_CODE_PREFIX

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
    # PARTICIPACIÓN
    # ======================================================

    rol = models.CharField(
        max_length=20,
        choices=RolTecnicoInstalacionChoices.choices,
        default=RolTecnicoInstalacionChoices.AYUDANTE,
        verbose_name=_("Rol"),
    )

    es_responsable = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Responsable"),
        help_text=_(
            "Indica si este técnico es el responsable principal de la instalación."
        ),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
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
                name="unique_tecnico_por_instalacion",
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "es_responsable",
                ]
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.usuario} - "
            f"{self.instalacion.codigo}"
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