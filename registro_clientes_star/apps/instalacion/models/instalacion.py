from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    INSTALLATION_CODE_PREFIX,
    MAX_NAME_LENGTH,
)
from apps.common.choices import (
    EstadoInstalacionChoices,
    PrioridadInstalacionChoices,
)

from apps.servicio.models import ServicioContratado


class Instalacion(CodeModel):
    """
    Representa un trabajo técnico realizado sobre un servicio contratado.

    Una instalación agrupa los dispositivos instalados, los técnicos
    participantes y toda la información relacionada con el trabajo.

    No almacena información del cliente ni de la sucursal, ya que estos
    datos se obtienen a través del ServicioContratado.
    """

    CODE_PREFIX = INSTALLATION_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    servicio_contratado = models.ForeignKey(
        ServicioContratado,
        on_delete=models.PROTECT,
        related_name="instalaciones",
        verbose_name=_("Servicio contratado"),
    )

    # ======================================================
    # PLANIFICACIÓN
    # ======================================================

    prioridad = models.CharField(
        max_length=20,
        choices=PrioridadInstalacionChoices.choices,
        default=PrioridadInstalacionChoices.NORMAL,
        db_index=True,
        verbose_name=_("Prioridad"),
    )

    fecha_programada = models.DateField(
        verbose_name=_("Fecha programada"),
        db_index=True,
    )

    duracion_estimada = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_("Duración estimada"),
        help_text=_("Tiempo estimado para completar la instalación."),
    )

    # ======================================================
    # EJECUCIÓN
    # ======================================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoInstalacionChoices.choices,
        default=EstadoInstalacionChoices.PENDIENTE,
        db_index=True,
        verbose_name=_("Estado"),
    )

    fecha_inicio = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de inicio"),
    )

    fecha_finalizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de finalización"),
    )

    # ======================================================
    # CONFORMIDAD
    # ======================================================

    recibido_por = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Recibido por"),
    )

    fecha_conformidad = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de conformidad"),
    )

    observaciones_conformidad = models.TextField(
        blank=True,
        verbose_name=_("Observaciones de conformidad"),
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
        verbose_name = _("Instalación")
        verbose_name_plural = _("Instalaciones")
        ordering = (
            "prioridad",
            "fecha_programada",
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=[
                    "estado",
                    "fecha_programada",
                ]
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return f"{self.codigo} - {self.servicio_contratado}"

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def esta_pendiente(self):
        return (
            self.estado
            == EstadoInstalacionChoices.PENDIENTE
        )

    @property
    def esta_programada(self):
        return (
            self.estado
            == EstadoInstalacionChoices.PROGRAMADA
        )

    @property
    def en_proceso(self):
        return (
            self.estado
            == EstadoInstalacionChoices.EN_PROCESO
        )

    @property
    def finalizada(self):
        return (
            self.estado
            == EstadoInstalacionChoices.FINALIZADA
        )

    @property
    def cancelada(self):
        return (
            self.estado
            == EstadoInstalacionChoices.CANCELADA
        )

    @property
    def esta_vencida(self):
        """
        Determina si una instalación programada se encuentra vencida.
        """

        return (
            self.fecha_programada < timezone.localdate()
            and not self.finalizada
            and not self.cancelada
        )